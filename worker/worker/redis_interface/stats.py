import json
from datetime import datetime

from worker import app, log
from worker.constants import URL
from worker.http_client import http_get
from worker.parser.profile import extract_pseudo
from worker.parser.stats import extract_stats


def get_user_stats_data(username):
    html = http_get(URL + username + '?inc=statistiques')
    if html is None:
        log.warning(f'could_not_get_user_stats', username=username)
        return

    pseudo = extract_pseudo(html)
    solved_challenges = extract_stats(html)

    return {
        'pseudo': pseudo,
        'solved_challenges': solved_challenges,
    }


async def set_user_stats(username):
    response = get_user_stats_data(username)
    await app.redis.set(f'{username}.stats',
                        json.dumps({'body': response, 'last_update': str(datetime.now())}))
    log.debug('set_user_stats_success', username=username)
