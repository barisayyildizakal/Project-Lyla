import os
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
AUTH_TOKEN = os.getenv("X_AUTH_TOKEN")
CT0 = os.getenv("X_CT0")

def x_e_gonder(metin, tip="TWEET", hedef_id=None):
    """Playwright (Sanal İnsan) kullanarak X.com'a gizlice bağlanır ve gönderiyi atar."""
    if not AUTH_TOKEN or not CT0:
        print("🚨 HATA: .env dosyasında çerezler (AUTH_TOKEN/CT0) eksik!")
        return False

    print(f"\nSistem: Lyla X'in ön kapısından (Web) sızıyor... ({tip} ateşleniyor) 🚀")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        context = browser.new_context()
        context.add_cookies([
            {"name": "auth_token", "value": AUTH_TOKEN, "domain": ".x.com", "path": "/"},
            {"name": "ct0", "value": CT0, "domain": ".x.com", "path": "/"}
        ])
        page = context.new_page()

        try:
            if tip == "REPLY" and hedef_id:
                page.goto(f"https://x.com/i/status/{hedef_id}")
                
                kutucuk = page.locator("[data-testid='tweetTextarea_0']").first
                kutucuk.wait_for(timeout=15000)
                kutucuk.click()
                
                # ÇÖZÜM: Metni doldur ve X'i uyandırmak için boşluk bırak
                kutucuk.fill(metin)
                page.keyboard.press("Space")
                
                time.sleep(2) # Butonun aktif olması için kısa bir süre tanı
                page.locator("[data-testid='tweetButtonInline']").first.click()
                
            else:
                page.goto("https://x.com/compose/tweet")
                
                kutucuk = page.locator("[data-testid='tweetTextarea_0']").first
                kutucuk.wait_for(timeout=15000)
                kutucuk.click()
                
                # ÇÖZÜM: Metni doldur ve X'i uyandırmak için boşluk bırak
                kutucuk.fill(metin)
                page.keyboard.press("Space")
                
                time.sleep(2)
                page.locator("[data-testid='tweetButton']").first.click()

            time.sleep(4) 
            print("✅ BAŞARILI: Lyla gönderiyi Playwright ile başarıyla postaladı!")
            return True
            
        except Exception as e:
            # Hata mesajını daha anlaşılır hale getirdik
            print(f"❌ GÖNDERİM BAŞARISIZ: Hedef yanıtları kapatmış olabilir veya buton pasif. (Hata pas geçiliyor)")
            return False
        finally:
            browser.close()