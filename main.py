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


def get_gemini_chat_analysis(user_prompt):
  """Pyet Gemini AI për të krijuar një analizë ICT dhe sinjal bazuar në kërkesën e përdoruesit."""
  if not GEMINI_API_KEY:
    return "Mungon Gemini API Key te Render Environment!"

  try:
   model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
        Je një krye-analist i tregjeve Forex dhe Crypto me strategjinë ICT (Inner Circle Trader).
        Përdoruesi të ka kërkuar këtë analizë/aset: "{user_prompt}"
        Jep një analizë të shkurtër profesionale në gjuhën shqipe (max 2-3 fjali) duke përfshirë një strukturë të mundshme ICT (si FVG, Order Block, ose Liquidity Sweep) për këtë aset, dhe përcakto një drejtim (BUY ose SELL) me çmimin aktual të tregut.
        
        Kthe përgjigjen në këtë format të saktë:
        ASTI: [Emri i Asetit, p.sh. XAUUSD]
        DREJTIMI: [BUY ose SELL]
        ENTRY: [Një çmim realist aktual, p.sh. 4170.50]
        ARSYEJA: [Analiza e shkurtër ICT]
        """
    response = model.generate_content(prompt)
    return response.text.strip()
  except Exception as e:
    print(f"Gemini error: {e}")
    return "Nuk munda të përpunoj analizën për momentin. Provoni përsëri."


@app.route("/", methods=["GET"])
def home():
  return "CA2NET Personal ICT AI Assistant Bot is Running!", 200


# Ky është webhook-u që pret mesazhet e tua nga Telegrami
@app.route("/telegram-webhook", methods=["POST"])
def telegram_webhook():
  try:
    data = request.get_json(force=True, silent=True)
    print(f"Mesazhi i ardhur nga Telegrami: {data}")

    if data and "message" in data:
      chat_id = data["message"]["chat"]["id"]
      text = data["message"].get("text", "").strip()

      if text:
        if text.lower() in ["/start", "përshëndetje", "pershendetje"]:
          welcome_msg = """
🤖 <b>Përshëndetje Imsad! Unë jam Asistenti yt Personal ICT & Gemini AI.</b>

Mjafton të më shkruash emrin e çdo aseti (p.sh: <b>xauusd</b>, <b>eurusd</b>, <b>gbpusd</b>, <b>btcusd</b>) ose t'i kërkosh një analizë, dhe unë do të gjeneroj menjëherë një sinjal ICT me:
• 📍 <i>Entry</i>
• 🛑 <i>Stop Loss</i>
• 🎯 <i>Take Profits</i>
• 📋 <i>Copy me 1 klikim!</i>

Shkruaj çfarë aseti dëshiron të analizojmë tani:
"""
          send_telegram(chat_id, welcome_msg)
          return "OK", 200

        # Lajmërojmë përdoruesin se po mendohet
        send_telegram(
            chat_id, "⏳ <i>Duke analizuar tregun përmes strategjisë ICT...</i>"
        )

        # Marrim përgjigjen nga Gemini AI
        ai_response = get_gemini_chat_analysis(text)

        # Përpunojmë tekstin për të nxjerrë të dhënat dhe për t'i llogaritur nivelet
        ticker = "XAUUSD"
        action = "BUY"
        price = 4170.0
        reason = ai_response

        # Përpiqemi të lexojmë përgjigjen e Gemini nëse ka kthyer formatin e kërkuar
        lines = ai_response.split("\n")
        for line in lines:
          if "ASTI:" in line:
            ticker = line.replace("ASTI:", "").strip().upper()
          elif "DREJTIMI:" in line:
            action = line.replace("DREJTIMI:", "").strip().upper()
          elif "ENTRY:" in line:
            try:
              price = float(
                  line.replace("ENTRY:", "")
                  .strip()
                  .replace("$", "")
                  .replace(",", "")
              )
            except:
              pass
          elif "ARSYEJA:" in line:
            reason = line.replace("ARSYEJA:", "").strip()

        # Llogaritja e SL dhe TP sipas llojit të asetit
        if "BTC" in ticker:
          sl_dist = 300.0
          decimals = 2
        elif "XAU" in ticker:
          sl_dist = 6.0
          decimals = 2
        else:
          sl_dist = 0.0020  # 20 pips për forex
          decimals = 4

        if "BUY" in action:
          sl = round(price - sl_dist, decimals)
          risk = abs(price - sl)
          tp1 = round(price + (risk * 2), decimals)
          tp2 = round(price + (risk * 3), decimals)
          icon = "🟢"
        else:
          sl = round(price + sl_dist, decimals)
          risk = abs(sl - price)
          tp1 = round(price - (risk * 2), decimals)
          tp2 = round(price - (risk * 3), decimals)
          icon = "🔴"

        entry = round(price, decimals)

        # Krijimi i mesazhit final me Copy me 1 klik
        final_msg = f"""
🚨 <b>ANALIZA ICT (CA2NET AI)</b> 🚨

📊 <b>Aseti:</b> #{ticker} (1H)
{icon} <b>Veprimi:</b> <b>{action}</b>

👇 <i>Kliko mbi numër për ta bërë Copy:</i>
📍 <b>Entry:</b> <code>{entry}</code>
🛑 <b>Stop Loss:</b> <code>{sl}</code>
🎯 <b>Take Profit 1:</b> <code>{tp1}</code>
🎯 <b>Take Profit 2:</b> <code>{tp2}</code>

🤖 <b>Analiza e Gemini AI:</b>
<i>{reason}</i>

📋 <b>Copy të gjithë rreshtin:</b>
<code>{ticker} {action} {entry} SL {sl} TP1 {tp1} TP2 {tp2}</code>

⚡ <i>By Imsad Kamberi | CA2-NET</i>
"""
        send_telegram(chat_id, final_msg)

    return "OK", 200
  except Exception as e:
    print(f"Webhook error: {e}")
    return f"Error: {e}", 500


if __name__ == "__main__":
  port = int(os.environ.get("PORT", 5000))
  app.run(host="0.0.0.0", port=port)
