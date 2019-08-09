from abc import ABC
import json

from tornado.web import RequestHandler

from api.constants import VERSION, AUTHORS, GITHUB_ACCOUNTS
from api.routes import routes


class RedirectHandler(RequestHandler, ABC):
    """Only allow GET requests."""
    SUPPORTED_METHODS = ["GET"]

    def initialize(self, url):
        self.url = url

    def get(self):
        self.set_status(302)
        self.redirect(self.url)


class InfoHandler(RequestHandler, ABC):
    """Only allow GET requests."""
    SUPPORTED_METHODS = ["GET"]

    def set_default_headers(self):
        """Set the default response header to be JSON."""
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    def get(self):
        """List of routes for this API."""
        self.set_status(200)
        #  routes imported from api.routes
        info = dict(title="Root-Me-API", authors=AUTHORS, follow_us=GITHUB_ACCOUNTS, routes=routes)
        self.write(json.dumps(info))


class RootMeStaticHandler(RequestHandler, ABC):
    """Only allow GET requests."""
    SUPPORTED_METHODS = ["GET"]

    def initialize(self, key):
        self.key = key

    def set_default_headers(self):
        """Set the default response header to be JSON."""
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    async def get(self):
        """Construct and send a JSON response with appropriate status code."""
        self.set_status(200)
        data = await self.application.redis.get(self.key)
        self.write(data)


class RootMeDynamicHandler(RequestHandler, ABC):
    """Only allow GET requests."""
    SUPPORTED_METHODS = ["GET"]

    def initialize(self, key):
        if 'categories' in key:
            self.key = key + '.{}'
        else:  # url_argument is an username
            self.key = '{}.' + key

    def set_default_headers(self):
        """Set the default response header to be JSON."""
        self.set_header("Content-Type", 'application/json; charset="utf-8"')

    async def get(self, url_argument):
        """Construct and send a JSON response with appropriate status code."""
        self.key = self.key.format(url_argument)
        data = await self.application.redis.get(self.key)
        if data is None:
            self.set_status(404)  # raise raise tornado.web.HTTPError ?
        else:
            self.set_status(200)
            self.write(data)


handlers = [
    ('/', RedirectHandler, {'url': f'/{VERSION}'}),
    (f'/{VERSION}', InfoHandler),
    (f'/{VERSION}/categories', RootMeStaticHandler, {'key': 'categories'}),
    (f'/{VERSION}/category/(.*)', RootMeDynamicHandler, {'key': 'categories'}),
    (f'/{VERSION}/challenges', RootMeStaticHandler, {'key': 'challenges'}),
    (f'/{VERSION}/(.*)/profile', RootMeDynamicHandler, {'key': 'profile'}),
    (f'/{VERSION}/(.*)/contributions', RootMeDynamicHandler, {'key': 'contributions'}),
    (f'/{VERSION}/(.*)/contributions/challenges', RootMeDynamicHandler, {'key': 'contributions.challenges'}),
    (f'/{VERSION}/(.*)/contributions/solutions', RootMeDynamicHandler, {'key': 'contributions.solutions'}),
    (f'/{VERSION}/(.*)/details', RootMeDynamicHandler, {'key': 'details'}),
    (f'/{VERSION}/(.*)/ctf', RootMeDynamicHandler, {'key': 'ctfs'}),
    (f'/{VERSION}/(.*)/stats', RootMeDynamicHandler, {'key': 'stats'})
]
