from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time
import random
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка Selenium WebDriver
firefox_options = Options()
firefox_options.add_argument("--headless")
firefox_options.add_argument("--no-sandbox")
firefox_options.add_argument("--disable-dev-shm-usage")
firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0")

driver = webdriver.Firefox(service=Service(), options=firefox_options)

def parse_geolocation_data(ip):
    try:
        url = f'https://www.geolocation.com/ru?ip={ip}#ipresult'
        driver.get(url)
        logger.info(f"Загружена страница: {url}")
        time.sleep(random.uniform(2, 5))

        # Извлечение данных с таблицы
        table_data = driver.find_elements(By.CSS_SELECTOR, 'table.table-ip.table-striped > tbody > tr > td')
        parsed_text = "\n".join([td.text for td in table_data if td.text != "Демо W3C Geolocation API"])
        logger.info(f"Текстовые данные успешно извлечены:\n{parsed_text}")

        # Сохранение карты как скриншота
        map_canvas = driver.find_element(By.CSS_SELECTOR, 'canvas[style^="position: absolute"]')
        screenshot_path = 'map_screenshot.png'
        map_canvas.screenshot(screenshot_path)
        logger.info("Изображение сохранено")

        return parsed_text, screenshot_path
    except Exception as e:
        logger.error(f"Произошла ошибка: {str(e)}")
        return None, None

def format_data(data):
    lines = data.split('\n')
    formatted_lines = []
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            formatted_lines.append(f"├── {lines[i]}")
            formatted_lines.append(f"│   └── {lines[i+1]}")
    formatted_text = "🌐 Данные геолокации:\n" + "\n".join(formatted_lines)
    return formatted_text
