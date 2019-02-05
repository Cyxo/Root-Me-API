from html import unescape
from datetime import datetime, timedelta
import bot.manage.json_data as jd
from bot.constants import emoji1, emoji2, emoji3, emoji4, emoji5
from bot.display.update import add_emoji


def display_parts(message):
    message = message.split('\n')
    tosend = ''
    stored = []
    for part in message:
        if len(tosend + part + '\n') >= 2000:
            stored.append(tosend)
            tosend = ''
        tosend += part + '\n'
    stored.append(tosend)
    return stored


def display_add_user(bot, name):
    """ Check if user exist in RootMe """
    if not jd.user_rootme_exists(name):
        tosend = 'RootMe profile for {} can\'t be established'.format(name)
        return add_emoji(bot, 'RootMe profile for {} '
              'can\'t be established'.format(name), emoji3)

    """ Add user to data.json """
    if jd.user_json_exists(name):
        return add_emoji(bot, 'User {} already '
              'exists in team'.format(name), emoji5)
    else:
        jd.create_user(name)
        return add_emoji(bot, 'User {} successfully '
               'added in team'.format(name), emoji2)


def display_remove_user(bot, name):
    """ Remove user from data.json """
    if not jd.user_json_exists(name):
        return add_emoji(bot, 'User {} was not in team'.format(name), emoji5)
    else:
        jd.delete_user(name)
        return add_emoji(bot, 'User {} successfully removed '
               'from team'.format(name),  emoji2)


def display_scoreboard(users):
    tosend = ''
    scores = jd.get_scores(users)
    for rank, d in enumerate(scores):
        user, score = d['name'], d['score']
        tosend += '-{}: {} --> Score = {} \n'.format(1+rank, user, score)
    return tosend


def display_categories():
    tosend = ''
    for c in jd.get_categories():
        tosend += '- {} ({} challenges) \n'.format(c['name'], c['challenges_nb'])
    return tosend


def display_category(category):
    c = jd.get_category(category)

    if c is None:
        tosend = 'Category {} does not exists.'.format(category)
        return tosend

    tosend = ''
    for chall in c[0]['challenges']:
        tosend += ('- {} ({} points / {}% of success / difficulty: {}) '
        '\n'.format(unescape(chall['name']), chall['value'],
                    chall['validations_percentage'], 
                    unescape(chall['difficulty'])))
    return tosend


def find_challenge(challenge_selected):
    for category in jd.get_categories():
        challenges = category['challenges']
        for challenge in challenges:
            if challenge['name'] == challenge_selected:
                return challenge
    return None


def user_has_solved(challenge_selected, solved_challenges):
    test = [ c['name'] == challenge_selected for c in solved_challenges ]
    return True in test


def display_who_solved(challenge_selected):
    challenge_found = find_challenge(challenge_selected)

    if challenge_found is None:
        return 'Challenge {} does not exists.'.format(challenge_selected)

    tosend = ''
    users = jd.select_users()
    scores = jd.get_scores(users)
    for d in scores:
        user, score = d['name'], d['score']
        solved_challenges = jd.get_solved_challenges(user)
        if user_has_solved(challenge_selected, solved_challenges):
            tosend += '- {}\n'.format(user)
    if not tosend: 
        tosend = 'Nobody solves {}.'.format(challenge_selected)
    return tosend


def display_duration(args, delay, delay_msg):

    if len(args) == 1:
        if not jd.user_json_exists(args[0]):
            return ('User {} is not in team, you might add it with '
            '`!week (<username>)`'.format(args[0]))
        else:
            users = [args[0]]
    else:
        users = jd.select_users()

    scores = jd.get_scores(users)
    categories = jd.get_categories()
    challs_selected = []
    pattern = '%Y-%m-%d %H:%M:%S'
    tosend = ''

    for d in scores:
        user, score = d['name'], d['score']
        now = datetime.now()

        for chall in jd.get_solved_challenges(user):
            date = datetime.strptime(chall['date'], pattern)
            diff = now - date
            if diff < delay:
                challs_selected.append(chall)

        if challs_selected:
            tosend += 'Challenges solved by {} {}:\n'.format(user, delay_msg)
        for chall in challs_selected:
            value = find_challenge(chall['name'])['value']
            tosend += ('- {} ({} points) - {}\n'.format(chall['name'], 
                        value, chall['date']))
        if challs_selected:
            tosend += '\n\n'

    if len(users) == 1 and not challs_selected:
        tosend = ('No challenges solved by {} {} '
                   ':\'('.format(user, delay_msg))
    elif not tosend:
        tosend = 'No challenges solved by anyone {} :\'('.format(delay_msg)

    return tosend


def display_week(args):
    return display_duration(args, timedelta(weeks=1), 'last week')


def display_today(args):
    return display_duration(args, timedelta(days=1), 'since last 24h')


