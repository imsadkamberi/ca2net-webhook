from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = "8857720884:AAFZYZxsy3S16esXqamy1YGCADnb9XjiK7Q"
CHAT_ID = "901764770"


def send_telegram(text):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": text}
  try:
    requests.post(url, json=payload)
  except Exception as e:
    print(f"Error: {e}")


@app.route("/", methods=["GET"])
def home():
  return "Ca2net Bot is running!", 200


# Kemi shtuar ["GET", "POST"] që të mos jep gabim nga shfletuesi
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
  # Nëse hyhet nga shfletuesi (GET)
  if request.method == "GET":
    msg = request.args.get("message", "Testim nga shfletuesi direkt!")
    send_telegram(msg)
    return "Mesazhi u dërgua me sukses në Telegram përmes GET!", 200

  # Nëse vjen nga TradingView (POST)
  data = request.json
  if data and "message" in data:
    send_telegram(data["message"])
    return "OK", 200

  return "Bad Request", 400


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
