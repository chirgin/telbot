from aiogram import types, F, Router
from aiogram.types import Message
from aiogram.filters import Command
import aiohttp
import asyncio
import typing as tp
from config import token_kinopoisk
import sqlite3, datetime


router = Router()


def Insert_to_DB(id_user: str, film_name: str) -> None:
    connection = sqlite3.connect('requests.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Requests (id_user, film, date) VALUES (?, ?, ?)',
                    (id_user, film_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    connection.commit()
    connection.close()


async def async_fetch(session: aiohttp.ClientSession, req: dict[str, tp.Any]) -> tp.Any:
    """
    Asyncronously fetch (get-request) single url using provided session
    :param session: aiohttp session object
    :param url: target http url
    :return: fetched text
    """
    async with session.get(req['url'], headers=req['token']) as resp:
        if resp.status != 200:
            return 'error'
        if req['method'] == 'text':
            text = await resp.text()
        elif req['method'] == 'json':
            text = await resp.json()
        else:
            text = await resp.read()    
        return text


async def async_requests(reqs: list[dict[str, tp.Any]]) -> list[tp.Any]:
    """
    Concurrently fetch provided urls using aiohttp
    :param urls: list of http urls ot fetch
    :return: list of fetched texts
    """
    async with aiohttp.ClientSession() as sess:
        tasks = [async_fetch(sess, req) for req in reqs]
        res = await asyncio.gather(*tasks)
    return res


@router.message(Command("start"))
async def start_handler(msg: Message):
    await msg.answer(f"Привет, {msg.from_user.full_name}! Я телеграм-бот," \
                     "я за соблюдение авторских прав, но мой создатель " \
                        "заставляет меня парсить сайты и сообщать информацию о фильмах.")


@router.message(Command("help"))
async def start_handler(msg: Message):
    await msg.answer(f"Я умею находить информацию о фильмах, для этого " \
                     " просто сообщи мне название фильма без всяких команд.")
    await msg.answer(f"Ещё я храню историю запросов, поэтому ты можешь посмотреть " \
                     "когда и информацию о каких фильмах ты просматривал. " \
                        "Для этого отправь мне команду /history")
    await msg.answer(f"А если хочешь посмотреть количество запросов по каждому фильму, " \
                         "то отправь мне команду /stats")


@router.message(Command("history"))
async def history_handler(msg: Message):
    connection = sqlite3.connect('requests.db')
    cursor = connection.cursor()
    cursor.execute(f'SELECT film, date FROM Requests WHERE id_user=={msg.from_user.id}')
    results = cursor.fetchall()
    await msg.answer(f"История поиска фильмов пользователем {msg.from_user.full_name}")
    res = ''
    for req in results:
        res += f'{req[0]}:   {req[1]}\n'
    await msg.answer(res)
    connection.commit()
    connection.close()


@router.message(Command("stats"))
async def stats_handler(msg: Message):
    connection = sqlite3.connect('requests.db')
    cursor = connection.cursor()
    cursor.execute(f'SELECT film, COUNT(*) FROM Requests WHERE id_user=={msg.from_user.id} GROUP BY film')
    results = cursor.fetchall()
    await msg.answer(f"Статистика поиска фильмов пользователем {msg.from_user.full_name}:")
    res = ''
    for req in results:
        res += f'{req[0]}:   {req[1]}\n'
    await msg.answer(res)
    connection.commit()
    connection.close()


def Reqkinogo(text: str) -> str:
    req = '+'.join(text.split())
    url = 'https://www.google.com/search?q=' + req + \
    '+kinogo.ec' + '+фильм+смотреть' + '+watch' + '+online' + '&ie=utf-8&oe=utf-8'
    return url


def Urlkinogo(req: str) -> str:
    ind = req.find("https://kinogo.ec")
    if ind == -1:
        return "error"
    i = ind    
    while (i+5 < len(req)) and (req[i:i+5] != '.html'):
        i += 1
    if (i - ind > 300) or i+5 == len(req):
        return "error"        
    res = req[ind:i+5]
    return res


def Urlkinogo_media(req: str) -> str:
    ind = req.find("https://kinogo.media")
    if ind == -1:
        return "error"
    i = ind    
    while (i+5 < len(req)) and (req[i:i+5] != '.html'):
        i += 1
    if (i - ind > 300) or i+5 == len(req):
        return "error"        
    res = req[ind:i+5]
    return res


async def googlekinopoisk(text: str) -> tuple[str, str]:
    if text == 'venom' or text == 'Venom':
        text += ' 2018' 
    req = '+'.join(text.split())
    url = 'https://www.google.com/search?q=' + req + \
    '+kinopoisk' + '+ru'+'+описание' + '+фильма' + '+кинопоиск' + '&ie=utf-8&oe=utf-8'
    text = await async_requests([{'url': url, 'token': None, 'method': 'text'}])
    req = text[0]
    ind = req.find("https://www.kinopoisk.ru/")
    if ind == -1:
        return "error1", '0'
    i = ind + 33   
    while (i < len(req)) and (req[i] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
        i += 1
    if i == len(req):
        return "error2", '0'
    j = i - 1
    while (req[j] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):
        j -= 1
    res = req[ind:i+1]
    return res, req[j+1:i]


async def Find_data(urlkinopoisk: str, id_film: str, msg: Message):
    reqkinogo = Reqkinogo(msg.text)
    texts = await async_requests([{'url': reqkinogo, 'token': None, 'method': 'text'},
                                  {'url': 'https://api.kinopoisk.dev/v1.4/movie/'+id_film,
                                    'token': token_kinopoisk, 'method': 'json'}])
 
    kp = texts[1]
    if kp == 'error':
        await msg.answer('Такой фильм ещё не сняли')
    else:
        if (kp.get('name', None) is not None) and kp.get('name', None):
            await msg.answer('<b>' + kp['name'] + '</b>', parse_mode='HTML')    
        if (kp.get('description', None) is not None) and  kp.get('description', None):
            await msg.answer(kp['description'])
        if (kp.get('rating', None) is not None) and  kp.get('rating', None).get('imdb', None) is not None:
            await msg.answer('Рейтинг IMDb: ' + str(kp['rating']['imdb']))
            if kp.get('rating').get('kp', None) is not None:
                await msg.answer('Рейтинг Кинопоиска: ' + str(kp['rating']['kp']))

        if (kp.get('poster') is not None) and kp.get('poster').get('url') is not None:
            await msg.answer_photo(photo=kp['poster']['url'])
        if (kp.get('year') is not None) and kp.get('year'):
            await msg.answer(f"Год выпуска: {kp['year']}")

        urlkinopoisk_tel = '[Смотреть на Кинопоиске](' + urlkinopoisk + ')\n'
        await msg.answer(urlkinopoisk_tel, parse_mode='MarkdownV2', disable_web_page_preview=True)

        urlkinogo = Urlkinogo(texts[0])        
        if urlkinogo == 'error':
            urlkinogo = Urlkinogo_media(texts[0])
            urlkinogo_tel = 'Я против пиратства'
        if urlkinogo != 'error':
            urlkinogo_tel = '[Смотреть бесплатно](' + urlkinogo + ')'                 
        await msg.answer(urlkinogo_tel, parse_mode='MarkdownV2', disable_web_page_preview=True)
        if (kp.get('name', None) is not None) and kp.get('name', None):
            Insert_to_DB(msg.from_user.id, kp.get('name'))


@router.message()
async def message_handler(msg: Message):
    urlkinopoisk, id_film = await googlekinopoisk(msg.text)
    if urlkinopoisk in ['error1', 'error2']:
        await msg.answer('Такой фильм еще не сняли', parse_mode='MarkdownV2', disable_web_page_preview=True)
    else:
        await Find_data(urlkinopoisk, id_film, msg)    
