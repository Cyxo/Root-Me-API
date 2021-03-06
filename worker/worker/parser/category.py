import re
from html import unescape
from typing import Dict, List, Tuple

from lxml import html


def extract_categories(content: bytes) -> List[str]:
    tree = html.fromstring(content)
    result = tree.xpath(f'//li/a[starts-with(@class, "submenu")][contains(@href, "/Challenges")]/@href')
    return [name.split('/')[2] for name in result]


def _extract_category_logo(tree: html.HtmlElement) -> str:
    result = tree.xpath('//h1/img[@class="vmiddle"][starts-with(@src, "local")]/@src')
    return result[0]


def _extract_category_description(tree: html.HtmlElement) -> Tuple[str, str]:
    result = tree.xpath('//meta[@name="Description"]/@content')
    description1 = result[0]

    result = tree.xpath('string(//div[starts-with(@class, "texte crayon rubrique-texte")]//p)')
    if not result or 'Prérequis' in result:
        description2 = ''
    else:
        description2 = result
    return description1, description2


def _extract_category_prereq(tree: html.HtmlElement) -> List[str]:
    result = tree.xpath('string(//div[starts-with(@class, "texte crayon rubrique-texte")]/p[2]/following-sibling::p)')
    if not result:  # if prerequisites are not on two "p" html tags
        result = tree.xpath('string(//div[starts-with(@class, "texte crayon rubrique-tex")]/p[contains(., "Préreq")])')
    #  RootMe does not list prerequisites with ul/li HTML tags.
    #  I need to make some chemistry to extract the data i want.
    return [prerequisite for prerequisite in result.split('\xa0')[1:] if '\n' not in prerequisite]


def _extract_challenge_url_path(node: html.HtmlElement) -> str:
    path = node.xpath('./td/a[contains(@href, "/Challenges")]/@href')
    return path.pop().strip()


def _extract_challenge_statement(node: html.HtmlElement) -> str:
    statement = node.xpath('./td/a[contains(@href, "/Challenges")]/@title').pop()
    return unescape(statement).strip()


def _extract_challenge_name(node: html.HtmlElement) -> str:
    name = node.xpath('./td/a[contains(@href, "/Challenges")]/text()').pop()
    return unescape(name.strip())


def _extract_challenge_validations_percentage(node: html.HtmlElement) -> str:
    return node.xpath('./td/span[starts-with(@class, "gras left text-left")]/text()').pop()


def _extract_challenge_validations_nb(node: html.HtmlElement) -> int:
    validations = node.xpath('./td/span[@class="right"]/a/text()').pop()
    return int(validations)


def _extract_challenge_difficulty(node: html.HtmlElement) -> str:
    difficulty = node.xpath('./td/a[starts-with(@href,"tag")]/@title')
    if not difficulty:  # difficulty is not registered on some challenges (lang de/es)
        return ''
    difficulty = difficulty.pop()
    return unescape(difficulty.split(':')[0]).strip()


def _extract_challenge_value(node: html.HtmlElement) -> int:
    value = node.xpath('./td[4]/text()').pop()
    return int(value)


def _extract_challenge_author(node: html.HtmlElement) -> List[str]:
    html_elements = node.xpath('./td[@class="show-for-large-up"]/a/@href')
    return [re.match(r'^/(.*)\?lang=..$', link).group(1) for link in html_elements]


def _extract_challenge_note(node: html.HtmlElement) -> int:
    note_img = node.xpath('./td/img[starts-with(@src, "squelettes/img/note")]/@src').pop()
    note = re.match(r'.*note(.*?)\.png', note_img).group(1)
    return int(note)


def _extract_challenge_solutions_nb(node: html.HtmlElement) -> int:
    solution = node.xpath('./td[8]/text()').pop()
    return int(solution)


def _extract_challenges_info(tree: html.HtmlElement) -> List[Dict[str, str]]:
    challenge_nodes = tree.xpath('//*[@id="main"]/div/div[2]/div/div/div/table/tbody/tr')
    result = []
    for node in challenge_nodes:
        result.append({
            'author': _extract_challenge_author(node),
            'difficulty': _extract_challenge_difficulty(node),
            'name': _extract_challenge_name(node),
            'note': _extract_challenge_note(node),
            'path': _extract_challenge_url_path(node),
            'solutions_nb': _extract_challenge_solutions_nb(node),
            'statement': _extract_challenge_statement(node),
            'validations_nb': _extract_challenge_validations_nb(node),
            'validations_percentage': _extract_challenge_validations_percentage(node),
            'value': _extract_challenge_value(node),
        })

    return result


def extract_category_info(content: bytes, category: str) -> List[Dict[str, str]]:
    tree = html.fromstring(content)

    logo = _extract_category_logo(tree)
    desc1, desc2 = _extract_category_description(tree)
    prereq = _extract_category_prereq(tree)
    challenges = _extract_challenges_info(tree)

    return [{
        'name': category.strip(),
        'logo': logo.strip(),
        'description1': desc1.strip(),
        'description2': desc2.strip(),
        'prerequisites': prereq,
        'challenges': challenges,
        'challenges_nb': len(challenges),
    }]
