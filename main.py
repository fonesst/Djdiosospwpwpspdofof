# Начало библиотекk
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
import os
import time
import random
import logging
import zipfile
import io
from datetime import datetime
from urllib.parse import urljoin, urlparse
from search import perform_ahmia_search, perform_aol_search, perform_google_search, perform_bing_search
from mask_link import masklink
from ip import parse_geolocation_data, format_data
from parse import parse_site
from gemini import perform_gemini_with_aol_search
from git_hub_fz import create_github_repo, upload_files_to_repo, enable_github_pages
from phoneFO import phone_lookup  # Импортируем функцию из файла phoneFO.py
from open_site import handle_open_site, create_markup, user_texts, user_titles, user_urls  # Импорт функции из open_site.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from kadastr import parse_opendatabot_page, close_driver
from selenium.webdriver.common.by import By
import base64
import json
# Конец библиотек


# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Конец настройки логирования

# Константы, переменные конфигурации
API_KEY = '7368730334:AAH9xUG8G_Ro8mvV_fDQxd5ddkwjxHnBoeg'
ADMIN_CHAT_ID = '1653222949'
GEMINI_API_KEY = 'AIzaSyCzgAreGdXqUXZd5-P_iLUg-3hM9U4Md70'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
CHANNEL_ID = '@fronest_news'
GITHUB_TOKEN = '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'
REPO = 'fonesst/usersFRONEST'  # Укажите репозиторий в формате 'пользователь/репозиторий'
# Конец констант и переменных конфигураций

bot = telebot.TeleBot(API_KEY)

# Глобальная переменная для хранения запроса пользователя
user_query = {}

# Функция для выполнения Google Dork поиска
def perform_google_search(query, filetype, start=0, max_results=100):
    all_results = []
    while len(all_results) < max_results:
        search_query = f"{query} filetype:{filetype}"
        url = f"https://www.google.com/search?q={urllib.parse.quote(search_query)}&start={start}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        results = soup.find_all('div', class_='g')
        if not results:
            break

        for result in results:
            link = result.find('a', href=True)
            if link:
                url = link['href']
                domain = urllib.parse.urlparse(url).netloc
                all_results.append((domain, url))
                if len(all_results) >= max_results:
                    break

        start += 10
        time.sleep(1)

    return all_results

# Команда /dorks
@bot.message_handler(commands=['dorks'])
def handle_dorks_command(message):
    bot.send_message(message.chat.id, "Введите текст для поиска Google Dorks:")
    bot.register_next_step_handler(message, get_user_query)

def get_user_query(message):
    user_query[message.chat.id] = message.text
    bot.send_message(message.chat.id, "Ищу файлы по вашему запросу. Это может занять некоторое время...")

    base_dir = 'search_results'
    if os.path.exists(base_dir):
        for root, dirs, files in os.walk(base_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    os.makedirs(base_dir, exist_ok=True)

    file_categories = {
    "Текстовые файлы": ['txt', 'md', 'log', 'csv', 'xml', 'json', 'yaml', 'yml', 'ini', 'rtf', 'doc', 'docx', 'pdf'],
    "Табличные файлы": ['xls', 'xlsx', 'ods', 'csv', 'tsv'],
    "Базы данных": ['db', 'sqlite', 'sqlite3', 'sql', 'mdb', 'accdb'],
    "Изображения": ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg'],
    "Аудио файлы": ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'],
    "Видео файлы": ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv'],
    "Архивы и сжатие": ['zip', 'rar', '7z', 'tar', 'gz'],
    "Файлы кодирования и сценариев": ['py', 'js', 'html', 'css', 'php', 'cpp', 'java'],
    "Документы": ['pdf', 'doc', 'docx', 'odt', 'rtf'],
    "Системные файлы": ['exe', 'dll', 'sys', 'bat', 'ini'],
    "3D Моделирование и графика": ['obj', 'fbx', 'stl', 'blend'],
    "Виртуальные машины и контейнеры": ['vdi', 'vmdk', 'dockerfile'],
    "Другие специализированные файлы": ['torrent', 'ics', 'apk', 'ipa']
    }
    
    for category, extensions in file_categories.items():
        bot.send_message(message.chat.id, f"Поиск в категории '{category}'...")
        for filetype in extensions:
            search_results = perform_google_search(user_query[message.chat.id], filetype)
            if search_results:
                save_results_to_file(search_results, category, filetype, base_dir)
                bot.send_message(message.chat.id, f"Найдено {len(search_results)} результатов для типа {filetype}")
    
    zip_path = 'all_results.zip'
    create_zip_structure(base_dir, zip_path)
    
    with open(zip_path, 'rb') as zip_file:
        bot.send_document(message.chat.id, zip_file)
    
    os.remove(zip_path)
    bot.send_message(message.chat.id, "Поиск завершен. Результаты отправлены в виде ZIP-архива.")

# Функция сохранения результатов в файл
def save_results_to_file(results, category, filetype, base_dir):
    category_dir = os.path.join(base_dir, category, filetype.upper())
    os.makedirs(category_dir, exist_ok=True)
    
    for domain, url in results:
        file_path = os.path.join(category_dir, f'{domain}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(url)

# Функция создания ZIP-архива с результатами
def create_zip_structure(base_dir, zip_name='all_results.zip'):
    with zipfile.ZipFile(zip_name, 'w') as zipf:
        for folder, subfolders, files in os.walk(base_dir):
            for file in files:
                file_path = os.path.join(folder, file)
                archive_path = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, archive_path)
# Конец команды /dorks
        

# Функция OSINT Сервисов /osint
@bot.message_handler(commands=['osint'])
def handle_osint(message):
    osint_info = """
Привет, Искатель Знаний!

Ты вступил на тропу OSINT — искусства сбора данных из открытых источников. Это не просто инструменты, это твои ключи к миру информации. За каждым запросом скрываются секреты.

Ты вступаешь на путь хакинга и разведки. Но помни — ответственность и закон всегда идут рядом. Используй своё знание с умом.

Твоя разведка начинается здесь 𖤍
"""
    keyboard = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text="NETSTALKING", callback_data="netstalking"),
        InlineKeyboardButton(text=".ONION", callback_data="onion"),
        InlineKeyboardButton(text="БОТЫ ТЕЛЕГРАММ", callback_data="telegram_bots"),
        InlineKeyboardButton(text="АНОНИМНОСТЬ", callback_data="anonymity"),
        InlineKeyboardButton(text="ВК", callback_data="vk"),
        InlineKeyboardButton(text="Ник", callback_data="nickname"),
        InlineKeyboardButton(text="Поиск по ТГ", callback_data="searchtg"),
        InlineKeyboardButton(text="Пробив по АВТО", callback_data="car"),
        InlineKeyboardButton(text="Intelligence X", callback_data="intelligence_x"),
        InlineKeyboardButton(text="Исследования сайтов", callback_data="webwhois"),
        InlineKeyboardButton(text="Термины", callback_data="terms"),
        InlineKeyboardButton(text="Пробив по фото", callback_data="photo"),
        InlineKeyboardButton(text="ЭТАПЫ OSINT", callback_data="osintetaps"),
        InlineKeyboardButton(text="VPN", callback_data="vpns"),
        InlineKeyboardButton(text="Ошибки хакеров", callback_data="hackermistakes"),
        InlineKeyboardButton(text="Google Dork", callback_data="googledork"),
        InlineKeyboardButton(text="ВСЁ О VPN", callback_data="vpntoproxy"),
        InlineKeyboardButton(text="СЕРВИСЫ", callback_data="services"),
    ]
    keyboard.add(*buttons)

    bot.send_message(message.chat.id, osint_info, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data in ['netstalking', 'onion', 'telegram_bots', 'anonymity', 'vk', 'nickname', 'searchtg', 'car', 'intelligence_x', 'webwhois', 'terms', 'photo', 'osintetaps', 'vpns', 'hackermistakes', 'googledork', 'vpntoproxy', 'services'])
def handle_osint_topics(call):
    bot.answer_callback_query(call.id)

    topics = {
        'netstalking': {
            'text': """
Если просто, то нетсталкинг — это поиск секретов интернета.
Нетсталкинг опирается на теорию о трех уровней интернета, согласно которому существует всем известный открытый интернет, так называемая видимая сеть, в которой информация доступа для всех желающих и достижима с помощью обычного сетевого поиска. Второй уровень, глубокая сеть, с ресурсами, которые недоступны через обычный поиск — находится в особом поле зрении искателей секретов, так как этот сегмент сети имеет большое количество контента. Третий уровень это уже даркнет со всеми вытекающими ухищрениями для пользования — нет привычных всем адресов http формата, обязательно нужно приложение для входа (например, TOR браузер).
""",
            'prev': 'osint_services',
            'next': 'onion'
        },
        'onion': {
            'text': """
Onion сеть - что это? И с чем его едят?

Относитесь к onion сети, как к обычной, там есть все тоже самое: форумы, видеохостинги, чаты и так далее. Работа с ними так же не особо отличается, вместо обычного браузера вы используете Tor, вместо google - torch, duckduckgo onion, и другие луковые поисковики.

Топ поисковых систем в onion сети (даркнете):

Duckduckgo:
https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/

Torch:
https://torchqsxkllrj2eqaitp5xvcgfeg3g5dr3hr2wnuvnj76bbxkxfiwxqd.onion/

Kraken:
https://krakenai2gmgwwqyo7bcklv2lzcvhe7cxzzva2xpygyax5f33oqnxpad.onion/

Sentor:
https://e27slbec2ykiyo26gfuovaehuzsydffbit5nlxid53kigw3pvz6uosqd.onion/

GDrak:
https://zb2jtkhnbvhkya3d46twv3g7lkobi4s62tjffqmafjibixk6pmq75did.onion/

Ahmia:
https://ahmia.fi
https://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/

Ourrealm:
http://orealmvxooetglfeguv2vp65a3rig2baq2ljc7jxxs4hsqsrcemkxcad.onion/

Excavator:
https://2fd6cemt4gmccflhm6imvdfvli3nf7zn6rfrwpsy7uhxrgbypvwf5fad.onion/

Для лучшего результата используйте не один, а сразу несколько поисковиков.
""",
            'prev': 'netstalking',
            'next': 'telegram_bots'
        },
        'telegram_bots': {
            'text': """
Подборка ботов которые специализируются на пробиве в Телеграме:
https://telegra.ph/BOTY-TELEGRAMM-09-13
""",
            'prev': 'onion',
            'next': 'anonymity'
        },
        'anonymity': {
            'text': """
• Сперва, почему вообще вам нужно быть анонимными? Наверняка будут люди, которые скажут: "Мне нечего скрывать", отвечаю на это.

• Может быть вам нечего скрывать, но у вас есть все, что нужно защитить. Смысл анонимности не в том, чтобы скрываться от кого-то, а в том, чтобы защитить себя и свою личную жизнь. 

• А так же, нужно различать:

• Конфиденциальность - люди знают, кто вы, но не знают, что вы делаете. 

• Анонимность - люди знают, что вы делаете, но не знают, кто вы.



### Шаг 1: Туннель к свободе
Первое, что должен сделать любой уважающий себя хакер или человек, стремящийся к анонимности, — это спрятать свой IP. Для этого существуют VPN и прокси-сервера. Но будь осторожен: не каждый VPN одинаково полезен. Если он хранит логи, ты всё равно остаешься уязвим. Поэтому ищи VPN с политикой no-logs, который не оставляет следов. Другой важный шаг — использование сети Tor. Это как туннель внутри туннеля, где каждый узел зашифрован, а путь к тебе усложнен.

### Шаг 2: Отключи трекеры
Следующее — это блокировка трекеров и куки. Большинство сайтов собирают огромное количество данных о твоем поведении в интернете, что потом можно легко использовать против тебя. Установи такие расширения, как uBlock Origin или Privacy Badger, чтобы заблокировать все эти невидимые скрипты, которые следят за каждым твоим движением.

### Шаг 3: Меняй идентификацию
Всегда используй ложные учетные записи, виртуальные почтовые ящики и, конечно, одноразовые номера телефонов. Каждый новый аккаунт — это новая личность. Пусть тебя никто не сможет связать с твоими настоящими данными.

### Шаг 4: Убери все лишнее
Хочешь минимизировать следы в сети? Очищай метаданные из файлов, которые загружаешь. Метаданные могут содержать информацию о том, где и когда был создан файл, с какого устройства и т.д. Эти данные могут выдать больше, чем ты думаешь. Для удаления метаданных можно использовать специальные утилиты вроде ExifTool.

### Полезные ресурсы
Теперь о том, что может действительно прокачать твою анонимность. Есть один **интересный сайт**, который станет твоим лучшим другом на этом пути — https://privacytools.io/
На нём собраны инструменты для анонимизации и анонимные аналоги обычных приложений, которые не сливают данные корпорациям. Там же можно найти полезные гайды и приложения для повышения уровня конфиденциальности. Если тебе не безразлична твоя анонимность — настоятельно рекомендую заглянуть.
""",
            'prev': 'telegram_bots',
            'next': 'vk'
        },
        'vk': {
            'text': """
Инструмент для анализа странички ВК - 220VK.
https://new.220vk.com/

Посмотреть исходящие лайки и комментарии можно бесплатно. Так же есть онлайн трекер, но без подписки есть определенные лимиты.
 Бесплатная подписка предоставляет:

- Онлайн трекер
- Поиск скрытых друзей (Работает не на 100%)
- Кому цель ставит лайки
- Кому цель оставляет комментарии
И другие аналитические инструменты


Рассмотрим интересное приложение в ВК, для анализа странички снова - infoapp.
https://m.vk.com/app7183114

Этот инструмент не может искать скрытых друзей или кого комментирует цель, но умеет кое что другое, а именно:

- Нахождение сообществ, в которых цель указана в контактах(возможно группы созданы целью)
- Какими приложениями в ВК пользуется цель
- Нахождение видеозаписей, которые отправлял пользователь
- Друзья друзей
- Какие стикеры есть у цели

Приложение интересное и в умелых руках может помочь в анализе личности и составлении психологического портрета.

Ко всему прочему есть бот в телегарме, который ищет информацию о истории профиля: @VKHistoryRobot
""",
            'prev': 'anonymity',
            'next': 'nickname'
        },
        'nickname': {
            'text': """
Было ли у вас такое, что вы захотели узнать о человеке с интересным никнеймом, но не знали как? Для начала это должен быть уникальный ник, условный "Arthas", а не "pro100gamer228". 

Боты 🤖

@osint_maigret_bot - бот основан на форке скрипта sherlock (о котором будет речь дальше)
@mailcat_s_bot - выдает возможные почты по нику
@boxusers1_bot - универсальный бот, так же имеет поиск по слитым базам по нику

Сайты 🖥

search.0t.rocks - универсальный сайт, так же ищет по слитым базам
whatsmyname.app - сайт ищет где зарегистрирован пользователь 

Скрипты(GitHub) 📝

Snoop - платный, но один из самых перспективных OSINT-инструментов по поиску никнеймов, полная версия ищет по 4000 сайтам [https://github.com/snooppr/snoop]

Sherlock - один из самых известных инструментов по поиску информации по нику [https://github.com/sherlock-project/sherlock]

Enola - усовершенствованная версия Sherlock написанная на golang [https://github.com/TheYahya/enola]
""",
            'prev': 'vk',
            'next': 'searchtg'
        },
        'searchtg': {
            'text': """
Подобрал для вас несколько поисковик по телеграму, это не все и если вам будет интересна эта тема, будет еще один пост.

• Телеграм бот @MotherSearchBot - поможет найти нужный канал, текст, аудио или документ.

• Телеграм бот @TGStat_Bot -  покажет статистику любого канала, группы, публикации в Telegram.

• https://lyzem.com/ - полностью самостоятельный поисковик по телеграм/Telegraph.

• https://cse.google.com/cse?cx=006368593537057042503%3Aefxu7xprihg&ref=exploit.media#gsc.tab=0 - сервис использующий гугл для поиска по чатам и каналам.

• https://cse.google.com/cse?cx=f4046a4505f1e4b48 - еще один сервис использующий гугл для поиска по чатам и каналам.
""",
            'prev': 'nickname',
    'next': 'car'
},

        'car': {
        'text': """
инструменты для поиска информации по гос. номеру машины.

Сайты 🖥

• unda - https://www.unda.com.ua/proverka-gosnomer-UA
• vin01 - https://vin01.ru/
• vinformer - https://vinformer.su/
• avtokompromat - https://avtokompromat.ru/user/gosvin.php

Все 4 имеют примерно одинаковый функционал, но иногда на одном сайте есть информация, которой нет на других, так что пользуйтесь несколькими для лучшего результата.

Боты 🤖

• UniversalSearch - @UniversalSearchEasyBot
• GTASearch - @Iditinahyubot
• QuickOSINT - @tearch_bot

Боты на самом деле универсальны, но именно в них поиск по номеру авто мне приглянулся больше.
""",
        'prev': 'searchtg',  # предыдущий раздел
    'next': 'intelligence_x' # следующий раздел
},
         'intelligence_x': {
            'text': """
Intelligence X (intelx.io) — это поисковая система для анализа данных из разных источников, включая веб, даркнет и утечки баз данных. Она позволяет искать информацию по доменам, IP-адресам, email и документам, а также просматривать утекшие пароли, логи и файлы. Пользователи могут искать данные как в открытом доступе, так и в закрытых сетях. Сервис предлагает бесплатные и платные тарифы, с расширенными возможностями для глубокого поиска.
""",
            'prev': 'car',
            'next': 'webwhois'
},
               'webwhois': {
            'text': """
Инструмент для анализа сайтов Web-Check

• Web-check - ОСИНТ инструмент с открытым исходным кодом с помощью которого вы получите представление о внутренней работе конкретного веб-сайта.

• В настоящее время на панели мониторинга отображаются: информация о IP, цепочка SSL, записи DNS, файлы cookie, заголовки, информация о домене, правила сканирования при поиске, карта страниц, местоположение сервера, реестр перенаправлений, открытые порты, трассировка, расширения безопасности DNS, производительность сайта, трекеры, связанные имена хостов, углеродный след.

• Полезно для понимания инфраструктуры сайта и дальнейшей разведки.

Сайт: Web-Check.xyz
GitHub: github.com/Lissy93/web-check

-----------

• Wayback Machine - смотрим, разные версии того, как выглядел конкретный сайт ранее.

Сайт: https://archive.org
""",
            'prev': 'intelligence_x',
            'next': 'terms'
},

'terms': {
            'text': """
OSINT (Open Source Intelligence) — это разведка на основе открытых источников. Она включает в себя сбор, анализ и использование информации, которая доступна из публичных, открытых источников, таких как интернет, социальные сети, блоги, новостные сайты, правительственные отчеты, базы данных и другие общедоступные ресурсы.

Doxing — это процесс публичного раскрытия личной информации о человеке без его согласия. Эта информация может включать имя, адрес, телефонный номер, электронную почту, семейные данные, документы и другие личные сведения. Часто доксинг используется в интернете для того, чтобы нанести вред или запугать человека, раскрыв его конфиденциальные данные. Методы получения данных могут варьироваться: от использования общедоступных источников, таких как социальные сети, до применения методов OSINT, о которых мы ранее говорили.


SWAT — это кибер-атака, когда злоумышленники делают ложные вызовы в полицию, чтобы устроить спецоперацию у жертвы, обычно с участием SWAT. Они используют социальную инженерию и подделку данных, чтобы создать ложное ощущение угрозы, например, заложников или бомбы. Это приводит к опасным и унизительным ситуациям для жертвы и может иметь серьезные юридические последствия.


Деанон — это процесс раскрытия реальной личности или идентичности человека, который ранее оставался анонимным в интернете. Обычно это происходит путём сбора, анализа и сопоставления различных данных, таких как IP-адреса, аккаунты в социальных сетях, фотографии, метаданные и другая личная информация, доступная в сети. Цель деанона может варьироваться: от личных конфликтов и шантажа до расследований и юридических действий.

DDoS (Distributed Denial of Service) атака — это попытка перегрузить сервер, сеть или другое сетевое устройство, чтобы они не могли предоставлять услуги пользователям. Это достигается путём координированной отправки большого объема трафика на целевую систему. Атаки DDoS могут быть направлены на различные цели и имеют множество форм.

Фишинг — это форма киберпреступления, при которой злоумышленники пытаются обманным путем получить конфиденциальную информацию у жертвы, такую как логины, пароли, данные банковских карт, или другие личные данные. Это достигается путем отправки сообщений, которые выглядят как официальные письма от доверенных организаций (например, банков, социальных сетей, государственных учреждений), но на самом деле направляют жертву на поддельный сайт, имитирующий оригинальный. На этом фальшивом сайте пользователь вводит свою информацию, думая, что взаимодействует с законной организацией, а злоумышленники собирают введенные данные для последующего использования в мошеннических действиях.

Сквоттинг доменов — это практика регистрации, покупки или использования доменных имен, которые совпадают или очень похожи на зарегистрированные торговые марки, имена компаний или известных личностей, с целью их последующей перепродажи с прибылью или использования в мошеннических целях.

Брутфорс (или метод перебора, brute force) — это метод атаки на системы защиты, при котором злоумышленник последовательно перебирает все возможные комбинации паролей, ключей или других данных до тех пор, пока не найдет правильное значение.

Киберсталкинг — это форма преследования или домогательства, которая осуществляется с использованием цифровых технологий, таких как интернет, социальные сети, электронная почта, мессенджеры и другие онлайн-коммуникации. В отличие от традиционного сталкинга, киберсталкинг может происходить на расстоянии, и жертвы могут подвергаться преследованию из любой точки мира.

Фарминг — перенаправление жертвы с легитимного сайта на фейковый, где собираются данные, подобно фишингу, но с применением технических методов.

SQL-инъекция — способ взлома баз данных через внедрение вредоносных SQL-запросов в поля ввода на сайтах. Это позволяет получать доступ к личным данным пользователей.
""",
            'prev': 'webwhois',
            'next': 'photo'
},

'photo': {
            'text': """
Узнай место по фотке.

• GeoSpy AI [https://geospy.ai] - полезный инструмент, использующий искусственный интеллект для определения местоположения на основе фотографии.

• Выдает подробное описание местоположения и примерные координаты.

• GeoSpy AI не просто полагается на общие элементы изображения, а учитывает контекстные подсказки, что обеспечивает более точный результат, так что советую использовать детализированные фото.

• Инструмент не всегда точен: зачастую представляет общую территорию, например большой город.
""",
            'prev': 'terms',
            'next': 'osintetaps'
},

'osintetaps': {
            'text': """
• Сегодня поверхностно рассмотрим разведывательный цикл, а точнее его составляющие.

• Разведывательный цикл состоит из:

• Определения цели.
• Определения точек входа.
• Формирования гипотезы.
• Сбора данных.
• Анализа собранных данных.
• Проверки гипотез.
• Корректировки.
• Подведения итогов.
""",
            'prev': 'photo',
            'next': 'vpns'
},

'vpns': {
            'text': """
• VPN - Virtual Private Network -  Виртуальная Частная Сеть - это технология, позволяющая безопасно и анонимно подключаться к интернету. Она создает зашифрованный туннель между вашим устройством и VPN-сервером, скрывая ваш IP-адрес и шифруя весь ваш трафик.
• Как это работает?
• В отличие от проски, который по сути просто является посредником между вами и сервером, VPN использует различные методы шифрования трафика. 


    
Лучшие VPN сервисы, которые помогут вам скрыться:

• Lantern [https://play.google.com/store/apps/details?id=org.getlantern.lantern] — создает одноранговую пиринговую сеть распределённой файловой системой IPFS, в отличие от VPN он использует децентрализованное распределение сети.
• Что это значит?
• Одноранговая - все участники сети равны между собой.
• Децентрализованная -  каждый участник сети является узлом.
• У lantern есть встроенная возможность анонимно делиться файлами, все так же децентрализовано, это означает, что если вы загрузите файл, вы уже не сможете его удалить.
• Lantern есть на любые операционные сети и он так же легок в настройке.

А так же VPN от Samsung:

• Samsung Max VPN [https://play.google.com/store/apps/details?id=com.opera.max.global] — впн приложение, которое имеет защиту личных данных, экономию трафика, подключение к облаку, включение защита конфиденциальности, изменять местоположение, использование DNS серверов и так-же сканирование сети Wi-Fi
""",
            'prev': 'osintetaps',
            'next': 'hackermistakes'
},

'hackermistakes': {
            'text': """
Типичные ошибки хакеров.

• В этом посте мы рассмотрим, какие ошибки приводят к деанонимизации и поимке хакеров.

• На самом деле хакеров губят не супертехнологии и не киберспецагенты. Глупость, лень, и излишняя самоуверенность - вот что раскрывает большинство преступлений.

• Лень.

• Любой человек подвержен лени, как самый простой пример - проверить свой ip перед началом. Вдруг VPN дал сбой или вы вовсе забыли его включить. Если это единственное, что отделяет вас от незаконных дел, не поленитесь проверить подключение.

• Самоуверенность.

• Не считайте себя всемогущим, не думайте, что вас невозможно найти. Сколько бы слоев защиты вас не защищало, в теории все это возможно вычислить, максимально отделяйте свою повседневную жизнь от незаконной. Ставьте сложные пароли, даже если думаете, что вас не найдут.

• Глупость.

• Если уж и думаете делать что-то незаконное, то изучите все подводные камни, не используйте открытые каналы связи, не оставляйте следов, ну и не расскрывайте свою личность.

• Эти 3 очевидных и глупых ошибки стоили тюремного срока многим хакерам, так что не будьте ленивыми, глупыми и самоуверенными.
""",
            'prev': 'vpns',
            'next': 'googledork'
},

'googledork': {
            'text': """
https://telegra.ph/Google-Dork-09-11
""",
            'prev': 'hackermistakes',
            'next': 'vpntoproxy'
},
'vpntoproxy': {
            'text': """
Всё о VPN:

1. Политика NO-LOG (без ведения журналов)
   - Настоящая политика no-log, которая означает, что VPN не ведет учет активности пользователя: посещенные сайты, IP-адреса, временные метки подключений, объем переданных данных и другие метаданные.
   - В идеале, эту политику должна была бы подтвердить независимая проверка, проведенная сторонними аудиторами.

2. Сильное шифрование
   - Шифрование должно быть на уровне AES-256 (Advanced Encryption Standard) — это стандарт военной и банковской безопасности.
   - Поддержка Perfect Forward Secrecy (PFS) — технология, которая обеспечивает уникальные ключи шифрования для каждого сеанса, чтобы взлом одного ключа не скомпрометировал всю историю сеансов.

3. Протоколы безопасности
   - VPN должен поддерживать несколько надежных протоколов, таких как **OpenVPN**, **WireGuard**, или **IKEv2/IPSec**. Эти протоколы обеспечивают быструю передачу данных и высокую защиту.
   - Поддержка Stealth Mode или Obfuscation (замаскированный VPN) для обхода блокировок в странах с жесткой цензурой.

4. Kill Switch (автоматическое отключение)
   - Kill Switch — это функция, которая автоматически разрывает интернет-соединение, если VPN по какой-то причине отключился. Это предотвращает утечку данных через незащищенное соединение.

5. DNS и IP защита от утечек
   - VPN должен иметь встроенные механизмы для предотвращения утечек DNS, IP и WebRTC (которые могут раскрыть ваш реальный IP-адрес или DNS-запросы).
   
6. Многократное шифрование (Double VPN)
   - Double VPN (или MultiHop) — технология, при которой интернет-трафик пользователя проходит через два разных VPN-сервера в разных странах, обеспечивая дополнительную защиту и анонимность.

7. Раздельное туннелирование (Split Tunneling)
   - Позволяет пользователю выбирать, какой трафик идет через VPN, а какой — напрямую через интернет. Это особенно полезно для повышения скорости и оптимизации соединения.

8. Независимость от юрисдикций с требованием передачи данных
   - VPN должен быть зарегистрирован в стране, где нет законов о хранении данных (например, Швейцария, Панама, Исландия). Это защитит пользователя от возможных требований властей о передаче данных.
   - Он должен не подчиняться международным соглашениям о совместном доступе к информации, таким как 5/9/14-Eyes Alliances (альянсы стран по обмену разведданными).

9. Поддержка Tor over VPN (или Onion over VPN)
   - Это возможность использовать сеть Tor через VPN для обеспечения максимальной анонимности. Трафик сначала шифруется через VPN, а затем проходит через узлы сети Tor, добавляя дополнительный слой безопасности.

10. Анонимные способы оплаты
   - VPN должен принимать анонимные методы оплаты, такие как криптовалюты (Bitcoin, Monero), подарочные карты, чтобы исключить возможность отслеживания личности через финансовые транзакции.

11. Маскировка трафика (Obfuscation)
   - VPN должен иметь инструменты для маскировки трафика, чтобы он не выглядел как трафик VPN. Это особенно важно в странах, где блокируют VPN (например, Китай, Россия, Иран).

12. Быстрая скорость и широкая сеть серверов
   - Наличие глобальной сети серверов для обеспечения высокой скорости и обхода гео-блокировок. Чем больше серверов, тем меньше перегрузка и больше выбор стран для подключения.
   
13. Поддержка множества устройств и платформ
   - VPN должен поддерживать все основные операционные системы (Windows, MacOS, Linux, iOS, Android), а также устройства типа роутеров, смарт-ТВ и игровых консолей.

14. Независимые аудиты безопасности
   - Для подтверждения своей надежности, VPN должен регулярно проходить независимые аудиты, которые проверяют, что политика no-log и безопасность соответствуют заявленным стандартам.

15. Круглосуточная поддержка
   - Наличие компетентной и оперативной службы поддержки 24/7 через чаты, email или другие средства связи, чтобы пользователь мог всегда получить помощь при необходимости.

--------------------

Продолжить читать:
https://telegra.ph/Prodolzhenie-soobshcheniya-10-10
""",
            'prev': 'googledork',
            'next': 'services'
},
'services': {
            'text': """
Сайты / сервисы, которые могут вам пригодится в будещем:

https://telegra.ph/Servisy-FRONEST-10-20
""",
            'prev': 'vpntoproxy',
            'next': 'osint_services'
      }  
}


    
    topic_info = topics[call.data]
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(text="Назад", callback_data=topic_info['prev']),
        InlineKeyboardButton(text="Вперёд", callback_data=topic_info['next'])
    )

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=topic_info['text'], reply_markup=keyboard)
# Конец функции OSINT сервисов /osint









# Функция приветствия /start
# Функция для создания клавиатуры с кнопкой запроса номера телефона
def request_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_phone = KeyboardButton(text="Отправить номер телефона", request_contact=True)
    keyboard.add(button_phone)
    return keyboard

# Функция для создания инлайн-клавиатуры с кнопкой подписки
def create_subscription_keyboard():
    keyboard = InlineKeyboardMarkup()
    url_button = InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_ID[1:]}")
    check_button = InlineKeyboardButton(text="Я подписался", callback_data="check_subscription")
    keyboard.add(url_button)
    keyboard.add(check_button)
    return keyboard

# Функция проверки подписки пользователя на канал
def check_subscription(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except telebot.apihelper.ApiException:
        return False

# Функция проверки наличия пользователя в CSV файле
def is_user_in_csv(user_id):
    url = f"https://api.github.com/repos/{REPO}/contents/users.csv"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = base64.b64decode(response.json()['content']).decode('utf-8')
        return str(user_id) in content
    return False

# Функция приветствия /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if is_user_in_csv(user_id):
        welcome_text = (
            "Добро пожаловать в FRONEST (Free Resources of OSINT & Network Security Tools)!\n\n"
            "⬇️ Примеры команд для ввода:\n\n"
            "🔍 Поиск информации в различных поисковых системах [Интернет, даркнет]\n"
            "└  /search\n\n"
            "🗺🌍 Сбор и анализ геопространственных данных\n"
            "└  /geoint\n\n"
            "🎭 Маскировка ссылок\n"
            "└  /mask\n\n"
            "🗺 Проверка информации по IP-адресу\n"
            "└  /checkip\n\n"
            "🤖 Использование Gemini AI для поиска и анализа\n"
            "└ /gemini\n\n"
            "🌐 Взаимодействие с сайтами\n"
            "├ 🌍 Открытие сайта и извлечение информации: /opensite\n"
            "├ 🌎 Скачивание файлов с сайта: /parse\n"
            "└ 🌏 Создание простого сайта [.zip файл]: Функция в BETA-тесте и ограничена\n\n"
            "🅰🅿🅺 Полезные приложения для hacking\n"
            "└/apks\n\n"
            "🕵️‍♂️📡 Доркинг поиск по файлам в интернете\n"
            "└/dorks\n\n"
            "👁 Пробив информации по людям\n"
            "└/q\n\n"
            "💬 Доступ к OSINT сервисам и инструментам\n"
            "└ в разработке"
        )
        bot.send_message(message.chat.id, welcome_text)
    else:
        if check_subscription(user_id):
            bot.send_message(
                message.chat.id,
                "Для завершения регистрации отправьте свой номер телефона. Ваши данные останутся конфиденциальными и не будут переданы третьим лицам:",
                reply_markup=request_phone_keyboard()
            )
        else:
            bot.reply_to(
                message,
                "Для использования бота необходимо подписаться на наш канал.",
                reply_markup=create_subscription_keyboard()
            )

# Обработка нажатия кнопки "Я подписался"
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check_subscription(call):
    user_id = call.from_user.id
    if check_subscription(user_id):
        bot.answer_callback_query(call.id, "Спасибо за подписку! Теперь отправьте свой номер телефона.")
        bot.send_message(
            call.message.chat.id,
            "Для завершения регистрации отправьте свой номер телефона. Ваши данные останутся конфиденциальными и не будут переданы третьим лицам:",
            reply_markup=request_phone_keyboard()
        )
    else:
        bot.answer_callback_query(call.id, "Вы еще не подписались на канал. Пожалуйста, подпишитесь и попробуйте снова.")

# Обработка контакта (номера телефона)
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact is not None:
        phone_number = message.contact.phone_number
        user_id = message.from_user.id
        username = f"@{message.from_user.username}" if message.from_user.username else "Нет username"
        first_name = message.from_user.first_name or "Нет имени"
        last_name = message.from_user.last_name or "Нет фамилии"
        chat_type = message.chat.type
        language_code = message.from_user.language_code or "Неизвестно"

        # Формируем строку с данными пользователя
        user_data = (
            f"{phone_number} | {user_id} | {username} | {first_name} | {last_name} | "
            f"{chat_type} | {language_code} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        update_github_file('users.csv', user_data, message)

        # Приветственное сообщение после отправки номера телефона
        welcome_text = (
            "Добро пожаловать в FRONEST (Free Resources of OSINT & Network Security Tools)!\n\n"
            "⬇️ Примеры команд для ввода:\n\n"
            "🔍 Поиск информации в различных поисковых системах [Интернет, даркнет]\n"
            "└  /search\n\n"
            "🗺🌍 Сбор и анализ геопространственных данных\n"
            "└  /geoint\n\n"
            "🎭 Маскировка ссылок\n"
            "└  /mask\n\n"
            "🗺 Проверка информации по IP-адресу\n"
            "└  /checkip\n\n"
            "🤖 Использование Gemini AI для поиска и анализа\n"
            "└ /gemini\n\n"
            "🌐 Взаимодействие с сайтами\n"
            "├ 🌍 Открытие сайта и извлечение информации: /opensite\n"
            "├ 🌎 Скачивание файлов с сайта: /parse\n"
            "└ 🌏 Создание простого сайта [.zip файл]: Функция в BETA-тесте и ограничена\n\n"
            "🅰🅿🅺 Полезные приложения для hacking\n"
            "└/apks\n\n"
            "🕵️‍♂️📡 Доркинг поиск по файлам в интернете\n"
            "└/dorks\n\n"
            "👁 Пробив информации по людям\n"
            "└/q\n\n"
            "💬 Доступ к OSINT сервисам и инструментам\n"
            "└ в разработке"
        )
        bot.send_message(message.chat.id, welcome_text)

# Обновление файла на GitHub
def update_github_file(filename, new_data, message):
    url = f"https://api.github.com/repos/{REPO}/contents/{filename}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_data = response.json()
        sha = file_data['sha']
        content = base64.b64decode(file_data['content']).decode('utf-8')
        updated_content = content + new_data
    else:
        sha = None
        header = "Phone Number | User ID | Username | First Name | Last Name | Chat Type | Language Code | Registration Date\n"
        updated_content = header + new_data

    encoded_content = base64.b64encode(updated_content.encode('utf-8')).decode('utf-8')
    data = {
        "message": "Обновлен файл users.csv",
        "content": encoded_content,
        "sha": sha
    }

    response = requests.put(url, headers=headers, data=json.dumps(data))

    if response.status_code in [200, 201]:
        bot.send_message(message.chat.id, "Данные успешно сохранены!")
    else:
        bot.send_message(message.chat.id, f"Ошибка при сохранении данных: {response.json().get('message')}")
# Конец команды /start








    
# Переменная для отслеживания текущего активного процесса (либо 'extract', либо 'screenshot')
current_process = None

user_texts = {}
user_titles = {}
user_urls = {}

# Команда /opensite
@bot.message_handler(commands=['opensite'])
def handle_opensite(message):
    # Отображаем клавиатуру с действиями
    show_open_site_options(message)

def show_open_site_options(message):
    # Создаем клавиатуру с двумя кнопками: "Извлечь текст" и "Сделать скриншот"
    keyboard = InlineKeyboardMarkup()
    extract_text_button = InlineKeyboardButton('ИЗВЛЕЧЬ ТЕКСТ', callback_data='extract_text')
    screenshot_button = InlineKeyboardButton('СДЕЛАТЬ СКРИНШОТ', callback_data='make_screenshot')
    keyboard.row(extract_text_button)
    keyboard.row(screenshot_button)
    
    # Отправляем сообщение с выбором
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=keyboard)

# Обработчик кнопки "ИЗВЛЕЧЬ ТЕКСТ"
@bot.callback_query_handler(func=lambda call: call.data == 'extract_text')
def request_url_for_text_extraction(call):
    global current_process
    bot.answer_callback_query(call.id)
    
    # Если в процессе другой функционал, завершаем его
    if current_process == 'screenshot':
        bot.send_message(call.message.chat.id, "Завершаем предыдущий процесс. Пожалуйста, отправьте ссылку заново.")
    
    current_process = 'extract'
    bot.send_message(call.message.chat.id, "Пожалуйста, отправьте ссылку на сайт, с которого нужно извлечь текст.")

    @bot.message_handler(func=lambda message: current_process == 'extract')
    def extract_text_from_url(message):
        global current_process
        if current_process != 'extract':
            return

        url = message.text
        try:
            response = requests.get(url)
            response.raise_for_status()  # Проверяем статус ответа
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.title.string if soup.title else 'Без заголовка'
            text = soup.get_text()
            chunks = [text[i:i+4096] for i in range(0, len(text), 4096)]  # Разбиваем текст на части по 4096 символов

            user_texts[message.chat.id] = chunks
            user_titles[message.chat.id] = title
            user_urls[message.chat.id] = url

            bot.send_message(message.chat.id, f"Заголовок: {title}\nТекст страницы:")
            bot.send_message(message.chat.id, chunks[0], reply_markup=create_markup(0, len(chunks), title, url))
        
        except requests.exceptions.RequestException as e:
            bot.send_message(message.chat.id, f"Не удалось получить доступ к сайту: {str(e)}")
        
        # Завершаем процесс
        current_process = None

# Обработчик кнопки "СДЕЛАТЬ СКРИНШОТ"
@bot.callback_query_handler(func=lambda call: call.data == 'make_screenshot')
def request_url_for_screenshot(call):
    global current_process
    bot.answer_callback_query(call.id)

    # Если в процессе другой функционал, завершаем его
    if current_process == 'extract':
        bot.send_message(call.message.chat.id, "Завершаем предыдущий процесс. Пожалуйста, отправьте ссылку заново.")
    
    current_process = 'screenshot'
    bot.send_message(call.message.chat.id, "Пожалуйста, отправьте ссылку на сайт, для которого нужно сделать скриншот.")

    @bot.message_handler(func=lambda message: current_process == 'screenshot')
    def process_screenshot(message):
        global current_process
        if current_process != 'screenshot':
            return

        url = message.text.strip()
        if not url.startswith(('http://', 'https://')):
            bot.reply_to(message, "Пожалуйста, введите корректный URL, начинающийся с http:// или https://")
            return

        bot.reply_to(message, "Создаю скриншот. Пожалуйста, подождите...")
        screenshot_path = take_screenshot(url)
        
        if screenshot_path:
            with open(screenshot_path, 'rb') as file:
                bot.send_photo(message.chat.id, file, caption=f"Скриншот сайта {url}")
            os.remove(screenshot_path)
        else:
            bot.reply_to(message, "Произошла ошибка при создании скриншота. Попробуйте снова.")
        
        # Завершаем процесс
        current_process = None

# Функция создания скриншота
def take_screenshot(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        logger.info(f"Загружена страница: {url}")
        time.sleep(random.uniform(2, 5))  # Имитация времени загрузки страницы
        
        screenshot_path = 'page_screenshot.png'
        driver.save_screenshot(screenshot_path)
        logger.info("Скриншот сохранен")
        return screenshot_path

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return None

    finally:
        driver.quit()

# Функция для создания разметки кнопок навигации по тексту
def create_markup(current_page, total_pages, title, url):
    markup = InlineKeyboardMarkup()
    if current_page > 0:
        prev_button = InlineKeyboardButton("Назад", callback_data=f"prev:{current_page}")
        markup.add(prev_button)
    if current_page < total_pages - 1:
        next_button = InlineKeyboardButton("Вперед", callback_data=f"next:{current_page}")
        markup.add(next_button)
    return markup

# Обработчик перехода по страницам текста
@bot.callback_query_handler(func=lambda call: call.data.startswith('prev') or call.data.startswith('next'))
def callback_query(call):
    try:
        chat_id = call.message.chat.id
        if chat_id not in user_texts:
            bot.answer_callback_query(call.id, "Текст не найден. Попробуйте отправить ссылку снова.")
            return

        action, current_page = call.data.split(':')
        current_page = int(current_page)

        chunks = user_texts[chat_id]

        if action == "prev" and current_page > 0:
            current_page -= 1
        elif action == "next" and current_page < len(chunks) - 1:
            current_page += 1
        else:
            bot.answer_callback_query(call.id, "Вы достигли края текста.")
            return

        new_text = chunks[current_page] if chunks[current_page].strip() else "Эта страница пуста."

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=new_text,
            reply_markup=create_markup(current_page, len(chunks), user_titles[chat_id], user_urls[chat_id])
        )
        bot.answer_callback_query(call.id)
    except Exception as e:
        error_message = f"Ошибка при обработке callback query: {str(e)}"
        bot.send_message(chat_id, error_message)
        bot.answer_callback_query(call.id, "Произошла ошибка при обработке вашего запроса.")
# Конец команды /opensite




 



# Обработчик сообщений с "pn"
@bot.message_handler(func=lambda message: message.text.lower().startswith("pn"))
def handle_phone_lookup_text(message):
    phone_number = message.text[2:].strip()  # Удаляем "pn" и любые пробелы

    # Если номер не начинается с "+", добавляем его
    if not phone_number.startswith("+"):
        phone_number = "+" + phone_number

    response, original_number = phone_lookup(phone_number)

    if original_number:
        # Создание Inline клавиатуры с кнопками
        markup = InlineKeyboardMarkup()
        encoded_number = urllib.parse.quote(original_number)
        telegram_url = f"https://t.me/{encoded_number}"
        viber_url = f"https://botapi.co/viber/{encoded_number}?&gclid=25662590:6b357895f6c29c75a7554a70834bdaf0&_bk=cloudflare"
        whatsapp_url = f"https://api.whatsapp.com/send/?phone={encoded_number.replace('+', '')}&text&type=phone_number&app_absent=0"

        markup.add(InlineKeyboardButton("Открыть в Telegram", url=telegram_url))
        markup.add(InlineKeyboardButton("Открыть в Viber", url=viber_url))
        markup.add(InlineKeyboardButton("Открыть в WhatsApp", url=whatsapp_url))

        bot.send_message(message.chat.id, response, reply_markup=markup)
    else:
        bot.reply_to(message, response)
# Конец обработчика "pn"


# Команда /createsite
@bot.message_handler(commands=['createsite'])
def handle_createsite(message):
    msg = bot.send_message(message.chat.id, "Введите название для нового сайта:")
    bot.register_next_step_handler(msg, process_repo_creation)

def process_repo_creation(message):
    repo_name = message.text
    repo = create_github_repo(repo_name)
    bot.reply_to(message, f"Репозиторий {repo_name} создан. Теперь отправьте ZIP-файл с файлами для сайта.")
    bot.register_next_step_handler(message, process_site_files, repo)

def process_site_files(message, repo):
    if message.document and message.document.mime_type == 'application/zip':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open('site_files.zip', 'wb') as new_file:
            new_file.write(downloaded_file)

        upload_files_to_repo(repo, 'site_files.zip')
        bot.reply_to(message, "Файлы успешно загружены в репозиторий.")

        success, site_url = enable_github_pages(repo)
        if success:
            bot.send_message(message.chat.id, f"GitHub Pages включены. Ваш сайт доступен по адресу: {site_url}")
        else:
            bot.send_message(message.chat.id, "Не удалось включить GitHub Pages. Пожалуйста, проверьте настройки репозитория вручную.")
    else:
        bot.reply_to(message, "Пожалуйста, отпра вьте ZIP-файл.")
        bot.register_next_step_handler(message, process_site_files, repo)
# Конец команды /createsite



# Команда /search
@bot.message_handler(commands=['search'])
def handle_search(message):
    show_search_engines(message)
    
def show_search_engines(message):
    keyboard = InlineKeyboardMarkup()
    aol_button = InlineKeyboardButton('AOL ПОИСК', callback_data='aol_search')
    google_button = InlineKeyboardButton('GOOGLE ПОИСК', callback_data='google_search')
    bing_button = InlineKeyboardButton('BING ПОИСК', callback_data='bing_search')
    ahmia_button = InlineKeyboardButton('AHMIA ПОИСК', callback_data='ahmia_search')
    keyboard.add(aol_button, google_button, bing_button, ahmia_button)

    message_text = """🌐 ПОПУЛЯРНЫЕ ПОИСКОВИКИ
├── AOL ПОИСК
│   └── это альтернатива BING
│    
├── GOOGLE ПОИСК
│   └── обычный поиск по интернету
│  
├── BING ПОИСК
│   └── может пригодится если AOL не работает
│
└── AHMIA ПОИСК
    └── поиск по скрытому сегменту интернета"""

    bot.send_message(message.chat.id, message_text, reply_markup=keyboard)
    
@bot.callback_query_handler(func=lambda call: call.data in ['aol_search', 'google_search', 'bing_search', 'ahmia_search'])
def ask_for_search_query(call):
    search_type = call.data.split('_')[0].capitalize()
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, f"Введите запрос для поиска в {search_type}:")
    bot.register_next_step_handler(msg, process_search, search_type.lower())

def process_search(message, search_type):
    query = message.text
    if search_type == 'aol':
        response_text, keyboard = perform_aol_search(query)
    elif search_type == 'google':
        response_text, keyboard = perform_google_search(query)
    elif search_type == 'bing':
        response_text, keyboard = perform_bing_search(query)
    elif search_type == 'ahmia':
        response_text, keyboard = perform_ahmia_search(query)
    else:
        response_text = "Неизвестный тип поиска."
        keyboard = None

    bot.send_message(message.chat.id, response_text, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('aol_search_page', 'google_search_page', 'bing_search_page', 'ahmia_search_page')))
def handle_pagination(call):
    search_type, query, page = call.data.split(";")
    page = int(page)
    search_type = search_type.split('_')[0]
    
    if search_type == 'aol':
        response_text, keyboard = perform_aol_search(query, page)
    elif search_type == 'google':
        response_text, keyboard = perform_google_search(query, page)
    elif search_type == 'bing':
        response_text, keyboard = perform_bing_search(query, page)
    elif search_type == 'ahmia':
        response_text, keyboard = perform_ahmia_search(query, page)
    else:
        response_text = "Неизвестный тип поиска."
        keyboard = None

    # Обновляем сообщение с новыми результатами
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=response_text,
        reply_markup=keyboard
    )

    # Отвечаем на callback query, чтобы убрать "часы загрузки" на кнопке
    bot.answer_callback_query(call.id)
# Конец команды /search


# Команда /mask
@bot.message_handler(commands=['mask'])
def handle_mask(message):
    msg = bot.send_message(message.chat.id, "Введите ссылку для маскировки:")
    bot.register_next_step_handler(msg, process_link_masking)
    
def process_link_masking(message):
    link = message.text
    masked_links = masklink(link)
    bot.reply_to(message, masked_links)
# Конец команды /mask


# Команда /сheckip
@bot.message_handler(commands=['checkip'])
def handle_checkip(message):
    msg = bot.send_message(message.chat.id, "Введите IP-адрес для проверки:")
    bot.register_next_step_handler(msg, process_ip_check)

def process_ip_check(message):
    ip_address = message.text.strip()
    bot.reply_to(message, f"Ищу данные для IP: {ip_address}. Пожалуйста, подождите.")
    
    parsed_text, screenshot_path = parse_geolocation_data(ip_address)
    
    if parsed_text and screenshot_path:
        formatted_text = format_data(parsed_text)
        with open(screenshot_path, 'rb') as file:
            bot.send_photo(message.chat.id, file, caption=f"Данные для IP {ip_address}:\n{formatted_text}")
        os.remove(screenshot_path)
    else:
        bot.reply_to(message, "Произошла ошибка при получении данных. Попробуйте снова.")
# Конец команды /checkip



# Команда /parse
@bot.message_handler(commands=['parse'])
def handle_parse(message):
    msg = bot.send_message(message.chat.id, "Введите ссылку для скачивания файлов сайта [BETA]:")
    bot.register_next_step_handler(msg, process_parse_site)

def process_parse_site(message):
    url = message.text.strip()
    if not url.startswith(('http://', 'https://')):
        bot.reply_to(message, "Пожалуйста, отправьте корректный URL, начинающийся с http:// или https://")
        return

    bot.reply_to(message, "Обрабатываю ваш запрос. Это может занять некоторое время...")

    zip_buffer, zip_filename = parse_site(url)

    if zip_buffer:
        bot.send_document(message.chat.id, zip_buffer, visible_file_name=zip_filename)
        bot.send_message(message.chat.id, "Вот ваш ZIP-файл, содержащий все файлы из корневой директории!")
    else:
        bot.send_message(message.chat.id, "Не удалось найти файлы для скачивания.")
# Конец команды /parse


# Команда /gemini
@bot.message_handler(commands=['gemini'])
def handle_gemini(message):
    msg = bot.send_message(message.chat.id, "Введите запрос для Gemini:")
    bot.register_next_step_handler(msg, process_gemini_query)

def process_gemini_query(message):
    query = message.text
    bot.send_message(message.chat.id, "Обрабатываю ваш запрос. Это может занять некоторое время...")
    response = perform_gemini_with_aol_search(query)
    bot.reply_to(message, response)
# Конец команды /gemini




# Команда /geoint
# Функция для проверки, является ли строка кадастровым номером
def is_cadastral_number(text):
    return ':' in text and any(char.isdigit() for char in text) and not text.startswith(('http://', 'https://'))

# Функция для проверки, являются ли введенные данные координатами
def is_coordinates(text):
    parts = text.split(',')
    if len(parts) != 2:
        return False
    try:
        lat, lon = float(parts[0]), float(parts[1])
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except ValueError:
        return False

# Обработчик команды /geoint
@bot.message_handler(commands=['geoint'])
def request_input(message):
    markup = InlineKeyboardMarkup()
    button_coordinates = InlineKeyboardButton("ПО КООРДИНАТАМ", callback_data="request_coordinates")
    button_cadastral = InlineKeyboardButton("КАДАСТРОВЫЙ НОМЕР 🇺🇦", callback_data="request_cadastral")
    markup.add(button_coordinates)
    markup.add(button_cadastral)
    bot.send_message(message.chat.id, "Выберите тип ввода:", reply_markup=markup)

# Обработчик callback-запроса для кнопки "ПО КООРДИНАТАМ"
@bot.callback_query_handler(func=lambda call: call.data == "request_coordinates")
def callback_coordinates(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Пожалуйста, введите координаты в формате: 50.503716,30.809038")

# Обработчик callback-запроса для кнопки "КАДАСТРОВЫЙ НОМЕР"
@bot.callback_query_handler(func=lambda call: call.data == "request_cadastral")
def callback_cadastral(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Пожалуйста, введите кадастровый номер")

# Обработчик ввода координат
@bot.message_handler(func=lambda message: is_coordinates(message.text))
def handle_coordinates(message):
    coordinates = message.text.strip()
    lat, lon = map(float, coordinates.split(','))
    
    google_maps_url = f"https://www.google.com/maps?ll={lat},{lon}&q={lat},{lon}&hl=en&t=m&z=15"
    bing_maps_url = f"https://www.bing.com/maps/?v=2&cp={lat}~{lon}&style=r&lvl=15&sp=Point.{lat}_{lon}____"
    apple_maps_url = f"https://maps.apple.com/maps?ll={lat},{lon}&q={lat},{lon}&t=m"
    yandex_maps_url = f"https://maps.yandex.com/?ll={lon},{lat}&spn=0.01,0.01&l=sat,skl&pt={lon},{lat}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Google Maps", url=google_maps_url))
    markup.add(InlineKeyboardButton("Bing Maps", url=bing_maps_url))
    markup.add(InlineKeyboardButton("Apple Maps", url=apple_maps_url))
    markup.add(InlineKeyboardButton("Yandex Maps", url=yandex_maps_url))
    
    bot.reply_to(message, f"По данным координатам найдены такие результаты:", reply_markup=markup)


# Send image and additional buttons
    # Дополнительные ресурсы
    image_url = "https://i.postimg.cc/t4LXnfqX/1000474879.png"
    caption = "Дополнительные ресурсы:"
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Arcgis", url=f"https://livingatlas.arcgis.com/wayback/#localChangesOnly=true&ext={lon},{lat},{lon},{lat}"),
        InlineKeyboardButton("EarthEngine", url=f"https://earthengine.google.com/timelapse/#v={lat},{lon},15,latLng&t=3.04"),
        InlineKeyboardButton("Sentinel", url=f"https://apps.sentinel-hub.com/sentinel-playground/?source=S2L2A&lat={lat}&lng={lon}")
    )
    bot.send_photo(message.chat.id, image_url, caption=caption, reply_markup=markup)

    # Генерация ссылок с координатами
    toolforge_url = f"https://osm-gadget-leaflet.toolforge.org/#/?lat={lat}&lon={lon}&zoom=15&lang=commons"
    yandex_url = f"https://yandex.com/maps/?l=sat%2Cpht&ll={lon}%2C{lat}&pt={lon},{lat}&z=15"
    flickr_url = f"https://www.flickr.com/map?&fLat={lat}&fLon={lon}&zl=17"
    
    # Первое сообщение с фото и тремя кнопками
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Toolforge", url=toolforge_url),
        InlineKeyboardButton("Yandex", url=yandex_url),
        InlineKeyboardButton("Flickr", url=flickr_url)
    )
    
    bot.send_photo(message.chat.id, 'https://i.postimg.cc/dQhTtC42/1000474891.png', caption="Результаты по введенным координатам:", reply_markup=markup)
    
    # Далее добавляем остальные фото и кнопки
    send_photos_with_buttons(message.chat.id, lat, lon)

def send_photos_with_buttons(chat_id, lat, lon):
    # Второе сообщение
    pastvu_url = f"https://pastvu.com/?g={lat},{lon}&z=16&s=osm&t=mapnik&type=1"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Pastvu", url=pastvu_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/63Mp9ByB/1000474905.png', reply_markup=markup)
    
    # Третье сообщение
    zoom_earth_url = f"https://zoom.earth/#view={lat},{lon},8z/date=,+0/layers=wind,fires"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Zoom Earth", url=zoom_earth_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/GpqCDqrQ/1000474913.png', reply_markup=markup)
    
    # Четвертое сообщение
    peakfinder_url = f"https://www.peakfinder.org/?lat={lat}&lng={lon}&name=The%20Antipodes%20of%20"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("PeakFinder", url=peakfinder_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/TPwRCZtS/1000474918.png', reply_markup=markup)

    # Пятое сообщение
    wikimapia_url = f"http://wikimapia.org/m/#lang=en&lat={lat}&lon={lon}&z=15&m=b"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Wikimapia", url=wikimapia_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/QMH3pctZ/1000474926.png', reply_markup=markup)

    # Шестое сообщение
    copernix_url = f"https://copernix.io/#?where={lon},{lat},15&query=&pagename=?language=en"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Copernix", url=copernix_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/rygfL3jg/1000474936.png', reply_markup=markup)

    # Седьмое сообщение
    strava_url = f"https://labs.strava.com/heatmap/#15.11/{lon}/{lat}/hot/all"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Strava", url=strava_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/Hs0m9p93/1000474945.png', reply_markup=markup)

    # Восьмое сообщение с двумя кнопками
    openstreet_url = f"https://openstreetbrowser.org/#map=15/{lat}/{lon}"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("OpenStreetBrowser", url=openstreet_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/mk2YpZFM/1000474954.png', reply_markup=markup)

    # Девятое сообщение с тремя кнопками
    cities_url = f"https://www.360cities.net/map?lat={lat}&lng={lon}&zoom=15"
    kartaview_url = f"https://kartaview.org/map/@{lat},{lon},17z"
    mapillary_url = f"https://www.mapillary.com/app/?menu=false&lat={lat}&lng={lon}&z=17&mapStyle=Mapillary+satellite"
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("360 Cities", url=cities_url),
        InlineKeyboardButton("KartaView", url=kartaview_url),
        InlineKeyboardButton("Mapillary", url=mapillary_url)
    )
    bot.send_photo(chat_id, 'https://i.postimg.cc/RFqCgjZh/1000474962.png', reply_markup=markup)

    # Десятое сообщение
    kadastr_url = f"https://kadastr.live/#16.30/{lat}/{lon}"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Kadastr", url=kadastr_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/Wz8kqWTb/1000475071.png', reply_markup=markup)

    # 11 Сообщение
    rosreestr_url = f"https://росреестра-выписка.рус/кадастровая_карта#ct={lat}&cg={lon}&zoom=18"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Росреестр", url=rosreestr_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/L63PBmjz/1000475079.png', reply_markup=markup)

    # 11 Сообщение
    deepstate_url = f"https://deepstatemap.live/#18/{lat}/{lon}"
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("DeepState", url=deepstate_url))
    bot.send_photo(chat_id, 'https://i.postimg.cc/1zhr6J7x/1000476132.png', reply_markup=markup)

# Обработчик ввода кадастрового номера
@bot.message_handler(func=lambda message: is_cadastral_number(message.text))
def handle_cadastral_number(message):
    cadastral_number = message.text.strip()
    url = f'https://opendatabot.ua/l/{cadastral_number}?from=search'
    bot.send_message(message.chat.id, f"Обрабатываю данные по кадастровому номеру: {cadastral_number}")
    
    screenshot_path, description = parse_opendatabot_page(url)
    
    if screenshot_path:
        with open(screenshot_path, 'rb') as file:
            bot.send_photo(message.chat.id, file, caption=description)
        os.remove(screenshot_path)
    else:
        bot.send_message(message.chat.id, "Не удалось получить информацию по указанному кадастровому номеру.")

# Функция для закрытия драйвера при завершении работы
def shutdown():
    close_driver()
# Конец команды /geoint 


# Функционал команды /apks
@bot.message_handler(commands=['apks'])
def handle_apks(message):
    apks_info = """
Привет! Ты попал в мир APK-файлов.

Здесь ты найдешь различные инструменты для декомпиляции, анализа, проверки и исследования приложений на Android. Выбери нужную опцию:
"""
    keyboard = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton(text="Apk Mods Store", callback_data="decompile_apk"),
        InlineKeyboardButton(text="Fake GPS Location", callback_data="analyze_permissions"),
        InlineKeyboardButton(text="Password Manager", callback_data="static_analysis"),
        InlineKeyboardButton(text="WI-FI", callback_data="dynamic_analysis"),
        InlineKeyboardButton(text="Подпись APK", callback_data="sign_apk"),
        InlineKeyboardButton(text="Проверка на вирусы", callback_data="virus_check"),
        InlineKeyboardButton(text="APKTool", callback_data="apktool"),
        InlineKeyboardButton(text="JADX GUI", callback_data="jadx_gui"),
        InlineKeyboardButton(text="Анализ DEX", callback_data="dex_analysis"),
        InlineKeyboardButton(text="Прочие инструменты", callback_data="other_tools")
    ]
    keyboard.add(*buttons[:2])
    keyboard.add(*buttons[2:4])
    keyboard.add(*buttons[4:6])
    keyboard.add(*buttons[6:8])
    keyboard.add(*buttons[8:])

    bot.send_message(message.chat.id, apks_info, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data in ['decompile_apk', 'analyze_permissions', 'static_analysis', 'dynamic_analysis', 'sign_apk', 'virus_check', 'apktool', 'jadx_gui', 'dex_analysis', 'other_tools', 'return_to_menu'])
def handle_apks_topics(call):
    bot.answer_callback_query(call.id)

    topics = {
        'decompile_apk': {
            'text': """
Lite APKS.com - приложение/сайт, самый лучший для скачивания крякнутых приложений.
https://upload.app/download/liteapks/com.liteapks.androidapps/67215d3af5ad10d84e1ba0e394ea3d5e7e93ead81bdfd05cd572247aed28d5b7
""",
            'prev': None,  # Первая тема, нет кнопки "Назад"
            'next': 'analyze_permissions'
        },
        'analyze_permissions': {
            'text': """
Fake GPS Location - легко изменить своё местоположение GPS.
https://upload.app/download/fake-gps-location/com.hopefactory2021.fakegpslocation/b03356e6200024a86277d4dacbaef03aebaab138fc507a623bbdac05601552c6
""",
            'prev': 'decompile_apk',
            'next': 'static_analysis'
        },
        'static_analysis': {
            'text': """
KPASS - сохранение своих паролей в надёжном месте, всё сохраняется в одном файле, есть экспорт файла.
https://play.google.com/store/apps/details?id=com.korovan.kpass
""",
            'prev': 'analyze_permissions',
            'next': 'dynamic_analysis'
        },
        'dynamic_analysis': {
            'text': """
1. WiFiMan - скенер сети, обноружение сетевых устройств, и много других плюшек
https://play.google.com/store/apps/details?id=com.ubnt.usurvey

2. Wigle WiFi - список сетей, карта сетей по GPS, база данных, исследование сетей
https://play.google.com/store/apps/details?id=net.wigle.wigleandroid

3.  WiFi Tools - узнать многл чего о вашем устройстве, маршрутизаторе.
https://play.google.com/store/apps/details?id=com.ddm.iptoolslight

4. WpsApp - взлом Wifi сетей
https://play.google.com/store/apps/details?id=com.themausoft.wpsapp

5. WiFi File Transfer - поделиться файлами с помощью WiFi, без интернета
https://upload.app/download/wifi-file-transfer-pro/com.smarterdroid.wififiletransferpro/1ac9ea8f9f8e95d2ca9ae9dc5fc534111fd7c7749275c9b4ee9ad4c2ec652f24

6. WiFi клавиатура - использование пк для взаимодействия с клавиатурой телефона
https://upload.app/download/wifikeyboard/com.volosyukivan/38374bb6573c4dca9fd58788ba120542b0aac592c55f276d4b0bbbe957d4a3dc
""",
            'prev': 'static_analysis',
            'next': 'sign_apk'
        },
        'sign_apk': {
            'text': """
Подпись APK — это важный шаг для развертывания приложения. Здесь ты узнаешь, как правильно подписывать APK-файлы.
""",
            'prev': 'dynamic_analysis',
            'next': 'virus_check'
        },
        'virus_check': {
            'text': """
Проверка APK на вирусы и вредоносные программы с использованием различных онлайн-сервисов и антивирусных программ.
""",
            'prev': 'sign_apk',
            'next': 'apktool'
        },
        'apktool': {
            'text': """
APKTool — мощный инструмент для декомпиляции и повторной компиляции APK. Используй его для редактирования исходного кода.
""",
            'prev': 'virus_check',
            'next': 'jadx_gui'
        },
        'jadx_gui': {
            'text': """
JADX GUI — графический интерфейс для декомпиляции APK и изучения Java-кода приложений.
""",
            'prev': 'apktool',
            'next': 'dex_analysis'
        },
        'dex_analysis': {
            'text': """
Анализ DEX-файлов — это изучение байт-кода приложения, который содержит основную логику работы программы.
""",
            'prev': 'jadx_gui',
            'next': 'other_tools'
        },
        'other_tools': {
            'text': """
Прочие инструменты для анализа APK, такие как MobSF, JADX, Androguard и другие, помогут исследовать приложения более глубоко.
""",
            'prev': 'dex_analysis',
            'next': None  # Последняя тема, нет кнопки "Вперед"
        }
    }

    if call.data == 'return_to_menu':
        handle_apks(call.message)
        return

    topic_info = topics[call.data]
    
    # Создаем клавиатуру для навигации
    keyboard = InlineKeyboardMarkup()

    if topic_info['prev']:
        prev_button = InlineKeyboardButton("Назад", callback_data=topic_info['prev'])
        keyboard.add(prev_button)

    if topic_info['next']:
        next_button = InlineKeyboardButton("Вперед", callback_data=topic_info['next'])
        keyboard.add(next_button)
    else:
        # Если это последняя тема, кнопка "Вперед" не добавляется
        last_button = InlineKeyboardButton("Конец списка", callback_data='end_of_list')
        keyboard.add(last_button)

    # Кнопка для возврата в меню
    return_button = InlineKeyboardButton("Вернуться в меню", callback_data='return_to_menu')
    keyboard.add(return_button)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=topic_info['text'], reply_markup=keyboard)
# Конец команды /apks

# Команда /q
@bot.message_handler(commands=['q'])
def handle_q(message):
    bot.send_message(message.chat.id, """
⬇️ Примеры Сообщений для Бота:

📱 Поиск по Номеру Телефона
 └ 💬 pn380********* | pn7**********

✈️ Поиск по Telegram
 ├ 💬 id281485304
 └ 💬 @durov

👨 Поиск по Имени
 ├ 💬 Иванов Иван Иванович
 └ 💬 Иванов Иван 05.02.1994

🚗 Поиск по VIN, Гос.Номеру Авто
 ├ 💬 XTA212140J2311550 
 └ 💬 Н777ОН777

👤 Поиск по Ссылке в Соц.Сети
 ├ 💬 vk.com/id577744097
 ├ 💬 instagram.com/ev.antipov
 ├ 💬 ok.ru/profile/382881 
 ├ 💬 fb.com/profile.php?id=1
... а так же по id**** или @UserName
 ├ 💬 id281485304
 └ 💬 @durov

📇 Поиск по Паспорту
 └ 💬 6113825395

📑 Поиск по ИНН
 └ 💬 784806113663

🎫 Поиск по СНИЛС
 └ 💬 13046964250

📨 Поиск по E-mail
 └ 💬 tema@gmail.com

💳 Поиск по Номеру Карты
 └ 💬 4276550070006000

🏚 Поиск по Адресу
 └ 💬 Москва, Герасима Курина, 14к2

📸 Поиск по Фото
 └ 💬 Отправьте боту фото Человека или Предмета, чтобы найти информацию о нем.

🌐 Наш сайт • 🤖 Резервный Бот 4
""")
# конец команды /q








# Начало обработчика id
# Функция для создания инлайн-кнопок выбора направления
def create_search_direction_keyboard(id_value):
    keyboard = InlineKeyboardMarkup()
    btn_telegram = InlineKeyboardButton(text="Telegram", callback_data=f"search_telegram_{id_value}")
    btn_vk = InlineKeyboardButton(text="Вконтакте", callback_data=f"search_vk_{id_value}")
    btn_ok = InlineKeyboardButton(text="Одноклассники", callback_data=f"search_ok_{id_value}")
    btn_instagram = InlineKeyboardButton(text="Instagram", callback_data=f"search_instagram_{id_value}")
    btn_facebook = InlineKeyboardButton(text="Facebook", callback_data=f"search_facebook_{id_value}")
    keyboard.row(btn_telegram)
    keyboard.row(btn_vk, btn_ok)
    keyboard.row(btn_instagram, btn_facebook)
    return keyboard

# Обработчик сообщений, начинающихся с "id"
@bot.message_handler(func=lambda message: message.text.lower().startswith("id"))
def handle_id_search(message):
    id_value = message.text[2:].strip()
    bot.reply_to(
        message,
        f"🆔 id{id_value}\n└  Выберите направление поиска",
        reply_markup=create_search_direction_keyboard(id_value)
    )

# Функция для получения содержимого файла users.csv с GitHub
def get_users_file():
    url = f"https://api.github.com/repos/fonesst/usersFRONEST/contents/users.csv"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = response.json()['content']
        decoded_content = base64.b64decode(content).decode('utf-8')
        return decoded_content.splitlines()
    else:
        print(f"Ошибка при получении файла users.csv: {response.json().get('message')}")
        return None

# Функция для поиска информации о пользователе по user_id в файле users.csv
def find_user_info(user_id):
    users_data = get_users_file()
    if users_data:
        for line in users_data:
            parts = line.split('|')
            if len(parts) >= 8 and parts[1].strip() == str(user_id):
                return {
                    "phone": parts[0].strip(),
                    "id": parts[1].strip(),
                    "username": parts[2].strip(),
                    "first_name": parts[3].strip(),
                    "last_name": parts[4].strip(),
                    "chat_type": parts[5].strip(),
                    "language": parts[6].strip(),
                    "added_date": parts[7].strip()
                }
    return None

# Обработчик нажатий на кнопки с выбором платформы
@bot.callback_query_handler(func=lambda call: call.data.startswith("search_"))
def handle_search_callback(call):
    direction, id_value = call.data.split("_")[1], call.data.split("_")[2]
    
    if direction == "telegram":
        user_info = find_user_info(id_value)

        if user_info:
            report_text = (
                f"🔎 ОТЧЁТ ПО ЗАПРОСУ:\n"
                f" └  Telegram: id{id_value}\n\n"
                f"📋 Отчёт содержит:\n"
                f"├📧 ID: {user_info['id']}\n"
                f"├📞 Телефон: {user_info['phone']}\n"
                f"├👤 Юзернейм: {user_info['username']}\n"
                f"├🏷 Имя Фамилия: {user_info['first_name']} {user_info['last_name']}\n"
                f"├💬 Тип чата: {user_info['chat_type']}\n"
                f"├🌎 Язык устройства: {user_info['language']}\n"
                f"└📆 Дата добавления: {user_info['added_date']}"
            )
            
            # Создаем инлайн кнопку "Проверить БД «глаз бога»"
            keyboard = InlineKeyboardMarkup()
            check_db_btn = InlineKeyboardButton("Проверить БД «глаз бога»", callback_data=f"check_db_{id_value}")
            keyboard.add(check_db_btn)
            
            # Отправляем сообщение с отчетом и кнопкой
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text=report_text, reply_markup=keyboard)
        else:
            # Добавляем кнопку для поиска в "глазе бога" даже если информация не найдена
            keyboard = InlineKeyboardMarkup()
            check_db_btn = InlineKeyboardButton("Проверить БД «глаз бога»", callback_data=f"check_db_{id_value}")
            keyboard.add(check_db_btn)

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                                  text=f"Информация для id{id_value} не найдена.", reply_markup=keyboard)
    else:
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text=f"Функция для поиска по {direction} пока не реализована.")

# Функция для поиска в файлах gb0.csv и gb1.csv
def search_in_gb_files(user_id):
    files_to_check = ['gb0.csv', 'gb1.csv']
    for file_name in files_to_check:
        url = f"https://api.github.com/repos/fonesst/usersFRONEST/contents/{file_name}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()['content']
            decoded_content = base64.b64decode(content).decode('utf-8')
            for line in decoded_content.splitlines():
                parts = line.split(',')
                if len(parts) >= 5 and parts[0].strip() == str(user_id):
                    return {
                        "id": parts[0].strip(),
                        "phone": parts[1].strip(),
                        "username": parts[2].strip(),
                        "first_name": parts[3].strip(),
                        "last_name": parts[4].strip()
                    }
    return None

# Обработчик нажатия на кнопку "Проверить БД «глаз бога»"
@bot.callback_query_handler(func=lambda call: call.data.startswith("check_db_"))
def handle_check_db_callback(call):
    id_value = call.data.split("_")[2]
    user_info = search_in_gb_files(id_value)
    
    if user_info:
        report_text = (
            "💦 В слитой базе данных Telegram-бота «Глаз Бога» содержится информация о 774 тысячах пользователей. "
            "Включены данные, такие как ID пользователей, номера телефонов, имена и фамилии. "
            "База данных стала «утекшей» в июле 2021 года.\n\n"
            "📋 Отчёт содержит:\n"
            f"├📧 ID: {user_info['id']}\n"
            f"├📞 Телефон: {user_info['phone']}\n"
            f"├👤 Юзернейм: {user_info['username']}\n"
            f"├🏷 Имя: {user_info['first_name']}\n"
            f"└🏷 Фамилия: {user_info['last_name']}"
        )
    else:
        report_text = (
            "💦 В слитой базе данных Telegram-бота «Глаз Бога» содержится информация о 774 тысячах пользователей. "
            "Включены данные, такие как ID пользователей, номера телефонов, имена и фамилии. "
            "База данных стала «утекшей» в июле 2021 года.\n\n"
            f"Информация для id{id_value} не найдена в базе данных «Глаз Бога»."
        )
    
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                          text=report_text)
# Конец обработчика id










# Запуск бота
try:
    bot.polling(none_stop=True)
except Exception as e:
    logging.error(f"Ошибка: {e}")
finally:
    from ip import driver
    driver.quit()  # Закрываем браузер при завершении работы программы
