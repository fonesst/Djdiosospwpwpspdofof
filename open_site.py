import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
import sys
import traceback

# Remove the API_TOKEN and bot initialization from here
# as they should be in the main.py file

user_texts = {}
user_titles = {}
user_urls = {}

def split_text(text, max_length=4000):
    chunks = []
    while len(text) > max_length:
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        chunks.append(text[:split_pos].strip())
        text = text[split_pos:].strip()
    chunks.append(text.strip())
    return chunks

def create_markup(current_page, total_pages, title, url):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("<<" if current_page > 0 else " ", callback_data=f"prev:{current_page}"),
        InlineKeyboardButton(f"{current_page + 1}/{total_pages}", callback_data="current"),
        InlineKeyboardButton(">>" if current_page < total_pages - 1 else " ", callback_data=f"next:{current_page}")
    )
    markup.row(InlineKeyboardButton(title[:64], url=url))
    return markup

def handle_open_site(message, bot):  # Add 'bot' as a parameter
    url = message.text
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        text = soup.get_text()
        chunks = split_text(text)
        user_texts[message.chat.id] = chunks

        title = soup.title.string if soup.title else "Без заголовка"
        user_titles[message.chat.id] = title
        user_urls[message.chat.id] = url

        if chunks:
            bot.send_message(message.chat.id, chunks[0], reply_markup=create_markup(0, len(chunks), title, url))
        else:
            bot.reply_to(message, "Не удалось извлечь текст с этой страницы.")
    except Exception as e:
        error_message = f"Ошибка при обработке URL {url}:\n{str(e)}\n\n{traceback.format_exc()}"
        bot.reply_to(message, "Произошла ошибка при обработке вашего запроса. Администратор уведомлен.")

# Remove the __main__ block and bot.polling() from here
