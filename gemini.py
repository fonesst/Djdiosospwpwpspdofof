import requests
from bs4 import BeautifulSoup

GEMINI_API_KEY = 'AIzaSyDlIJZ3gAae5S_owNcETNahJvLYwPpFEwA'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

def perform_search_for_gemini(query):
    url = f"https://search.aol.com/search?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = soup.find_all('div', class_='algo-sr')[:5]
    if results:
        response_text = ""
        for result in results:
            title = result.find('h3').text.strip()
            link = result.find('a')['href']
            description = result.find('p').text.strip() if result.find('p') else 'Описание недоступно'
            response_text += f"{title}\n{description}\n{link}\n\n"
    else:
        response_text = "Результатов нет."
    return response_text

def get_gemini_response(query):
    payload = {
        "contents": [{
            "parts": [{
                "text": query
            }]
        }]
    }
    headers = {
        'Content-Type': 'application/json',
    }
    response = requests.post(f'{GEMINI_API_URL}?key={GEMINI_API_KEY}', json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        result = data['candidates'][0]['content']['parts'][0]['text']
        return result
    else:
        return "Извините, произошла ошибка при обработке запроса в Gemini."

def perform_gemini_with_aol_search(user_query):
    aol_results = perform_search_for_gemini(user_query)
    combined_query = f"Основывайся только лишь на информации найденной в интернете, которую я тебе предоставил, а так-же аккультурь эту информацию.\n\nЗапрос пользователя для тебя:\n{user_query}\n\nНиже информация, найденная в интернете:\n{aol_results}"
    gemini_response = get_gemini_response(combined_query)
    return gemini_response.lower()