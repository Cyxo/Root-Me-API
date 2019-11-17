import asyncio
import sys
from typing import Dict, List

from discord.ext import commands

import bot.display.embed as disp
import bot.manage.json_data as json_data
from bot.colors import red
from bot.constants import token
from bot.manage.discord_data import get_channel
from bot.wraps import update_challenges


class RootMeBot:

    def __init__(self, rootme_challenges: List[Dict[str, str]]):
        """ Discord Bot to catch RootMe events made by zTeeed """
        self.bot = commands.Bot(command_prefix='!')
        self.bot.rootme_challenges = rootme_challenges
        self.channel = None

    async def cron(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            if self.channel is not None:
                await disp.cron(self.channel, self.bot)
            await asyncio.sleep(5)

    def catch(self):
        @self.bot.event
        async def on_ready():
            self.channel = get_channel(self.bot)
            await disp.ready(self.channel, self.bot.command_prefix)

        @self.bot.command(description='Add a user to team into database.')
        async def add_user(context: commands.context.Context):
            """ <username> """
            await disp.add_user(context)

        @self.bot.command(description='Remove a user from team in database.')
        async def remove_user(context: commands.context.Context):
            """ <username> """
            await disp.remove_user(context)

        @self.bot.command(description='Show list of users from team.')
        async def scoreboard(context: commands.context.Context):
            """ """
            await disp.scoreboard(context)

        @self.bot.command(description='Show list of categories.')
        async def categories(context: commands.context.Context):
            """ """
            await disp.categories(context)

        @self.bot.command(description='Show list of challenges from a category.')
        async def category(context: commands.context.Context):
            """ <category> """
            await disp.category(context)

        @self.bot.command(description='Return who solved a specific challenge.')
        async def who_solved(context: commands.context.Context):
            """ <challenge> """
            await disp.who_solved(context)

        @self.bot.command(description='Return challenges solved grouped by users for last week.')
        async def week(context: commands.context.Context):
            """ (<username>) """
            await disp.week(context)

        @self.bot.command(description='Return challenges solved grouped by users for last day.')
        async def today(context: commands.context.Context):
            """ (<username>) """
            await disp.today(context)

        @update_challenges
        @self.bot.command(description='Return difference of solved challenges between two users.')
        async def diff(context: commands.context.Context):
            """ <username1> <username2> """
            await disp.diff(context)

        @update_challenges
        @self.bot.command(description='Return difference of solved challenges between a user and all team.')
        async def diff_with(context: commands.context.Context):
            """ <username> """
            await disp.diff_with(context)

        @self.bot.command(description='Flush all data from bot channel excepted events')
        async def flush(context: commands.context.Context):
            """ """
            await disp.flush(context)

    def start(self):
        if token == 'token':
            red('Please update your token in ./bot/constants.py')
            sys.exit(0)
        self.catch()
        self.bot.loop.create_task(self.cron())
        self.bot.run(token)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()  # event loop
    future = asyncio.ensure_future(json_data.get_categories())  # tasks to do
    rootme_challenges = loop.run_until_complete(future)  # loop until done
    if rootme_challenges is None:
        red('Cannot fetch RootMe challenges from the API.')
        sys.exit(0)
    bot = RootMeBot(rootme_challenges)
    bot.start()
