from flask import Flask, request
import requests

app = Flask(__name__)

# Konfigurimet e tua
TELEGRAM_TOKEN = "8857720884:AAFZYZxsy3S16esXqamy1YGCADnb9XjiK7Q"
CHAT_ID = "901764770"  # Vendosni ID-në tuaj numerike këtu


def send_telegram(text):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload)
  except Exception as e:
    print(f"Error: {e}")


@app.route("/", methods=["GET"])
def home():
  return "CA2NET Bot is running!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
  data = request.json
  if data:
    msg = data.get("message", "Sinjal i ri nga TradingView!")
    send_telegram(msg)
    return "OK", 200
  return "No data", 400


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
