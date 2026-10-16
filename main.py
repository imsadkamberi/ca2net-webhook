import os
from flask import Flask, request
import google.generativeai as genai
import requests

app = Flask(__name__)

# ==========================================
# KONFIGURIMET E TUA
# ==========================================
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = "901764770"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Konfigurimi i Gemini AI
if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)


def send_telegram(text):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
  try:
    res = requests.post(url, json=payload)
    print(f"Telegram pergjigje: {res.status_code} - {res.text}")
  except Exception as e:
    print(f"Gabim: {e}")


def get_gemini_ict_analysis(
    ticker, timeframe, action, entry, sl, tp1, tp2, note
):
  if not GEMINI_API_KEY:
    return (
        f"Konfluence e bazuar ne strukturen {timeframe} ICT ({note})."
        " Menaxhoni riskun 1-2%."
    )

  try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"""
        Je nje analist profesionist Forex me strategjine ICT (Inner Circle Trader).
        Analizo shkurtimisht ne gjuhen shqipe (maksimumi 2 fjali te qarta) kete sinjal:
        Aseti: {ticker} | Timeframe: {timeframe} | Drejtimi: {action}
        Entry: {entry} | SL: {sl} | TP1: {tp1} | TP2: {tp2}
        Arsyeja teknike nga TradingView: {note}
        Mos perserit numrat, vetem jep konfirmimin e struktures ICT (Liquidity Sweep, FVG, Order Block, Displacement).
        """
    response = model.generate_content(prompt)
    return response.text.strip()
  except Exception as e:
    print(f"Gemini error: {e}")
    return f"Set-up i konfirmuar sipas {note} ne {timeframe}."


@app.route("/", methods=["GET"])
def home():
  return "CA2NET ICT + Gemini AI Bot is Running!", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
  # Testim i shpejte nga shfletuesi
  if request.method == "GET":
    test_msg = """
🚨 <b>SINJAL FOREX ICT (CA2NET AI)</b> 🚨

📊 <b>Aseti:</b> XAUUSD (1H)
📈 <b>Drejtimi:</b> <b>BUY LIMIT</b>

👇 <i>Kliko mbi çmim për ta bërë Copy:</i>
📍 <b>Entry:</b> <code>4150.00</code>
🛑 <b>Stop Loss:</b> <code>4135.00</code>
🎯 <b>TP 1 (1:2):</b> <code>4180.00</code>
🎯 <b>TP 2 (1:3):</b> <code>4205.00</code>

🤖 <b>Analiza Gemini ICT:</b>
<i>Çmimi ka pastruar Sell-Side Liquidity dhe po rikthehet në 1H Bullish FVG. Pritet reagim impulsiv drejt Buy-Side Liquidity.</i>

📋 <b>Kopjo të gjithë sinjalin me 1 klik:</b>
<code>XAUUSD BUY 4150.00 SL 4135.00 TP1 4180.00 TP2 4205.00</code>

⚡ <i>Powered by CA2-NET & By Imsad Kamberi</i>
"""
    send_telegram(test_msg)
    return "Testi me Copy-Click u dergua ne Telegram!", 200

  # Kur vjen sinjali nga TradingView (POST)
  try:
    data = request.get_json(force=True, silent=True)
    if data and isinstance(data, dict):
      ticker = data.get("ticker", "XAUUSD")
      tf = data.get("tf", "1H")
      action = data.get("action", "BUY").upper()
      price = float(data.get("price", 0))
      note = data.get("note", "1H FVG + Liquidity Sweep")

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
      ai_analysis = get_gemini_ict_analysis(
          ticker, tf, action, entry, sl, tp1, tp2, note
      )

      msg = f"""
🚨 <b>SINJAL FOREX ICT (CA2NET AI)</b> 🚨

📊 <b>Aseti:</b> #{ticker} ({tf})
{icon} <b>Veprimi:</b> <b>{action}</b>

👇 <i>Kliko mbi numër për ta bërë Copy:</i>
📍 <b>Entry:</b> <code>{entry}</code>
🛑 <b>Stop Loss:</b> <code>{sl}</code>
🎯 <b>Take Profit 1:</b> <code>{tp1}</code>
🎯 <b>Take Profit 2:</b> <code>{tp2}</code>

🤖 <b>Analiza Gemini AI (ICT):</b>
<i>{ai_analysis}</i>

📋 <b>Copy të gjithë rreshtin:</b>
<code>{ticker} {action} {entry} SL {sl} TP1 {tp1} TP2 {tp2}</code>

⚡ <i>By Imsad Kamberi | CA2-NET</i>
"""
      send_telegram(msg)
      return "OK", 200
    else:
      # Nese nga TradingView vjen tekst i thjeshte pa JSON (psh: "XAUUSD BUY 4171.20")
      raw_text = request.data.decode("utf-8").strip()
      send_telegram(
          "🚨 <b>SINJAL NGA TRADINGVIEW (CA2NET)</b> 🚨\n\n👇 <i>Kliko për"
          f" Copy:</i>\n<code>{raw_text}</code>\n\n⚡ <i>By Imsad Kamberi</i>"
      )
      return "OK Raw", 200

  except Exception as e:
    print(f"Webhook error: {e}")
    return f"Error: {e}", 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
