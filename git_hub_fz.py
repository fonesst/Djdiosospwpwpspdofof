import os
import zipfile
import requests
from github import Github

GITHUB_TOKEN = 'ghp_6pYJ2MhVm34iNdwJCR00SNvXrjy9BN28QT2p'
g = Github(GITHUB_TOKEN)

def create_github_repo(repo_name):
    user = g.get_user()
    repo = user.create_repo(repo_name, private=False)
    return repo

def upload_files_to_repo(repo, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall('temp_site_files')

    for root, dirs, files in os.walk('temp_site_files'):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'rb') as f:
                content = f.read()
            repo.create_file(file_path.replace('temp_site_files/', ''), f"Add {file}", content)

    # Clean up temporary files
    os.remove(zip_file_path)
    for root, dirs, files in os.walk('temp_site_files', topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    os.rmdir('temp_site_files')

def enable_github_pages(repo):
    url = f"https://api.github.com/repos/{repo.full_name}/pages"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.switcheroo-preview+json"
    }
    data = {
        "source": {
            "branch": "main",
            "path": "/"
        }
    }
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        site_url = f"https://{repo.owner.login}.github.io/{repo.name}"
        return True, site_url
    else:
        return False, None
