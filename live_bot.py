"""
Live match Telegram bot: голдар, сары/қызыл қағаз, ауыстырулар.
Дерек көзі: API-Football (api-sports.io), тегін тариф ~100 сұраныс/тәулік.
Қолдану:  pip install requests
Colab-та: ауыстырмалыларды төменде толтырып, файлды іске қосыңыз.
"""
import os
import time
from datetime import datetime, timezone

import requests

# ====== БАПТАУЛАР ======
BOT_TOKEN = os.getenv("BOT_TOKEN", "BOT_TOKEN_МЫНДА")      # @BotFather токені
CHAT_ID = os.getenv("CHAT_ID", "@blaugrana_kaz")           # арна немесе чат
API_KEY = os.getenv("API_KEY", "API_FOOTBALL_KEY_МЫНДА")   # dashboard.api-football.com
TEAM_ID = int(os.getenv("TEAM_ID", "529"))                 # 529 = Барселона
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "90"))        # 90 сек ≈ 80 сұраныс/матч
# =======================

API = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

# ====== ҚАЗАҚША АТТАР ======
import unicodedata

TEAMS_KK = {
    "barcelona": "Барселона", "real madrid": "Реал Мадрид", "real betis": "Бетис",
    "atletico madrid": "Атлетико Мадрид", "sevilla": "Севилья", "valencia": "Валенсия",
    "villarreal": "Вильярреал", "athletic club": "Атлетик", "real sociedad": "Реал Сосьедад",
    "girona": "Хирона", "getafe": "Хетафе", "osasuna": "Осасуна", "celta vigo": "Сельта",
    "mallorca": "Мальорка", "rayo vallecano": "Райо Вальекано", "espanyol": "Эспаньол",
    "alaves": "Алавес", "las palmas": "Лас-Пальмас", "elche": "Эльче", "levante": "Леванте",
    "real oviedo": "Овьедо", "oviedo": "Овьедо", "valladolid": "Вальядолид",
    "paris saint germain": "ПСЖ", "paris saint-germain": "ПСЖ", "bayern munich": "Бавария",
    "manchester city": "Манчестер Сити", "manchester united": "Манчестер Юнайтед",
    "liverpool": "Ливерпуль", "chelsea": "Челси", "arsenal": "Арсенал",
    "tottenham": "Тоттенхэм", "newcastle": "Ньюкасл", "inter": "Интер", "ac milan": "Милан",
    "juventus": "Ювентус", "napoli": "Наполи", "roma": "Рома", "lazio": "Лацио",
    "atalanta": "Аталанта", "borussia dortmund": "Боруссия Дортмунд",
    "bayer leverkusen": "Байер", "benfica": "Бенфика", "porto": "Порту",
    "sporting cp": "Спортинг", "ajax": "Аякс", "psv eindhoven": "ПСВ", "monaco": "Монако",
    "club brugge": "Брюгге", "olympiakos piraeus": "Олимпиакос", "slavia praha": "Славия",
}

# Ойыншылар: кілт сөз (кіші әріппен, белгісіз) -> қазақша аты. Бірінші сәйкес тұрған алынады.
PLAYERS_KK = {
    "olmo": "Дани Ольмо", "gavira": "Гави", "cubarsi": "Пау Кубарси",
    "lamine yamal": "Ламин Ямал", "yamal": "Ламин Ямал", "lewandowski": "Левандовски",
    "raphinha": "Рафинья", "pedri": "Педри", "araujo": "Рональд Араухо",
    "kounde": "Жюль Кунде", "balde": "Алехандро Бальде", "ter stegen": "тер Штеген",
    "szczesny": "Шчесны", "joan garcia": "Жоан Гарсия", "eric garcia": "Эрик Гарсия",
    "de jong": "Френки де Йонг", "casado": "Марк Касадо", "bernal": "Марк Бернал",
    "fermin": "Фермин Лопес", "ferran torres": "Ферран Торрес", "rashford": "Рашфорд",
    "bardghji": "Бардджи", "christensen": "Кристенсен", "gerard martin": "Херард Мартин",
    "gabriel jesus": "Габриэл Жезус",
    "mbappe": "Мбаппе", "vinicius": "Винисиус", "bellingham": "Беллингем",
    "courtois": "Куртуа", "rodrygo": "Родригу", "valverde": "Вальверде",
    "camavinga": "Камавинга", "tchouameni": "Чуамени", "militao": "Милитан",
    "alaba": "Алаба", "rudiger": "Рюдигер", "daniel carvajal": "Дани Карвахаль",
    "dani carvajal": "Дани Карвахаль", "alexander-arnold": "Александер-Арнольд",
    "mastantuono": "Мастантуоно", "huijsen": "Хёйсен", "endrick": "Эндрик",
    "arda guler": "Арда Гюлер", "fran garcia": "Фран Гарсия", "mendy": "Менди",
    "asencio": "Асенсио", "carreras": "Каррерас",
    "isco": "Иско", "antony": "Антони", "lo celso": "Ло Сельсо", "fornals": "Форналс",
}


def _ascii(s):
    return "".join(
        c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c)
    )


_DIGRAPHS = [("sch", "ш"), ("sh", "ш"), ("ch", "ч"), ("zh", "ж"), ("ph", "ф"),
             ("ck", "к"), ("qu", "к"), ("ll", "лл"), ("rr", "рр"), ("th", "т")]
_LETTERS = dict(zip("abdefhiklmnoprstuvwxyz",
                    "абдефхиклмнопрстувв кйз".replace(" ", "")))
_LETTERS.update({"g": "г", "j": "х", "q": "к", "w": "в", "x": "кс", "y": "й", "c": "к"})


def translit(word):
    w = _ascii(word)
    out, i = [], 0
    while i < len(w):
        for lat, kk in _DIGRAPHS:
            if w.startswith(lat, i):
                out.append(kk)
                i += len(lat)
                break
        else:
            ch = w[i]
            if ch == "c" and w[i + 1:i + 2] in ("e", "i"):
                out.append("с")
            elif ch in _LETTERS:
                out.append(_LETTERS[ch])
            else:
                out.append(ch)
            i += 1
    res = "".join(out)
    return res[:1].upper() + res[1:] if res else res


def kk_team(name):
    key = _ascii(name or "")
    if key in TEAMS_KK:
        return TEAMS_KK[key]
    for k, v in TEAMS_KK.items():
        if len(k) > 5 and k in key:
            return v
    return " ".join(translit(p) for p in (name or "").split())


def kk_player(name):
    if not name:
        return name
    key = _ascii(name)
    for k, v in PLAYERS_KK.items():
        if k in key:
            return v
    parts = name.split()
    if len(parts) > 2:  # ұзын толық аттан алғашқы және соңғы сөзді аламыз
        parts = [parts[0], parts[-1]]
    return " ".join(translit(p) for p in parts)
# ===========================


def api_get(path, **params):
    r = requests.get(f"{API}{path}", headers=HEADERS, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("response", [])


def send(text):
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text},
        timeout=20,
    )
    if not r.ok:
        print("Telegram қатесі:", r.text)


def minute(ev):
    t = ev["time"]
    m = t["elapsed"]
    return f"{m}+{t['extra']}'" if t.get("extra") else f"{m}'"


def score_line(fx):
    h, a = kk_team(fx["teams"]["home"]["name"]), kk_team(fx["teams"]["away"]["name"])
    gh, ga = fx["goals"]["home"] or 0, fx["goals"]["away"] or 0
    return f"{h} {gh}–{ga} {a}"


def format_event(ev, fx):
    typ, det = ev["type"], ev["detail"]
    team = kk_team(ev["team"]["name"])
    player = kk_player(ev["player"]["name"]) or "—"
    assist = kk_player(ev["assist"]["name"])
    m = minute(ev)

    if typ == "Goal":
        if det == "Missed Penalty":
            return f"❌ {m} Пенальти соғылмады! {player} ({team})"
        if det == "Own Goal":
            return f"⚽ ӨЗ ҚАҚПАСЫНА ГОЛ! {m} {player} ({team})\n📊 {score_line(fx)}"
        txt = f"⚽ ГОЛ! {m} {player} ({team})"
        if det == "Penalty":
            txt += " — пенальти"
        if assist:
            txt += f"\n🅰️ Ассист: {assist}"
        return txt + f"\n📊 {score_line(fx)}"

    if typ == "Card":
        if det == "Yellow Card":
            return f"🟨 Сары қағаз! {m} {player} ({team})"
        if "Red" in det:
            return f"🟥 Қызыл қағаз! {m} {player} ({team})"

    if typ == "subst":
        # API-Football: player = шыққан, assist = кірген
        return f"🔄 Ауыстыру · {team} · {m}\n🔼 Кірді: {assist}\n🔽 Шықты: {player}"

    if typ == "Var":
        return f"📺 VAR · {m} · {team}: {det}"
    return None


def event_key(ev):
    return (
        ev["time"]["elapsed"], ev["time"].get("extra"), ev["type"],
        ev["detail"], ev["team"]["id"], ev["player"]["id"], ev["assist"]["id"],
    )


def find_fixture():
    live = api_get("/fixtures", team=TEAM_ID, live="all")
    if live:
        return live[0]
    nxt = api_get("/fixtures", team=TEAM_ID, next=1)
    return nxt[0] if nxt else None


def wait_for_kickoff(fx):
    ts = fx["fixture"]["timestamp"]
    while True:
        left = ts - time.time()
        if left <= 0:
            return
        print(f"Матчқа дейін {int(left // 60)} мин")
        time.sleep(min(left, 600))


def main():
    fx = find_fixture()
    if not fx:
        print("Жақын матч табылмады")
        return
    fid = fx["fixture"]["id"]
    print("Матч:", fx["teams"]["home"]["name"], "-", fx["teams"]["away"]["name"])

    # GitHub Actions үшін: матч алыс болса, бос күтпей шығып кетеміз
    max_wait = float(os.getenv("MAX_WAIT_HOURS", "3.2")) * 3600
    ts = fx["fixture"]["timestamp"]
    if ts - time.time() > max_wait:
        print("Матч әлі алыс, келесі іске қосылуды күтеміз")
        return

    wait_for_kickoff(fx)
    if time.time() - ts < 600:  # матч жаңа басталса ғана хабар жібереміз
        send(f"🔴 Матч басталды!\n{kk_team(fx['teams']['home']['name'])} — {kk_team(fx['teams']['away']['name'])}")

    seen, ht_sent = set(), False
    # Іске қосқан сәтте бұрыннан бар оқиғаларды қайта жазбау үшін (қайта қосылғанда)
    first_run = True

    while True:
        try:
            data = api_get("/fixtures", id=fid)
            if not data:
                time.sleep(POLL_SECONDS)
                continue
            fx = data[0]
            status = fx["fixture"]["status"]["short"]

            for ev in fx.get("events", []):
                k = event_key(ev)
                if k in seen:
                    continue
                seen.add(k)
                if first_run:
                    continue
                msg = format_event(ev, fx)
                if msg:
                    send(msg)
            first_run = False

            if status == "HT" and not ht_sent:
                send(f"⏸ Үзіліс\n📊 {score_line(fx)}")
                ht_sent = True
            if status == "2H":
                ht_sent = False
            if status in ("FT", "AET", "PEN"):
                send(f"🏁 Матч аяқталды\n📊 {score_line(fx)}")
                return
            if status in ("PST", "CANC", "ABD"):
                send("⚠️ Матч өтпеді немесе тоқтатылды")
                return
        except Exception as e:
            print("Қате:", e)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
