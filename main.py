import os
from flask import Flask, request
import google.generativeai as genai
import requests

app = Flask(__name__)

# ==========================================
# KONFIGURIMET E TUA (Lexohen nga Render Environment)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Konfigurimi i Gemini AI
if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)


def send_telegram(chat_id, text):
  if not TELEGRAM_TOKEN:
    print("Gabim: TELEGRAM_TOKEN mungon!")
    return
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
  try:
    res = requests.post(url, json=payload)
    print(f"Telegram përgjigje: {res.status_code} - {res.text}")
  except Exception as e:
    print(f"Gabim gjatë dërgimit në Telegram: {e}")


def get_gemini_conversational_response(user_prompt):
  """Gjeneron një përgjigje natyrale, të ngrohtë dhe profesionale si asistent personal."""
  if not GEMINI_API_KEY:
    return "Mungon Gemini API Key te Render Environment!"

  try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
        Ti je një bashkëpunëtor personal i zgjuar, i ngrohtë, angazhues dhe instruktor profesionist për Imsad Kamberi. 
        Përdoruesi të flet në Telegram për tregje, analiza (ICT/Forex/Crypto), teknologji, apo çfarë t'i duhet.
        Përgjigju në gjuhën shqipe në mënyrë natyrale, të pasur, të strukturuar bukur (përdor emoji dhe formatim HTML si <b>, <i>, etj., ku duhet), duke i dhënë ndihmë praktike, profesionale dhe miqësore, fiks si një asistent i dedikuar AI.
        
        Mesazhi i përdoruesi: "{user_prompt}"
        """
    response = model.generate_content(prompt)
    return response.text.strip()
  except Exception as e:
    print(f"Gemini error: {e}")
    return "Më fal, pata një vështirësi të vogël për t'u lidhur. Provojeni përsëri!"


@app.route("/", methods=["GET"])
def home():
  return "CA2NET Conversational AI Assistant is Running!", 200


@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
  try:
    data = request.get_json(force=True, silent=True)
    if data and "message" in data:
      chat_id = data["message"]["chat"]["id"]
      text = data["message"].get("text", "").strip()

      if text:
        # Përgjigjemi në mënyrë bisedore me AI
        ai_response = get_gemini_conversational_response(text)
        send_telegram(chat_id, ai_response)

    return "OK", 200
  except Exception as e:
    print(f"Webhook error: {e}")
    return f"Error: {e}", 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
