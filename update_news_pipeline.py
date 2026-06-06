import json
import urllib.request
import xml.etree.ElementTree as ET
import re
from datetime import datetime
 
FEEDS = [
    ("https://www.sport-express.ru/services/materials/news/football/se/", "Спорт-Экспресс"),
    ("https://feeds.bbci.co.uk/sport/football/rss.xml", "BBC Sport"),
    ("https://www.rusfootball.info/rss.xml", "РусФутбол"),
    ("https://www.championat.ru/rss/news/", "Чемпионат"),
]
 
KEYWORDS = [
    "world cup", "2026", "fifa", "чм-2026", "чемпионат мира",
    "worldcup", "mundial", "сборная", "сборн", "national team",
    "squad", "группа", "плей-офф", "матч открытия", "матч отбора"
]
 
EXCLUDE = [
    "теннис", "nba", "баскетбол", "хоккей", "cs2", "counter-strike",
    "ролан гаррос", "roland", "формула", "бокс", "ufc", "mma",
    "мото", "бильярд", "шахмат", "nfl", "nhl", "volleyball",
    "бэкхем", "зенит", "рпл", "апл", "лига чемпионов",
    "кубок уефа", "лига европы", "cornish", "gilmour", "israel"
]
 
MONTHS = [
    "января","февраля","марта","апреля","мая","июня",
    "июля","августа","сентября","октября","ноября","декабря"
]
 
def clean(text):
    """Убираем HTML-теги и лишние пробелы."""
    return re.sub(r'<[^>]+>', '', text or "").strip()
 
def fetch_news():
    news = []
    now = datetime.now()
    date_str = f"{now.day} {MONTHS[now.month-1]} {now.year}"
 
    for url, src in FEEDS:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                root = ET.fromstring(r.read())
 
            items = root.findall('.//item')
            print(f"{src}: {len(items)} новостей в ленте")
 
            for item in items:
                title = clean(item.findtext('title', ''))
                desc  = clean(item.findtext('description', ''))
                link  = item.findtext('link', '')
                tl, dl = title.lower(), desc.lower()
 
                # Должно быть хотя бы одно ключевое слово про ЧМ
                if not any(kw in tl or kw in dl for kw in KEYWORDS):
                    continue
 
                # Исключаем нерелевантные темы
                if any(ex in tl or ex in dl for ex in EXCLUDE):
                    continue
 
                news.append({
                    "d": date_str,
                    "t": title[:65] + ("..." if len(title) > 65 else ""),
                    "text": (desc[:130] + "...") if len(desc) > 130 else desc,
                    "src": src,
                    "url": link
                })
 
                if len(news) >= 8:
                    break
 
        except Exception as e:
            print(f"Ошибка {src}: {e}")
 
        if len(news) >= 8:
            break
 
    return news[:8]
 
 
if __name__ == "__main__":
    print("Загружаем свежие новости о ЧМ-2026...")
    fresh = fetch_news()
    print(f"\nНайдено подходящих новостей: {len(fresh)}")
 
    for i, n in enumerate(fresh, 1):
        print(f"  {i}. [{n['src']}] {n['t']}")
 
    if not fresh:
        print("Новостей не найдено — файл не изменён.")
    else:
        try:
            with open('api_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
 
        data['news'] = fresh
 
        with open('api_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
 
        print("\napi_data.json успешно обновлён!")
