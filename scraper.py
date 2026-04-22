import sys
sys.stdout.reconfigure(line_buffering=True) # Canlı log aktarımı için

import os
import time
import json
import random
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
CT0 = os.getenv("X_CT0")

def twitter_tara():
    toplanan_twitler = {}
    
    if not AUTH_TOKEN or not CT0:
        print("🚨 HATA: .env dosyasında çerezler eksik!")
        return

    print("Sistem: Tarayıcı başlatılıyor...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        context.add_cookies([
            {"name": "auth_token", "value": AUTH_TOKEN, "domain": ".x.com", "path": "/"},
            {"name": "ct0", "value": CT0, "domain": ".x.com", "path": "/"}
        ])
        page = context.new_page()
        
        try:
            page.goto("https://x.com/home")
            time.sleep(6)
            
            if "login" in page.url:
                print("🚨 Hata: Çerezler geçersiz! Lütfen güncelleyin.")
                return
                
            toplam_dongu = random.randint(20, 32)
            print(f"Sistem: Giriş BAŞARILI! Toplam {toplam_dongu} kaydırma yapılacak.")
            
            for i in range(1, toplam_dongu + 1):
                tweet_elementleri = page.locator("article").all()
                for element in tweet_elementleri:
                    try:
                        metin = element.inner_text()
                        if metin and len(metin) > 10 and "Ad" not in metin:
                            temiz_metin = metin.replace("\n", " | ")
                            link_elementi = element.locator('a[href*="/status/"]').first
                            href = link_elementi.get_attribute("href")
                            
                            if href:
                                tweet_id = href.split("/")[-1]
                                if tweet_id not in toplanan_twitler:
                                    toplanan_twitler[tweet_id] = {
                                        "id": tweet_id,
                                        "url": "https://x.com" + href,
                                        "text": temiz_metin
                                    }
                    except:
                        continue
                
                kaydirma_miktari = random.randint(750, 1100)
                page.evaluate(f"window.scrollBy(0, {kaydirma_miktari})")
                
                bekleme = random.randint(7, 19)
                print(f"Döngü {i}/{toplam_dongu} bitti. {bekleme} sn bekleme...")
                time.sleep(bekleme)

            twit_listesi = list(toplanan_twitler.values())
            with open("toplanan_twitler.json", "w", encoding="utf-8") as f:
                json.dump(twit_listesi, f, ensure_ascii=False, indent=4)
                
            print(f"Sistem: Otonom tarama bitti! Ara tabloya {len(twit_listesi)} yeni tweet yazıldı.")

        except Exception as e:
            print(f"Tarama sırasında hata oluştu: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    twitter_tara()