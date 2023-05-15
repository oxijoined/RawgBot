import datetime
from typing import List

from rawg.game import Game
from rawg.genre import Genre
from rawg.developer import Developer
from rawg.store import Store
from rawg.store_brief import StoreBrief
from telebot import types
import re
from dotenv import load_dotenv
import requests
import json
import os

load_dotenv()


RAWG_GAME_URL = 'https://rawg.io/games/'
RAWG_DEVELOPERS_URL = 'https://rawg.io/developers/'
ELLIPSIS_FORMAT = '{}...'
ARBITRARY_PRETTY_LENGTH_LIMIT = 550
html_cleanup = re.compile('<.*?>')


def translate_text(text, target_language="RU"):
    url = "https://api-free.deepl.com/v2/translate"
    data = {
        "auth_key": os.getenv("DEEPL_KEY"),  # Замените на ваш ключ API DeepL
        "text": text,
        "target_lang": target_language,
    }
    response = requests.post(url, data=data)
    return response.json()['translations'][0]['text']


def format_developer(developer: Developer) -> str:
    return f'<a href="{RAWG_DEVELOPERS_URL}{developer.slug}">{developer.name}</a>'


def format_developers(developers: List[Developer]) -> str:
    if not developers:
        return ''
    joined = ', '.join([format_developer(developer) for developer in developers])
    return f'{joined}\n'


def format_released(released: datetime.date, tba: bool) -> str:
    return f"<i>{'TBA' if tba or not released else released}</i>\n"


def format_alternative_names(alternative_names: List[str]) -> str:
    return f"({' / '.join(alternative_names)})\n" if alternative_names else ''


def format_genres(genres: List[Genre]) -> str:
    if not genres:
        return '\n\n'
    joined = ', '.join([genre.name for genre in genres])
    return f'{joined}\n\n'


def format_description(description: str) -> str:
    if not description:
        return ''

    description = re.sub(html_cleanup, ' ', description)
    first_paragraph = description.find('\n')
    if first_paragraph == -1 and description != '' and len(description) > ARBITRARY_PRETTY_LENGTH_LIMIT:
        description = ELLIPSIS_FORMAT.format(description[:ARBITRARY_PRETTY_LENGTH_LIMIT])
    else:
        description = description[:first_paragraph]
    description = description.replace('<3', '❤️')\
        .replace('<', '')\
        .replace('>', '')
    return description


def format_text(game: Game) -> str:
    text = f'<a href="{RAWG_GAME_URL}{game.slug}"><b>{game.name}</b></a>\n'
    text += format_alternative_names(game.alternative_names)
    text += format_released(game.released, game.tba)
    text += format_developers(game.developers)
    text += format_genres(game.genres)
    text += format_description(translate_text(game.description_raw))

    if len(text) > 4096: # Maximum allowed length of a telegram message is 4096 characters
        text = ELLIPSIS_FORMAT.format(text[:4092]) # subtracting 4 to account for the length of ellipsis

    return text


def format_links(brief_stores: List[StoreBrief], stores: List[Store]) -> types.InlineKeyboardMarkup:
    store_buttons = []

    store_names = {
        brief_store.id: brief_store.name for brief_store in brief_stores
    }
    for index, store in enumerate(stores):
        button = types.InlineKeyboardButton(text=store_names[store.store_id], url=store.url.replace('http://', 'https://'))
        if index % 2 == 0:
            store_buttons.append([button])
        else:
            store_buttons[-1].append(button)

    return types.InlineKeyboardMarkup(store_buttons)
