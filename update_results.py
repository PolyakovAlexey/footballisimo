"""
update_odds.py — реальные коэффициенты ЧМ-2026 с the-odds-api.com
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Источник: the-odds-api.com (агрегатор Pinnacle, Bet365, Unibet, …)
Бесплатный план: 500 запросов/месяц, без карты.

НАСТРОЙКА (один раз):
  1. Зарегистрируйся на https://the-odds-api.com
  2. Скопируй API-ключ из личного кабинета
  3. GitHub → Settings → Secrets → Actions → New repository secret
     Имя:  ODDS_API_KEY
     Значение: твой ключ

Ключ LS_COOKIE больше не нужен (старый источник — Лига Ставок).
"""
import os
import json
import requests
from datetime import datetime

API_KEY = os.environ.get("ODDS_API_KEY", "")
BASE    = "https://api.the-odds-api.com/v4"

# Английские названия команд → русские (как в DB сайта)
TEAM_RU = {
    "Mexico":                  "Мексика",
    "Czech Republic":          "Чехия",
    "Czechia":                 "Чехия",
    "South Africa":            "Юж. Африка",
    "South Korea":             "Ю. Корея",
    "Korea Republic":          "Ю. Корея",
    "Canada":                  "Канада",
    "Qatar":                   "Катар",
    "Switzerland":             "Швейцария",
    "Bosnia and Herzegovina":  "Босния и Г.",
    "Brazil":                  "Бразилия",
    "Morocco":                 "Марокко",
    "Haiti":                   "Гаити",
    "Scotland":                "Шотландия",
    "USA":                     "США",
    "United States":           "США",
    "Paraguay":                "Парагвай",
    "Australia":               "Австралия",
    "Turkey":                  "Турция",
    "Türkiye":                 "Турция",
    "Germany":                 "Германия",
    "Curacao":                 "Кюрасао",
    "Netherlands":             "Нидерланды",
    "Japan":                   "Япония",
    "Cote d'Ivoire":           "Кот-д'Ивуар",
    "Ivory Coast":             "Кот-д'Ивуар",
    "Ecuador":                 "Эквадор",
    "Sweden":                  "Швеция",
    "Tunisia":                 "Тунис",
    "Spain":                   "Испания",
    "Cape Verde":              "Кабо-Верде",
    "Belgium":                 "Бельгия",
    "Egypt":                   "Египет",
    "Saudi Arabia":            "Саудовская Аравия",
    "Uruguay":                 "Уругвай",
    "France":                  "Франция",
    "Senegal":                 "Сенегал",
    "Iraq":                    "Ирак",
    "Norway":                  "Норвегия",
    "Argentina":               "Аргентина",
    "Algeria":                 "Алжир",
    "Austria":                 "Австрия",
    "Jordan":                  "Иордания",
    "Portugal":                "Португалия",
    "DR Congo":                "ДР Конго",
    "Congo DR":                "ДР Конго",
    "Democratic Republic of Congo": "ДР Конго",
    "England":                 "Англия",
    "Croatia":                 "Хорватия",
    "Ghana":                   "Гана",
    "Panama":                  "Панама",
    "Uzbekistan":              "Узбекистан",
    "Colombia":                "Колумбия",
    "Iran":                    "Иран",
    "New Zealand":             "Нов. Зеландия",
}

def ru(name):
    return TEAM_RU.get(name, name)

def find_wc_sport(api_key):
    """Находим ключ ЧМ-2026 в списке доступных спортов."""
    try:
        r = requests.get(f"{BASE}/sports", params={"apiKey": api_key}, timeout=15)
        sports = r.json()
        # Сначала ищем 2026
        for s in sports:
            k = s.get("key", "")
            t = s.get("title", "")
            if ("2026" in k or "2026" in t) and ("world" in k.lower() or "fifa" in t.lower()):
                print(f"  Найден турнир: {k} ({t})")
                return k
        # Запасной вариант — любой WC
        for s in sports:
            if "world_cup" in s.get("key", "").lower():
                k = s["key"]
                print(f"  Запасной турнир: {k}")
                return k
    except Exception as e:
        print(f"  Ошибка поиска турнира: {e}")
    return "soccer_fifa_world_cup_2026"

def fetch_odds():
    if not API_KEY:
        print("⚠️  ODDS_API_KEY не задан — пропускаем.")
        return []

    print("Ищем турнир ЧМ-2026...")
    sport = find_wc_sport(API_KEY)

    print(f"Запрашиваем коэффициенты для: {sport}")
    try:
        r = requests.get(
            f"{BASE}/sports/{sport}/odds",
            params={
                "apiKey":      API_KEY,
                "regions":     "eu,uk",
                "markets":     "h2h",          # 1X2 (основное время)
                "oddsFormat":  "decimal",
                "bookmakers":  "pinnacle,bet365,unibet,bwin",
            },
            timeout=20,
        )
        remaining = r.headers.get("x-requests-remaining", "?")
        used      = r.headers.get("x-requests-used", "?")
        print(f"Статус: {r.status_code} | Запросов использовано: {used}, осталось: {remaining}")
        if r.status_code != 200:
            print(f"Ошибка: {r.text[:300]}")
            return []
        return r.json()
    except Exception as e:
        print(f"Исключение: {e}")
        return []

def parse_odds(events):
    """Из ответа API извлекаем средние коэффициенты по букмекерам."""
    result = []
    for ev in events:
        home = ev.get("home_team", "?")
        away = ev.get("away_team", "?")
        t1, t2 = ru(home), ru(away)

        all_k1, all_kx, all_k2 = [], [], []

        for bm in ev.get("bookmakers", []):
            for mkt in bm.get("markets", []):
                if mkt.get("key") != "h2h":
                    continue
                outcomes = {o["name"]: o["price"] for o in mkt.get("outcomes", [])}
                if home in outcomes and away in outcomes:
                    all_k1.append(outcomes[home])
                    all_k2.append(outcomes[away])
                    if "Draw" in outcomes:
                        all_kx.append(outcomes["Draw"])

        if not all_k1 or not all_kx or not all_k2:
            continue

        # Среднее по букмекерам, округляем до 2 знаков
        result.append({
            "t1":    t1,
            "t2":    t2,
            "k1":    round(sum(all_k1) / len(all_k1), 2),
            "kDraw": round(sum(all_kx) / len(all_kx), 2),
            "k2":    round(sum(all_k2) / len(all_k2), 2),
        })

    return result

def main():
    try:
        with open("api_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    raw   = fetch_odds()
    odds  = parse_odds(raw)

    if odds:
        data["odds"]         = odds
        data["odds_updated"] = datetime.utcnow().isoformat() + "Z"
        print(f"\n✅ Получено матчей с коэффициентами: {len(odds)}")
        for o in odds[:5]:
            print(f"  {o['t1']} vs {o['t2']}: {o['k1']} / {o['kDraw']} / {o['k2']}")
        with open("api_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("\n💾 api_data.json обновлён")
    else:
        print("⚠️  Коэффициенты не получены — api_data.json не изменён")

if __name__ == "__main__":
    main()
