import asyncio

from tornado.options import define, options

from api.app import Application

if __name__ == '__main__':
    define('port', default=3000, help='port to listen on')
    application = Application()
    application.listen(options.port)

    loop = asyncio.get_event_loop()
    application.init_with_loop(loop)
    loop.run_forever()
