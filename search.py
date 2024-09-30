import requests
from bs4 import BeautifulSoup
import urllib.parse
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для хранения экземпляра WebDriver
driver = None

def init_driver():
    global driver
    if driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def perform_ahmia_search(search_query, page=0):
    global driver
    driver = init_driver()
    
    try:
        if page == 0:
            driver.get("https://ahmia.fi")
            logger.info("Открыт сайт ahmia.fi")
            
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
            )
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)
            logger.info(f"Введен запрос: {search_query}")
        else:
            # Прокрутка страницы вниз для загрузки дополнительных результатов
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.result:nth-child(' + str(page * 5 + 1) + ')'))
            )
        
        results = driver.find_elements(By.CSS_SELECTOR, 'li[class="result"]')
        
        if results:
            response_text = f"Результаты Ahmia для запроса '{search_query}' (страница {page+1}):\n\n"
            start_index = page * 1
            end_index = start_index + 1
            
            for i, result in enumerate(results[start_index:end_index], start=start_index+1):
                title_element = result.find_element(By.CSS_SELECTOR, 'a')
                title = title_element.text.strip() if title_element else "Заголовок не найден"
                
                link_element = result.find_element(By.CSS_SELECTOR, 'cite')
                link = link_element.text.strip() if link_element else "Ссылка не найдена"
                
                description_element = result.find_element(By.CSS_SELECTOR, 'p')
                description = description_element.text.strip() if description_element else "Описание недоступно"
                
                site_name = urllib.parse.urlparse(link).netloc
                response_text += f"{i}. 🏷 {site_name}\n🔗 {link}\n🏴‍☠️ {title}\n📋 {description}\n\n"
        else:
            response_text = "Результатов нет."
        
        keyboard = InlineKeyboardMarkup()
        next_button = InlineKeyboardButton("»", callback_data=f"ahmia_search_page;{search_query};{page+1}") if len(results) > (page + 1) * 5 else None
        prev_button = InlineKeyboardButton("«", callback_data=f"ahmia_search_page;{search_query};{page-1}") if page > 0 else None
        
        if prev_button:
            keyboard.add(prev_button)
        if next_button:
            keyboard.add(next_button)
        
        return response_text, keyboard
    
    except Exception as e:
        logger.error(f"Произошла ошибка при поиске на Ahmia: {str(e)}")
        return "Произошла ошибка при выполнении поиска.", None

def perform_aol_search(query, page=0):
    url = f"https://search.aol.com/search?q={urllib.parse.quote(query)}&b={page*10}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    results = soup.find_all('div', class_='algo-sr')
    
    if results:
        response_text = f"Результаты AOL для запроса '{query}' (страница {page+1}):\n\n"
        for i, result in enumerate(results[:1], start=page*1+1):
            title_element = result.find('h3')
            title = title_element.text.strip() if title_element else "Заголовок не найден"
            link = result.find('a')['href'] if result.find('a') else "Ссылка не найдена"
            description = result.find('p').text.strip() if result.find('p') else "Описание недоступно"
            site_name = urllib.parse.urlparse(link).netloc
            response_text += f"{i}. 🏷 {site_name}\n🔗 {link}\n🏴‍☠️ {title}\n📋 {description}\n\n"
    else:
        response_text = "Результатов нет."

    keyboard = InlineKeyboardMarkup()
    next_button = InlineKeyboardButton("»", callback_data=f"aol_search_page;{query};{page+1}")
    prev_button = InlineKeyboardButton("«", callback_data=f"aol_search_page;{query};{page-1}") if page > 0 else None

    if prev_button:
        keyboard.add(prev_button)
    keyboard.add(next_button)

    return response_text, keyboard

def perform_google_search(query, page=0):
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&start={page*10}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    results = soup.find_all('div', class_='g')
    
    if results:
        response_text = f"Результаты Google для запроса '{query}' (страница {page+1}):\n\n"
        for i, result in enumerate(results[:1], start=page*1+1):
            title_element = result.find('h3')
            title = title_element.text.strip() if title_element else "Заголовок не найден"
            link = result.find('a')['href'] if result.find('a') else "Ссылка не найдена"
            description = result.find('div', class_='VwiC3b').text.strip() if result.find('div', class_='VwiC3b') else "Описание недоступно"
            site_name = urllib.parse.urlparse(link).netloc
            response_text += f"{i}. 🏷 {site_name}\n🔗 {link}\n🏴‍☠️ {title}\n📋 {description}\n\n"
    else:
        response_text = "Результатов нет."

    keyboard = InlineKeyboardMarkup()
    next_button = InlineKeyboardButton("»", callback_data=f"google_search_page;{query};{page+1}")
    prev_button = InlineKeyboardButton("«", callback_data=f"google_search_page;{query};{page-1}") if page > 0 else None

    if prev_button:
        keyboard.add(prev_button)
    keyboard.add(next_button)

    return response_text, keyboard

def perform_bing_search(query, page=0):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}&first={(page*10)+1}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    results = soup.find_all('li', class_='b_algo')
    
    if results:
        response_text = f"Результаты Bing для запроса '{query}' (страница {page+1}):\n\n"
        for i, result in enumerate(results[:10], start=page*10+1):
            title_element = result.find('h2')
            title = title_element.text.strip() if title_element else "Заголовок не найден"
            link = result.find('a')['href'] if result.find('a') else "Ссылка не найдена"
            description = result.find('p').text.strip() if result.find('p') else "Описание недоступно"
            site_name = urllib.parse.urlparse(link).netloc
            response_text += f"{i}. 🏷 {site_name}\n🔗 {link}\n🏴‍☠️ {title}\n📋 {description}\n\n"
    else:
        response_text = "Результатов нет."

    keyboard = InlineKeyboardMarkup()
    next_button = InlineKeyboardButton("»", callback_data=f"bing_search_page;{query};{page+1}")
    prev_button = InlineKeyboardButton("«", callback_data=f"bing_search_page;{query};{page-1}") if page > 0 else None

    if prev_button:
        keyboard.add(prev_button)
    keyboard.add(next_button)

    return response_text, keyboard

def close_driver():
    global driver
    if driver:
        driver.quit()
        driver = None
