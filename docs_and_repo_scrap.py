import requests
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Konfiguracja
REPO = "vabene1111/recipes"
GITHUB_TOKEN = ""  # Opcjonalnie dodaj token, by uniknąć rate limitu
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
BASE_URL = "https://docs.tandoor.dev/"

def get_github_releases():
    print("Pobieranie release notes...")
    url = f"https://api.github.com/repos/{REPO}/releases"
    response = requests.get(url, headers=HEADERS)
    releases = response.json()
    
    with open("tandoor_releases.txt", "w", encoding="utf-8") as f:
        for rel in releases:
            f.write(f"VERSION: {rel['tag_name']}\nDATE: {rel['published_at']}\n")
            f.write(f"NOTES:\n{rel['body']}\n")
            f.write("-" * 50 + "\n")
    print("Zapisano tandoor_releases.txt")

def get_docs_from_repo():
    print("Pobieranie dokumentacji z repozytorium...")
    # Tandoor trzyma dokumentację w folderze /docs
    url = f"https://api.github.com/repos/{REPO}/contents/docs"
    response = requests.get(url, headers=HEADERS)
    files = response.json()
    
    with open("tandoor_docs_summary.txt", "w", encoding="utf-8") as f:
        for file in files:
            if file['type'] == 'file' and file['name'].endswith('.md'):
                content = requests.get(file['download_url']).text
                f.write(f"FILE: {file['name']}\n")
                f.write(content)
                f.write("\n\n" + "="*80 + "\n\n")
    print("Zapisano tandoor_docs_summary.txt")

def scrape_website_docs():
    visited = set()
    to_visit = [BASE_URL]
    
    with open("tandoor_website_docs.txt", "w", encoding="utf-8") as f:
        while to_visit:
            url = to_visit.pop(0)
            if url in visited:
                continue
            
            visited.add(url)
            print(f"Scrapowanie: {url}")
            
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                article = soup.find('article')
                if article:
                    text = article.get_text(separator='\n', strip=True)
                    f.write(f"URL: {url}\n\n{text}\n\n{'='*80}\n\n")
                
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(url, link['href']).split('#')[0]
                    if full_url.startswith(BASE_URL) and full_url not in visited and full_url not in to_visit:
                        to_visit.append(full_url)
                        
            except Exception as e:
                print(f"Błąd {url}: {e}")

if __name__ == "__main__":
    get_github_releases()
    get_docs_from_repo()
    scrape_website_docs()