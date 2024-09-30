# osint_services.py

from main import bot  # Импортируем объект bot

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

def handle_osint_services(call):
    bot.answer_callback_query(call.id)
    
    osint_info = """
Привет, Искатель Знаний!

Ты вступил на тропу OSINT — искусства сбора данных из открытых источников. Это не просто инструменты, это твои ключи к миру информации. За каждым запросом скрываются секреты

Ты вступаешь на путь хакинга и разведки. Но помни — ответственность и закон всегда идут рядом. Используй своё знание с умом

Твоя разведка начинается здесь 𖤍
"""
    bot.send_message(call.message.chat.id, osint_info)
    
    keyboard = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton(text="NETSTALKING", callback_data="netstalking")
    keyboard.add(button1)
    
    bot.send_message(call.message.chat.id, "Выберите опцию:", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data == "netstalking")
def handle_netstalking_callback(call):
    netstalking_info = """
Если просто, то нетсталкинг — это поиск секретов интернета.
Нетсталкинг опирается на теорию о трех уровнях интернета, согласно которому существует всем известный открытый интернет, так называемая видимая сеть, в которой информация доступа для всех желающих и достижима с помощью обычного сетевого поиска. Второй уровень, глубокая сеть, с ресурсами, которые недоступны через обычный поиск — находится в особом поле зрении искателей секретов, так как этот сегмент сети имеет большое количество контента. Третий уровень это уже даркнет со всеми вытекающими ухищрениями для пользования — нет привычных всем адресов http формата, обязательно нужно приложение для входа (например, TOR браузер).
"""
    bot.send_message(call.message.chat.id, netstalking_info)