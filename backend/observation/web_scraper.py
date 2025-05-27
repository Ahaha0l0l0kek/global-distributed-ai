import requests
from bs4 import BeautifulSoup

def scrape_page(url: str) -> str:
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(separator="\n")
        return text.strip()[:1000]  # обрезаем, чтобы не забить LLM
    except Exception as e:
        return f"Ошибка загрузки страницы: {e}"