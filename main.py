import telebot
from telebot import types
import os
import requests

import formatters
from rawg.games import Games
from rawg.stores import Stores
from dotenv import load_dotenv
from rawg.game import Game

load_dotenv()

TOKEN = os.getenv("RAWG_BOT_TOKEN")
RAWG_API_KEY = os.getenv("RAWG_API_KEY")
RAWG_API_BASE_URL = "https://api.rawg.io/api"
RAWG_API_GAMES_URL = f"{RAWG_API_BASE_URL}/games"
RAWG_API_GAME_URL = RAWG_API_GAMES_URL + "/{}"
RAWG_API_STORES_URL = RAWG_API_GAMES_URL + "/{}/stores"

bot = telebot.TeleBot(TOKEN,parse_mode='HTML')

key_param = {
    "key": RAWG_API_KEY,
}



@bot.message_handler(commands=["start"])
def send_welcome(message):
    me = bot.get_me().username
    text = f'Это inline бот, попробуйте поискать с "@{me} Portal 2", или что-то в этом роде'
    bot.reply_to(message, text)


@bot.inline_handler(lambda query: len(query.query) > 0)
def query_text(inline_query):
    params = {
        "search": inline_query.query,
        "key": RAWG_API_KEY,
        "page_size": 5,
    }
    games = Games.from_dict(requests.get(RAWG_API_GAMES_URL, params=params).json())
    results = []
    for result in games.results:
        game = Game.from_dict(
            requests.get(RAWG_API_GAME_URL.format(result.id), params=key_param).json()
        )
        text = formatters.format_text(game)
        buttons = None
        if result.stores:
            stores_response = Stores.from_dict(
                requests.get(
                    RAWG_API_STORES_URL.format(result.id), params=key_param
                ).json()
            )
            if stores_response.results:
                buttons = formatters.format_links(
                    [store.store for store in result.stores],
                    [
                        store
                        for store in stores_response.results
                        if store.url is not None and store.url != ""
                    ],
                )

        r = types.InlineQueryResultArticle(
            id=result.id,
            title=game.name,
            description=game.released or "TBA",
            input_message_content=types.InputTextMessageContent(message_text=text, parse_mode='HTML'),
            reply_markup=buttons,
            thumbnail_url=result.background_image,
        )

        results.append(r)

    bot.answer_inline_query(inline_query.id, results)


bot.infinity_polling()