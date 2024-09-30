import requests
from bs4 import BeautifulSoup
import os
import zipfile
import io
from urllib.parse import urljoin, urlparse

def is_file_url(url):
    file_extensions = ['.html', '.php', '.aspx', '.jsp', '.css', '.js', '.zip', '.jpg', '.jpeg', '.png', '.gif', '.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4', '.avi', '.mov']
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    return any(path.endswith(ext) for ext in file_extensions) or path.endswith('/') or '.' not in path.split('/')[-1]

def is_root_directory_url(base_url, url):
    base_parsed = urlparse(base_url)
    url_parsed = urlparse(url)
    return (base_parsed.scheme == url_parsed.scheme and
            base_parsed.netloc == url_parsed.netloc and
            len(url_parsed.path.strip('/').split('/')) <= 1)

def find_files(url):
    files = set()
    files.add('index.html')

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        for tag in soup.find_all(['a', 'link', 'script', 'img']):
            for attr in ['href', 'src']:
                file_url = tag.get(attr)
                if file_url:
                    full_url = urljoin(url, file_url)
                    if is_file_url(full_url) and is_root_directory_url(url, full_url):
                        file_name = os.path.basename(urlparse(full_url).path) or 'index.html'
                        files.add(file_name)

    except Exception as e:
        print(f"Error finding files: {e}")

    return list(files)

def download_file(url, file_name):
    try:
        response = requests.get(urljoin(url, file_name))
        return response.content
    except Exception as e:
        print(f"Error downloading {file_name}: {e}")
        return None

def create_zip(url, files):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            content = download_file(url, file)
            if content:
                zip_file.writestr(file, content)
    zip_buffer.seek(0)
    return zip_buffer

def parse_site(url):
    files = find_files(url)
    if not files:
        return None, "Файлы в корневой директории не найдены."

    zip_buffer = create_zip(url, files)
    domain = urlparse(url).netloc
    zip_filename = f"{domain}_root_files.zip"

    return zip_buffer, zip_filename