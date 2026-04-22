import sys
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

import warnings
warnings.filterwarnings("ignore")

import logging
import telebot
telebot.logger.setLevel(logging.CRITICAL)

import os
import json
import uuid
import threading
import time
import random # YENİ: Rastgele süreler üretmek için eklendi
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

import gonderici 

# --- AYARLAR VE KURULUM ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("🚨 HATA: .env dosyasında TELEGRAM_BOT_TOKEN veya TELEGRAM_CHAT_ID eksik!")
    sys.exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)
BEKLEYEN_TWEETLER = {}
SAYAC = {"toplam": 0, "cevaplanan": 0, "aktif_zamanlayici": 0}

# --- YARDIMCI FONKSİYONLAR ---
def otonom_mod_kontrol():
    try:
        with open("config/ayarlar.json", "r", encoding="utf-8") as f:
            veri = json.load(f)
            return veri.get("otonom_mod", False)
    except:
        return False

def persona_oku():
    try:
        with open("persona.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return None

def telegram_hareketini_logla(aksiyon_durumu, icerik_ingilizce, tip="TWEET", hedef_url="Yok"):
    log_klasoru = "log_dosyasi"
    if not os.path.exists(log_klasoru):
        os.makedirs(log_klasoru)
    bugun = datetime.now().strftime("%Y-%m-%d")
    zaman_tam = datetime.now().strftime("%H:%M:%S")
    dosya_yolu = os.path.join(log_klasoru, f"{bugun}.txt")
    log_metni = f"[{zaman_tam}] TELEGRAM İŞLEMİ: {aksiyon_durumu}\nİÇERİK TİPİ: {tip}\nHEDEF URL: {hedef_url}\nLYLA'NIN MESAJI (EN): {icerik_ingilizce}\n{'-'*60}\n"
    with open(dosya_yolu, "a", encoding="utf-8") as f:
        f.write(log_metni)

def toplanan_twitleri_oku():
    try:
        with open("toplanan_twitler.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def model_sec():
    mevcut_modeller = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    for model in mevcut_modeller:
        if '1.5-flash' in model: return model
    for model in mevcut_modeller:
        if '1.5' in model: return model
    return mevcut_modeller[0]

def zamanli_gonderici_tetik(metin, tip, hedef_id):
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏳ Süre doldu! Kuyruktaki içerik X'e ateşleniyor...")
    gonderici.x_e_gonder(metin, tip, hedef_id)
    SAYAC["aktif_zamanlayici"] -= 1

# --- TELEGRAM BUTON DİNLEYİCİSİ ---
@bot.callback_query_handler(func=lambda call: True)
def buton_tiklandi(call):
    aksiyon, tweet_id = call.data.split('_')
    tweet_verisi = BEKLEYEN_TWEETLER.pop(tweet_id, None)
    
    if not tweet_verisi:
        bot.answer_callback_query(call.id, "İşlem yapılmış veya süre dolmuş.")
        return

    mesaj_id = call.message.message_id
    icerik_ingilizce = tweet_verisi.get("icerik", "")
    tip = tweet_verisi.get("tip", "TWEET")
    hedef_id = tweet_verisi.get("hedef_id")
    url = f"https://x.com/i/status/{hedef_id}" if tip == "REPLY" else "Otonom Tweet (URL Yok)"

    if aksiyon == "rej":
        bot.edit_message_text(f"❌ REDDEDİLDİ", chat_id=TELEGRAM_CHAT_ID, message_id=mesaj_id)
        telegram_hareketini_logla("REDDEDİLDİ", icerik_ingilizce, tip, url)
        aksiyon_ismi = "Reddedildi"
    elif aksiyon == "now":
        bot.edit_message_text(f"🚀 ONAYLANDI (Şimdi Gönderildi)\n\nGönderilen: {icerik_ingilizce}", chat_id=TELEGRAM_CHAT_ID, message_id=mesaj_id)
        telegram_hareketini_logla("ONAYLANDI (Şimdi)", icerik_ingilizce, tip, url)
        aksiyon_ismi = "Şimdi Gönder"
        gonderici.x_e_gonder(icerik_ingilizce, tip, hedef_id)
    elif aksiyon == "15m":
        bot.edit_message_text(f"⏳ ONAYLANDI (15 Dk Beklemede)\n\nKuyruktaki: {icerik_ingilizce}", chat_id=TELEGRAM_CHAT_ID, message_id=mesaj_id)
        telegram_hareketini_logla("ONAYLANDI (15 Dk)", icerik_ingilizce, tip, url)
        aksiyon_ismi = "15 Dk Bekle"
        SAYAC["aktif_zamanlayici"] += 1
        threading.Timer(900, zamanli_gonderici_tetik, args=[icerik_ingilizce, tip, hedef_id]).start()

    SAYAC["cevaplanan"] += 1
    kalan_mesaj = SAYAC["toplam"] - SAYAC["cevaplanan"]
    print(f"Sistem: Telegram'dan yanıt geldi -> [{aksiyon_ismi}] | Kalan: {kalan_mesaj}")
    if kalan_mesaj <= 0:
        bot.stop_polling()

# --- ANA KARAR MERKEZİ ---
def lyla_karar_merkezi():
    lyla_system_prompt = persona_oku()
    if not lyla_system_prompt:
        print("Sistem: persona.txt bulunamadı!")
        sys.exit(1)

    twitler = toplanan_twitleri_oku()
    if not twitler:
        print("Sistem: Okunacak tweet bulunamadı.")
        sys.exit(1)

    twitler_metni = "\n".join([f"ID: {t['id']} | TEXT: {t['text']}" for t in twitler[:30]])
    
    analiz_istegi = f"""
    Aşağıda X ana sayfamdan toplanan güncel tweetler bulunuyor:
    {twitler_metni}
    GÖREV: Persona'ndaki karakter ve kurallara göre JSON formatında 5 içerik üret.
    """

    print("Sistem: Lyla persona.txt emrine göre içerik hazırlıyor...")
    secili_model = model_sec()
    model = genai.GenerativeModel(model_name=secili_model, system_instruction=lyla_system_prompt)
    
    guvenlik_ayarlari = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
    ]
    
    try:
        response = model.generate_content(analiz_istegi, safety_settings=guvenlik_ayarlari)
        cevap = response.text.strip()
        temiz_json_metni = cevap.replace("```json", "").replace("```", "").strip()
        icerikler = json.loads(temiz_json_metni)
        
        otonom_mu = otonom_mod_kontrol()
        
        if otonom_mu:
            print("\nSistem: 🤖 OTONOM MOD AKTİF. İnsan gibi davranmak için rastgele gecikmeler eklendi.")
            for idx, item in enumerate(icerikler, 1):
                print(f"[{idx}/{len(icerikler)}] Hazırlanıyor: {item['tip']}")
                gonderici.x_e_gonder(item["icerik"], item["tip"], item.get("hedef_id"))
                
                if idx < len(icerikler):
                    # YENİ: 2 dk (120 sn) ile 6 dk (360 sn) arası rastgele bekleme
                    bekleme_suresi = random.randint(120, 360) 
                    print(f"Sistem: Doğallığı bozmamak adına {bekleme_suresi // 60} dk {bekleme_suresi % 60} sn bekleniyor...\n")
                    time.sleep(bekleme_suresi)
            
            print("\n✅ OTONOM GÖNDERİM TAMAMLANDI.")
            
        else:
            SAYAC["toplam"] = len(icerikler)
            SAYAC["cevaplanan"] = 0
            print(f"\nSistem: 👤 ONAY MODU AKTİF. Telegram'a {SAYAC['toplam']} mesaj gönderiliyor...")
            for item in icerikler:
                benzersiz_id = str(uuid.uuid4())[:8] 
                BEKLEYEN_TWEETLER[benzersiz_id] = item
                if item.get("tip") == "REPLY":
                    msg = (f"🎯 YENİ HEDEF (REPLY)\n\n📍 Hedef: {item.get('hedef_metin_tr', 'Yok')}\n\n🤖 Lyla: {item.get('icerik', 'Hata')}\n\n🇹🇷 TR: {item.get('icerik_tr', 'Yok')}")
                else:
                    msg = (f"💡 YENİ FİKİR (OTONOM TWEET)\n\n🤖 Lyla: {item.get('icerik', 'Hata')}\n\n🇹🇷 TR: {item.get('icerik_tr', 'Yok')}")
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton("🚀 Şimdi Gönder", callback_data=f"now_{benzersiz_id}"))
                markup.add(InlineKeyboardButton("⏳ 15 Dk Sonra", callback_data=f"15m_{benzersiz_id}"))
                markup.add(InlineKeyboardButton("❌ Reddet", callback_data=f"rej_{benzersiz_id}"))
                bot.send_message(TELEGRAM_CHAT_ID, msg, reply_markup=markup)
            print("✨ Telegram'a iletildi! Dinleniyor...")
            bot.infinity_polling()
            if SAYAC["aktif_zamanlayici"] > 0:
                while SAYAC["aktif_zamanlayici"] > 0:
                    time.sleep(5)
            print("\n✅ SİSTEM KAPANIYOR.")

    except Exception as e:
        print(f"\n❌ Kritik Hata Oluştu: {e}")
        sys.exit(1) 

if __name__ == "__main__":
    lyla_karar_merkezi()