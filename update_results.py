"""
update_results.py — тянет РЕАЛЬНЫЕ результаты матчей ЧМ-2026 в api_data.json.

Источник: football-data.org (бесплатный тариф, нужен токен).
  1. Регистрация: https://www.football-data.org/client/register
  2. Получи бесплатный API-токен
  3. GitHub → Settings → Secrets → Actions → New secret:
       Имя:  FOOTBALL_DATA_TOKEN
       Значение: твой токен

Турнир ЧМ имеет код 'WC'. Скрипт пишет в api_data.json массив "results":
  [{ "t1":"Мексика","t2":"Юж. Африка","score1":2,"score2":1,
     "status":"FINISHED","utcDate":"2026-06-11T19:00:00Z","winner":"HOME_TEAM" }, ...]

Имена команд переводятся в TEAM_RU РОВНО так, как в DB сайта,
иначе фронтенд не сопоставит результат с матчем.
"""
import os
import json
from datetime import datetime

try:
    import requests
except ImportError:
    print("⚠️  Модуль requests не установлен. Запусти: pip install requests")
    raise

TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
COMPETITION = "WC"
BASE = "https://api.football-data.org/v4"

# Англ. имя из API  ->  рус. имя ТОЧНО как в DB сайта
TEAM_RU = {
    "Mexico": "Мексика",
    "South Africa": "Юж. Африка",
    "South Korea": "Ю. Корея",
    "Korea Republic": "Ю. Корея",
    "Czech Republic": "Чехия",
    "Czechia": "Чехия",
    "Canada": "Канада",
    "Bosnia and Herzegovina": "Босния и Г.",
    "Bosnia-Herzegovina": "Босния и Г.",
    "USA": "США",
    "United States": "США",
    "Paraguay": "Парагвай",
    "Qatar": "Катар",
    "Switzerland": "Швейцария",
    "Brazil": "Бразилия",
    "Morocco": "Марокко",
    "Haiti": "Гаити",
    "Scotland": "Шотландия",
    "Australia": "Австралия",
    "Turkey": "Турция",
    "Türkiye": "Турция",
    "Turkiye": "Турция",
    "Germany": "Германия",
    "Curacao": "Кюрасао",
    "Curaçao": "Кюрасао",
    "Netherlands": "Нидерланды",
    "Japan": "Япония",
    "Cote d'Ivoire": "Кот-д'Ивуар",
    "Côte d'Ivoire": "Кот-д'Ивуар",
    "Ivory Coast": "Кот-д'Ивуар",
    "Ecuador": "Эквадор",
    "Sweden": "Швеция",
    "Tunisia": "Тунис",
    "Belgium": "Бельгия",
    "Egypt": "Египет",
    "Iran": "Иран",
    "New Zealand": "Нов. Зеландия",
    "Spain": "Испания",
    "Cape Verde": "Кабо-Верде",
    "Cabo Verde": "Кабо-Верде",
    "Saudi Arabia": "Саудовская Аравия",
    "Uruguay": "Уругвай",
    "France": "Франция",
    "Senegal": "Сенегал",
    "Iraq": "Ирак",
    "Norway": "Норвегия",
    "Argentina": "Аргентина",
    "Algeria": "Алжир",
    "Austria": "Австрия",
    "Jordan": "Иордания",
    "Portugal": "Португалия",
    "DR Congo": "ДРК",
    "Congo DR": "ДРК",
    "Democratic Republic of Congo": "ДРК",
    "DR Congo (Congo-Kinshasa)": "ДРК",
    "England": "Англия",
    "Croatia": "Хорватия",
    "Ghana": "Гана",
    "Panama": "Панама",
    "Uzbekistan": "Узбекистан",
    "Colombia": "Колумбия",
}


def ru(name):
    """Переводит англ. имя в русское. Если нет в словаре — возвращает как есть и предупреждает."""
    if name in TEAM_RU:
        return TEAM_RU[name]
    # Пробуем без учёта регистра / лишних слов
    for en, rus in TEAM_RU.items():
        if en.lower() == (name or "").lower():
            return rus
    print(f"   ⚠️  Нет перевода для команды: '{name}' — оставляю как есть")
    return name


def fetch_results():
    if not TOKEN:
        print("⚠️  FOOTBALL_DATA_TOKEN не задан в секретах GitHub — результаты не обновляются.")
        return None
    headers = {"X-Auth-Token": TOKEN}
    url = f"{BASE}/competitions/{COMPETITION}/matches"
    try:
        print(f"Запрос: {url}")
        r = requests.get(url, headers=headers, timeout=25)
        print(f"HTTP статус: {r.status_code}")
        remaining = r.headers.get("X-Requests-Available-Minute", "?")
        print(f"Запросов осталось в минуту: {remaining}")
        if r.status_code == 403:
            print("❌ 403 Forbidden — твой бесплатный тариф НЕ включает турнир WC.")
            print("   football-data.org даёт ЧМ только на платном тарифе ($$$).")
            print("   Используй ручной ввод результатов через админ-панель сайта,")
            print("   либо подключи другой источник (см. ниже в инструкции).")
            return None
        if r.status_code == 429:
            print("❌ 429 — превышен лимит запросов. Подожди минуту.")
            return None
        if r.status_code != 200:
            print(f"❌ Ошибка: {r.text[:300]}")
            return None
        return r.json()
    except Exception as e:
        print(f"❌ Исключение при запросе: {e}")
        return None


def parse_results(data):
    out = []
    matches = (data or {}).get("matches", [])
    print(f"Матчей получено от API: {len(matches)}")
    finished = 0
    live = 0
    for m in matches:
        home = (m.get("homeTeam") or {}).get("name") or "?"
        away = (m.get("awayTeam") or {}).get("name") or "?"
        ft = (m.get("score") or {}).get("fullTime") or {}
        status = m.get("status")
        if status == "FINISHED":
            finished += 1
        elif status in ("IN_PLAY", "PAUSED"):
            live += 1
        out.append({
            "t1": ru(home),
            "t2": ru(away),
            "score1": ft.get("home"),
            "score2": ft.get("away"),
            "status": status,
            "utcDate": m.get("utcDate"),
            "winner": (m.get("score") or {}).get("winner"),
        })
    print(f"   Завершённых: {finished}, идут сейчас: {live}")
    return out


def main():
    # читаем текущий api_data.json
    try:
        with open("api_data.json", "r", encoding="utf-8") as f:
            api_data = json.load(f)
    except Exception:
        api_data = {}

    raw = fetch_results()
    results = parse_results(raw) if raw else []

    if results:
        api_data["results"] = results
        api_data["results_updated"] = datetime.utcnow().isoformat() + "Z"
        with open("api_data.json", "w", encoding="utf-8") as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Сохранено {len(results)} матчей в api_data.json")

        # покажем последние завершённые
        fin = [r for r in results if r["status"] == "FINISHED"]
        if fin:
            print("\nПоследние результаты:")
            for r in fin[-5:]:
                print(f"   {r['t1']} {r['score1']}:{r['score2']} {r['t2']}")
    else:
        print("⚠️  Результаты не получены — api_data.json не изменён.")
        print("    Это НЕ ломает сайт: результаты можно вводить вручную через админку.")


if __name__ == "__main__":
    main()
