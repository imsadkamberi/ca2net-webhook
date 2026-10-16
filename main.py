import os
from flask import Flask, request
import google.generativeai as genai
import requests

app = Flask(__name__)

# ==========================================
# KONFIGURIMET E TUA (Lexohen nga Render Environment)
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = "901764770"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Konfigurimi i Gemini AI
if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)


def send_telegram(text):
  if not TELEGRAM_TOKEN:
    print("Gabim: TELEGRAM_TOKEN mungon!")
    return
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
  try:
    res = requests.post(url, json=payload)
    print(f"Telegram përgjigje: {res.status_code} - {res.text}")
  except Exception as e:
    print(f"Gabim gjatë dërgimit në Telegram: {e}")


def analyze_and_filter_ict(ticker, timeframe, action, price, note):
  """Kërkon nga Gemini të analizojë nëse ky set-up është i vlefshëm ICT.

  Nëse po, kthen detajet; nëse jo, e refuzon që të mos dërgojë sinjale kot.
  """
  if not GEMINI_API_KEY:
    return True, f"Set-up i pranuar pa filtrim AI (Mungon API Key): {note}"

  try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
        Je një krye-analist i tregjeve Forex dhe specialist i strategjisë ICT (Inner Circle Trader).
        Vlerëso këtë sinjal të ardhur nga TradingView:
        - Aseti: {ticker} ({timeframe})
        - Veprimi: {action}
        - Çmimi aktual: {price}
        - Shënimi teknik: {note}

        A ka ky set-up konfluencë të mjaftueshme ICT (p.sh. FVG, Order Block, ose Liquidity Sweep) për të marrë një trade me probabilitet të lartë tani?
        Përgjigju I PARI fjalën "PO" ose "JO", dhe më pas jep një arsyetim profesional prej maksimalisht 2 fjalish në gjuhën shqipe.
        Format i kërkuar:
        VENDIMI: [PO ose JO]
        ARSYEJA: [Arsyetimi yt]
        """
    response = model.generate_content(prompt)
    text = response.text.strip()

    print(f"Gemini Filter Response:\n{text}")

    if "VENDIMI: PO" in text.upper():
      reason = text.split("ARSYEJA:")[-1].strip()
      return True, reason
    else:
      return False, "Set-up u refuzua nga filtri i Gemini (Nuk u dërgua në Telegram)."
  except Exception as e:
    print(f"Gemini filter error: {e}")
    return True, f"Kaloi pa filtruar për shkak të gabimit të AI: {note}"


@app.route("/", methods=["GET"])
def home():
  return "CA2NET ICT + Gemini AI Filtered Bot is Running!", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
  # Testim nga shfletuesi
  if request.method == "GET":
    send_telegram(
        "🚨 <b>TEST BOTI (CA2NET)</b> 🚨\nFiltri i Gemini AI dhe lidhja me"
        " Telegram funksionojnë përkryer!"
    )
    return "Testi u dërgua me sukses në Telegram!", 200

  try:
    data = request.get_json(force=True, silent=True)
    if data and isinstance(data, dict):
      ticker = data.get("ticker", "XAUUSD")
      tf = data.get("tf", "1H")
      action = data.get("action", "BUY").upper()
      price = float(data.get("price", 0))
      note = data.get("note", "1H FVG + Liquidity Sweep")

      # 1. Kërkojmë nga Gemini të filtrojë sinjalin (Nuk dërgon sinjale kot)
      is_valid, ai_comment = analyze_and_filter_ict(
          ticker, tf, action, price, note
      )

      # NËSE GEMINI THOTË "JO", BOTI NUK DËRGON GJË DHE MBYLLET
      if not is_valid:
        print(f"Sinjali u bllokua nga Gemini: {ai_comment}")
        return "Sinjali u refuzua nga AI (Nuk u dërgua)", 200

      # 2. Nëse Gemini thotë "PO", llogarisim nivelet dhe i dërgojmë në Telegram
      sl_dist = float(data.get("sl_dist", 6.0))

      if "BUY" in action:
        sl = round(float(data.get("sl", price - sl_dist)), 2)
        risk = abs(price - sl)
        tp1 = round(float(data.get("tp1", price + (risk * 2))), 2)
        tp2 = round(float(data.get("tp2", price + (risk * 3))), 2)
        icon = "🟢"
      else:
        sl = round(float(data.get("sl", price + sl_dist)), 2)
        risk = abs(sl - price)
        tp1 = round(float(data.get("tp1", price - (risk * 2))), 2)
        tp2 = round(float(data.get("tp2", price - (risk * 3))), 2)
        icon = "🔴"

      entry = round(price, 2)

      msg = f"""
🚨 <b>SINJAL ICT I KONFIRMUAR NGA AI</b> 🚨

📊 <b>Aseti:</b> #{ticker} ({tf})
{icon} <b>Veprimi:</b> <b>{action}</b>

👇 <i>Kliko mbi numër për ta bërë Copy:</i>
📍 <b>Entry:</b> <code>{entry}</code>
🛑 <b>Stop Loss:</b> <code>{sl}</code>
🎯 <b>Take Profit 1:</b> <code>{tp1}</code>
🎯 <b>Take Profit 2:</b> <code>{tp2}</code>

🤖 <b>Analiza e Konfirmimit (ICT):</b>
<i>{ai_comment}</i>

📋 <b>Copy të gjithë rreshtin:</b>
<code>{ticker} {action} {entry} SL {sl} TP1 {tp1} TP2 {tp2}</code>

⚡ <i>By Imsad Kamberi | CA2-NET</i>
"""
      send_telegram(msg)
      return "Sinjali u filtrua, u konfirmua dhe u dërgua!", 200
    else:
      raw_text = request.data.decode("utf-8").strip()
      send_telegram(
          f"🚨 <b>SINJAL NGA TRADINGVIEW:</b>\n<code>{raw_text}</code>"
      )
      return "OK Raw", 200

  except Exception as e:
    print(f"Webhook error: {e}")
    return f"Error: {e}", 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
