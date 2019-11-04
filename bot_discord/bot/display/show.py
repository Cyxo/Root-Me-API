from datetime import datetime, timedelta
from html import unescape
from typing import Dict, List, Optional, Tuple, Union

from discord.channel import TextChannel
from discord.ext.commands.bot import Bot
from discord.ext.commands.context import Context

import bot.manage.channel_data as channel_data
from bot.api.fetch import user_rootme_exists, get_scores, get_solved_challenges, get_diff, \
    get_categories, get_category
from bot.api.parser import Parser
from bot.database.manager import DatabaseManager
from bot.colors import blue, green, red
from bot.constants import emoji2, emoji3, emoji5, limit_size, medals
from bot.display.update import add_emoji
from bot.wraps import stop_if_args_none


def display_parts(message: str) -> List[str]:
    message = message.split('\n')
    tosend = ''
    stored = []
    for part in message:
        if len(tosend + part + '\n') >= limit_size:
            stored.append(tosend)
            tosend = ''
        tosend += part + '\n'
    stored.append(tosend)
    return stored


async def display_lang(parser: Parser, bot: Bot, lang: str) -> str:
    if lang not in ['en', 'fr', 'de', 'es']:
        return add_emoji(bot, f'You need to choose fr/en/de/es as <lang> argument', emoji3)
    parser.lang = lang
    return add_emoji(bot, f'LANG successfully updated to "{lang}"', emoji2)


async def display_add_user(parser: Parser, db: DatabaseManager, id_discord_server: int, bot: Bot, name: str) -> str:
    """ Check if user exist in RootMe """
    user_exists = await user_rootme_exists(parser, name)
    if not user_exists:
        return add_emoji(bot, f'RootMe profile for {name} can\'t be established', emoji3)

    """ Add user to database """
    if await db.user_exists(id_discord_server, name):
        return add_emoji(bot, f'User {name} already exists in team', emoji5)
    else:
        stats_user = await parser.extract_rootme_stats(name)
        solved_challenges = stats_user['solved_challenges']
        if not solved_challenges:
            last_challenge_solved = '?????'
        else:
            last_challenge_solved = solved_challenges[-1]['name']
        await db.create_user(id_discord_server, name, last_challenge_solved=last_challenge_solved)
        return add_emoji(bot, f'User {name} successfully added in team', emoji2)


async def display_remove_user(db: DatabaseManager, id_discord_server: int, bot: Bot, name: str) -> str:
    """ Remove user from data.json """
    if not await db.user_exists(id_discord_server, name):
        return add_emoji(bot, f'User {name} is not in team', emoji5)
    else:
        await db.delete_user(id_discord_server, name)
        return add_emoji(bot, f'User {name} successfully removed from team', emoji2)


async def display_scoreboard(parser: Parser, db: DatabaseManager, id_discord_server: int) -> str:
    tosend = ''
    users = await db.select_users(id_discord_server)
    usernames = [user['rootme_username'] for user in users]
    scores = await get_scores(parser, usernames)
    for rank, d in enumerate(scores):
        user, score = d['name'], d['score']
        if rank < len(medals):
            tosend += f'{medals[rank]} {user} --> Score = {score} \n'
        else:
            tosend += f' • • • {user} --> Score = {score} \n'

    return tosend


async def display_categories(parser: Parser) -> str:
    tosend = ''
    categories = await get_categories(parser)
    for category in categories:
        tosend += f' • {category["name"]} ({category["challenges_nb"]} challenges) \n'
    return tosend


async def display_category(parser: Parser, category: str) -> str:
    category_data = await get_category(parser, category)

    if category_data is None:
        tosend = f'Category {category} does not exists.'
        return tosend

    tosend = ''
    for chall in category_data[0]['challenges']:
        tosend += f' • {unescape(chall["name"])} ({chall["value"]} points / {chall["validations_percentage"]} of \
success / difficulty: {unescape(chall["difficulty"])}) \n'
    return tosend


def find_challenge(bot: Bot, challenge_selected: str) -> Optional[Dict[str, Union[str, int, List[str]]]]:
    for category in bot.rootme_challenges:
        challenges = category['challenges']
        for challenge in challenges:
            if challenge['name'] == challenge_selected:
                return challenge
    return None


def user_has_solved(challenge_selected: str, solved_challenges: List[Dict[str, Union[str, int]]]) -> bool:
    test = [c['name'] == challenge_selected for c in solved_challenges]
    return True in test


async def display_who_solved(parser: Parser, db: DatabaseManager, id_discord_server: int, bot: Bot,
                             challenge_selected: str) -> Optional[str]:
    challenge_found = find_challenge(bot, challenge_selected)
    if challenge_found is None:
        return f'Challenge {challenge_selected} does not exists.'

    tosend = ''
    users = await db.select_users(id_discord_server)
    usernames = [user['rootme_username'] for user in users]
    scores = await get_scores(parser, usernames)
    for d in scores:
        user, score = d['name'], d['score']
        solved_challenges = await get_solved_challenges(parser, user)
        if solved_challenges is None:
            return None
        if user_has_solved(challenge_selected, solved_challenges):
            tosend += f' • {user}\n'
    if not tosend:
        tosend = f'Nobody solves {challenge_selected}.'
    return tosend


async def display_duration(parser: Parser, db: DatabaseManager, context: Context, args: Tuple[str], delay: timedelta) \
        -> List[Dict[str, Optional[str]]]:
    if len(args) == 1:
        if not await db.user_exists(context.guild.id, args[0]):
            tosend = f'User {args[0]} is not in team.\nYou might add it with ' \
                f'{context.bot.command_prefix}{context.command} {context.command.help.strip()}'
            tosend_list = [{'user': args[0], 'msg': tosend}]
            return tosend_list
        else:
            users = [args[0]]
    else:
        users = await db.select_users(context.guild.id)
        users = [user['rootme_username'] for user in users]

    scores = await get_scores(parser, users)
    #  categories = json_data.get_categories()
    pattern = '%Y-%m-%d %H:%M:%S'
    tosend_list = []

    for d in scores:
        tosend = ''
        user, score = d['name'], d['score']
        now = datetime.now()
        challs_selected = []

        challenges = await get_solved_challenges(parser, user)
        for chall in challenges:
            date = datetime.strptime(chall['date'], pattern)
            diff = now - date
            if diff < delay:
                challs_selected.append(chall)

        challs_selected.reverse()
        for chall in challs_selected:
            value = find_challenge(context.bot, chall['name'])['value']
            tosend += f' • {chall["name"]} ({value} points) - {chall["date"]}\n'
        tosend_list.append({'user': user, 'msg': tosend})

    test = [item['msg'] == '' for item in tosend_list]
    if len(users) == 1 and False not in test:
        tosend = f'No challenges solved by {user} :frowning:'
        tosend_list = [{'user': None, 'msg': tosend}]
    elif False not in test:
        tosend = 'No challenges solved by anyone :frowning:'
        tosend_list = [{'user': None, 'msg': tosend}]

    return tosend_list


async def display_week(parser: Parser, db: DatabaseManager, context: Context, args: Tuple[str]) \
        -> List[Dict[str, Optional[str]]]:
    return await display_duration(parser, db, context, args, timedelta(weeks=1))


async def display_today(parser: Parser, db: DatabaseManager, context: Context, args: Tuple[str]) \
        -> List[Dict[str, Optional[str]]]:
    return await display_duration(parser, db, context, args, timedelta(days=1))


@stop_if_args_none
def display_diff_one_side(bot: Bot, user_diff: List[Dict[str, Union[str, int]]]) -> str:
    tosend = ''
    for c in user_diff:
        value = find_challenge(bot, c['name'])['value']
        tosend += f' • {c["name"]} ({value} points)\n'
    return tosend


async def display_diff(parser: Parser, db: DatabaseManager, id_discord_server: int, bot: Bot, user1: str, user2: str) \
        -> List[Dict[str, Optional[str]]]:
    if not await db.user_exists(id_discord_server, user1):
        tosend = f'User {user1} is not in team.'
        tosend_list = [{'user': user1, 'msg': tosend}]
        return tosend_list
    if not await db.user_exists(id_discord_server, user2):
        tosend = f'User {user2} is not in team.'
        tosend_list = [{'user': user2, 'msg': tosend}]
        return tosend_list

    solved_user1 = await get_solved_challenges(parser, user1)
    solved_user2 = await get_solved_challenges(parser, user2)

    user1_diff, user2_diff = get_diff(solved_user1, solved_user2)
    tosend_list = []

    tosend = display_diff_one_side(bot, user1_diff)
    tosend_list.append({'user': user1, 'msg': tosend})
    tosend = display_diff_one_side(bot, user2_diff)
    tosend_list.append({'user': user2, 'msg': tosend})

    return tosend_list


async def display_diff_with(parser: Parser, db: DatabaseManager, id_discord_server: int, bot: Bot, selected_user: str):
    if not await db.user_exists(id_discord_server, selected_user):
        tosend = f'User {selected_user} is not in team.'
        tosend_list = [{'user': selected_user, 'msg': tosend}]
        return tosend_list

    tosend_list = []
    users = await db.select_users(id_discord_server)
    users = [user['rootme_username'] for user in users]
    solved_user_select = await get_solved_challenges(parser, selected_user)
    for user in users:
        solved_user = await get_solved_challenges(parser, user)
        user_diff, user_diff_select = get_diff(solved_user, solved_user_select)
        if user_diff:
            tosend = display_diff_one_side(bot, user_diff)
            tosend_list.append({'user': user, 'msg': tosend})
    return tosend_list


async def display_flush(channel: TextChannel, context: Context) -> str:
    result = await channel_data.flush(channel)
    if channel is None or not result:
        return 'An error occurs while trying to flush channel data.'
    return f'Data from channel has been flushed successfully by {context.author}.'


async def display_reset_database(db: DatabaseManager, id_discord_server: int, bot: Bot) -> str:
    """ Reset discord database """
    users = await db.select_users(id_discord_server)
    usernames = [user['rootme_username'] for user in users]
    for name in usernames:
        await db.delete_user(id_discord_server, name)
    return add_emoji(bot, f'Database has been successfully reset', emoji2)


def next_challenge_solved(solved_user: List[Dict[str, Union[str, int]]], challenge_name: str) \
        -> Optional[Dict[str, Union[str, int]]]:
    if len(solved_user) == 1:
        return solved_user[-1]
    for key, chall in enumerate(solved_user[:-1]):
        if chall['name'] == challenge_name:
            return solved_user[1 + key]
    return None


async def display_cron(id_discord_server: int, parser: Parser, db: DatabaseManager, bot: Bot) \
        -> Tuple[Optional[str], Optional[str]]:
    users = await db.select_users(id_discord_server)
    for user in users:
        last = user['last_challenge_solve']
        solved_user = await get_solved_challenges(parser, user['rootme_username'])
        if not solved_user or solved_user[-1]['name'] == last:
            continue
        blue(solved_user[-1]['name'] + "  |  " + last + "\n")
        next_chall = next_challenge_solved(solved_user, last)
        if next_chall is None:
            red(f'Error with {user} user --> last chall: {last}\n')
            continue
        name = f'New challenge solved by {user}'
        c = find_challenge(bot, next_chall['name'])
        green(f'{user} --> {c["name"]}')
        tosend = f' • {c["name"]} ({c["value"]} points)'
        tosend += f'\n • Difficulty: {c["difficulty"]}'
        tosend += f'\n • Date: {next_chall["date"]}'
        tosend += f'\n • New score: {next_chall["score_at_date"]}'
        await db.update_user_last_challenge(id_discord_server, user['rootme_username'], c['name'])
        return name, tosend
    return None, None
