import sys
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True) 

import json
import time
import schedule
import scraper
import subprocess

suanki_main_sureci = None 

def ayarlari_oku():
    try:
        with open("config/ayarlar.json", "r", encoding="utf-8") as f:
            veri = json.load(f)
            return veri.get("calisma_saatleri", [])
    except Exception as e:
        print(f"HATA: ayarlar.json okunamadı ({e})")
        return []

def gorev_baslat():
    global suanki_main_sureci
    
    MAKSIMUM_DENEME = 3
    deneme = 1
    
    while deneme <= MAKSIMUM_DENEME:
        print("\n" + "="*50)
        print(f"[{time.strftime('%H:%M:%S')}] ZAMANLANMIŞ GÖREV TETİKLENDİ (Deneme: {deneme}/{MAKSIMUM_DENEME})")
        print("="*50)
        
        # Varsa eski süreci temizle
        if suanki_main_sureci is not None and suanki_main_sureci.poll() is None:
            print("Sistem: Önceki saatten kalan oturum kapatılıyor...")
            suanki_main_sureci.terminate()
            time.sleep(2) 
            
        # 1. Twitter'ı Tara (Yeni taze tweetler topla)
        scraper.twitter_tara()
        
        # 2. Karar Merkezini (main.py) Başlat
        print("\nSistem: Lyla Karar Merkezi (main.py) başlatılıyor...")
        suanki_main_sureci = subprocess.Popen(
            [sys.executable, "main.py"], 
            stdout=sys.stdout, 
            stderr=sys.stderr
        )
        
        # 3. KONTROL NOKTASI: main.py çöktü mü diye 20 saniye gözlemle
        # (Gemini'nin filtreye takılıp çökmesi genelde ilk 10 saniyede olur)
        crashtimi = False
        print("Sistem: Lyla'nın durumu kontrol ediliyor...")
        for _ in range(20):
            time.sleep(1)
            # poll() None dönmezse süreç kapanmış demektir
            if suanki_main_sureci.poll() is not None: 
                if suanki_main_sureci.returncode != 0: # 0 değilse hata ile kapanmıştır
                    crashtimi = True
                break
                
        # 4. KARAR
        if crashtimi:
            print(f"🚨 DİKKAT: main.py çöktü (Muhtemelen yasaklı içeriğe takıldı).")
            if deneme < MAKSIMUM_DENEME:
                print("Sistem: Taze bir akış yakalamak için 1 dakika bekleniyor ve BAŞA DÖNÜLÜYOR...\n")
                time.sleep(60) # Akışın yenilenmesi için 1 dakika bekle
                deneme += 1
            else:
                print("❌ MAKSİMUM DENEME SINIRINA ULAŞILDI. Bu saatlik görev pas geçiliyor.")
                break # Döngüden çık, pes et
        else:
            print("✅ BAŞARILI: Görev Lyla'ya devredildi. Telegram'da onay bekleniyor...")
            break # Hata yok, döngüden çık ve bir sonraki saate kadar bekle


def main():
    saatler = ayarlari_oku()
    if not saatler:
        print("Hata: Ayarlanmış saat bulunamadı!")
        return
        
    print("\n🌟 LYLA OTOMASYON MERKEZİ AKTİF 🌟")
    print("Kurulu Saatler:")
    for saat in saatler:
        print(f" -> {saat}")
        schedule.every().day.at(saat).do(gorev_baslat)
        
    print("\nArka planda bekleniyor...")
    
    while True:
        schedule.run_pending()
        time.sleep(10)

if __name__ == "__main__":
    main()