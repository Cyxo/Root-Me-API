import json
from multiprocessing.pool import ThreadPool
from datetime import datetime

from worker import app, log
from worker.constants import URL
from worker.http_client import http_get
from worker.parser.category import extract_categories, extract_category_info


def retrieve_category_info(category):
    html = http_get(f'{URL}fr/Challenges/{category}/')
    if html is None:
        log.warn('category_not_found', category=category)
        return None

    log.msg(f"Fetched category page '{category}'")
    return extract_category_info(html, category)


async def set_all_challenges():
    html = http_get(URL + 'fr/Challenges/')
    if html is None:
        log.error('challenges_page_not_found')
        return

    categories = extract_categories(html)
    log.debug('fetched_categories', categories=categories)

    with ThreadPool(len(categories)) as tp:
        response = tp.map(retrieve_category_info, categories)

    timestamp = json.dumps({'timestamp': str(datetime.now())})

    await app.redis.set('challenges', json.dumps(response))
    await app.redis.set('challenges.timestamp', timestamp)
    await app.redis.set('categories', json.dumps(categories))
    await app.redis.set('categories.timestamp', timestamp)
    for category_data in response:
        await app.redis.set(f'categories.{category_data[0]["name"]}', json.dumps(category_data))
        await app.redis.set(f'categories.{category_data[0]["name"]}.timestamp', timestamp)

    log.debug('set_all_challenges_success')
