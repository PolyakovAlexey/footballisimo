"""
update_results.py — тянет РЕАЛЬНЫЕ результаты матчей ЧМ-2026 и пишет их в api_data.json.

Источник: football-data.org (бесплатный тариф, нужен токен).
  1. Зарегистрируйся на https://www.football-data.org/client/register
  2. Получи бесплатный API-токен.
  3. Добавь его в GitHub → Settings → Secrets → Actions как FOOTBALL_DATA_TOKEN.

Турнир ЧМ (FIFA World Cup) в football-data.org имеет код 'WC'.
Скрипт сохраняет в api_data.json массив "results":
  [{ "t1": "...", "t2": "...", "score1": 2, "score2": 1,
     "status": "FINISHED", "utcDate": "2026-06-11T19:00:00Z" }, ...]

Сопоставление имён команд (англ → рус, как в DB сайта) задаётся в TEAM_RU.
Дополняй TEAM_RU по мере необходимости — что не найдено, останется на англ.,
а фронтенд сопоставит по дате + частичному совпадению.
"""
import os
import json
import requests

TOKEN = os.environ.get("FOOTBALL_DATA_TOKEN", "")
COMPETITION = "WC"  # FIFA World Cup
BASE = "https://api.football-data.org/v4"

# Англ. название из API -> рус. название как в DB сайта.
# Дополняй при необходимости.
TEAM_RU = {
    "Mexico": "Мексика", "South Africa": "Юж. Африка", "South Korea": "Ю. Корея",
    "Korea Republic": "Ю. Корея", "Czech Republic": "Чехия", "Czechia": "Чехия",
    "Canada": "Канада", "Bosnia and Herzegovina": "Босния и Г.", "USA": "США",
    "United States": "США", "Paraguay": "Парагвай", "Qatar": "Катар",
    "Switzerland": "Швейцария", "Brazil": "Бразилия", "Morocco": "Марокко",
    "Haiti": "Гаити", "Scotland": "Шотландия", "Australia": "Австралия",
    "Turkey": "Турция", "Türkiye": "Турция", "Germany": "Германия",
    "Curacao": "Кюрасао", "Netherlands": "Нидерланды", "Japan": "Япония",
    "France": "Франция", "England": "Англия", "Argentina": "Аргентина",
    "Spain": "Испания", "Portugal": "Португалия", "Belgium": "Бельгия",
    "Uruguay": "Уругвай", "Colombia": "Колумбия", "Denmark": "Дания",
    "Croatia": "Хорватия", "Austria": "Австрия", "Poland": "Польша",
    "Senegal": "Сенегал", "Iran": "Иран", "Ecuador": "Эквадор",
    "Norway": "Норвегия", "Sweden": "Швеция", "Georgia": "Грузия",
    "Hungary": "Венгрия",
}


def ru(name):
    return TEAM_RU.get(name, name)


def fetch_results():
    if not TOKEN:
        print("⚠️  FOOTBALL_DATA_TOKEN не задан — результаты не обновляются.")
        return None
    headers = {"X-Auth-Token": TOKEN}
    url = f"{BASE}/competitions/{COMPETITION}/matches"
    try:
        r = requests.get(url, headers=headers, timeout=20)
        print("API статус:", r.status_code)
        if r.status_code != 200:
            print("Ошибка:", r.text[:200])
            return None
        return r.json()
    except Exception as e:
        print("Исключение:", e)
        return None


def parse_results(data):
    out = []
    for m in (data or {}).get("matches", []):
        home = m.get("homeTeam", {}).get("name") or "?"
        away = m.get("awayTeam", {}).get("name") or "?"
        ft = m.get("score", {}).get("fullTime", {})
        out.append({
            "t1": ru(home),
            "t2": ru(away),
            "score1": ft.get("home"),
            "score2": ft.get("away"),
            "status": m.get("status"),          # SCHEDULED / IN_PLAY / FINISHED
            "utcDate": m.get("utcDate"),
            "winner": m.get("score", {}).get("winner"),  # HOME_TEAM / AWAY_TEAM / DRAW
        })
    return out


def main():
    try:
        with open("api_data.json", "r", encoding="utf-8") as f:
            api_data = json.load(f)
    except Exception:
        api_data = {}

    raw = fetch_results()
    results = parse_results(raw)
    if results:
        api_data["results"] = results
        from datetime import datetime
        api_data["results_updated"] = datetime.utcnow().isoformat() + "Z"
        print(f"✅ Сохранено {len(results)} матчей с результатами/статусами")
        with open("api_data.json", "w", encoding="utf-8") as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)
        print("💾 api_data.json обновлён")
    else:
        print("⚠️  Результаты не получены — api_data.json не изменён")


if __name__ == "__main__":
    main()
