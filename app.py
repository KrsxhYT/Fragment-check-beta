from flask import Flask, request, jsonify
import requests, time, re

app = Flask(__name__)

CREDIT = "@Krsxh"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (TelegramCheckerAdvanced; +https://github.com)"
}


def safe_get(url, retries=3, timeout=5):
    for _ in range(retries):
        try:
            return requests.get(url, headers=HEADERS, timeout=timeout)
        except:
            time.sleep(0.3)
    return None


def fragmentcheck(username):
    url = f"https://fragment.com/username/{username}"
    response = safe_get(url)

    if response is None:
        return {"status": "ERROR", "price": None}

    html = response.text

    if response.url.startswith("https://fragment.com/?query="):
        status = "AVAILABLE"
    elif 'tm-status-avail' in html:
        status = "AVAILABLE"
    elif 'tm-status-taken' in html:
        status = "TAKEN"
    else:
        status = "UNKNOWN"

    price = None
    patterns = [
        r'class="tm-section-header-price">([\d\.]+)\s*TON',
        r'>([\d\.]+)\s*TON<\/',
        r'price-value">([\d\.]+)<',
        r'">([\d\.]+)\s*TON<'
    ]

    for p in patterns:
        m = re.search(p, html)
        if m:
            price = m.group(1)
            break

    return {"status": status, "price": price}


def check_username(username):
    start = time.time()
    username = username.lower().replace("@", "").strip()

    tg = safe_get(f"https://t.me/{username}")

    if tg is None:
        return {
            "error": "telegram connection failed",
            "username": username,
            "time": None,
            "credit": CREDIT
        }

    html = tg.text

    exists_patterns = [
        '<i class="tgme_icon_user"></i>',
        'tgme_page_title',
        'data-view="user"'
    ]

    exists = any(p in html for p in exists_patterns)

    if not exists:
        return {
            "username": username,
            "status": "TAKEN",
            "fragment_status": None,
            "fragment_price": None,
            "time": round(time.time() - start, 4),
            "credit": CREDIT
        }

    frag = fragmentcheck(username)

    return {
        "username": username,
        "status": frag["status"],
        "fragment_status": frag["status"],
        "fragment_price": frag["price"],
        "time": round(time.time() - start, 4),
        "credit": CREDIT
    }


@app.route("/api/check", methods=["GET", "POST"])
def api_check():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
    else:
        username = request.args.get("username", "").strip()

    if not username:
        return jsonify({"error": "username missing"}), 400

    return jsonify(check_username(username))


@app.route("/")
def home():
    return jsonify({
        "message": "Ultra Advanced Telegram Username Checker API",
        "usage_example": "/api/check?username=test",
        "credit": CREDIT,
        "developer": "Krsxh"
    })


# ----------------––––––––––
# REQUIRED FOR VERCEL!!!
# ----------------––––––––––
def handler(request, *args, **kwargs):
    return app(request.environ, lambda status, headers: (status, headers))
