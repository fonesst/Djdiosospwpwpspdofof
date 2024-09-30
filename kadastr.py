import time
import random
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Инициализация браузера
chrome_options = Options()
chrome_options.add_argument("--headless")  # Запуск без графического интерфейса
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Функция парсинга страницы OpenDataBot
def parse_opendatabot_page(url):
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 5))  # Задержка для загрузки страницы
        canvas_element = driver.find_element("css selector", 'canvas.leaflet-zoom-animated')
        screenshot_path = 'canvas_screenshot.png'
        canvas_element.screenshot(screenshot_path)

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        text_div = soup.select_one('div.bg-body.rounded-bottom.p-3.mb-2')
        text_content = text_div.get_text(strip=True) if text_div else "Текст не найден."
        formatted_text = format_text_content(text_content)

        return screenshot_path, formatted_text

    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return None, None

# Функция форматирования текста
def format_text_content(text_content):
    formatted_text = text_content.replace("Призначення", "➤ Призначення:\n➔") \
                                 .replace("Категорія", "\n\n➤ Категорія:\n➔") \
                                 .replace("Площа", "\n\n➤ Площа:\n➔") \
                                 .replace("Власність", "\n\n➤ Власність:\n➔")
    return formatted_text

def close_driver():
    driver.quit()
