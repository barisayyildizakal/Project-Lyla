import tkinter as tk
from tkinter import scrolledtext
import json
import subprocess
import threading
import sys
import os

# Arka planda çalışan otomasyon sürecini tutacağımız değişken
process = None

def ayari_guncelle(otonom_mu):
    """Tıklanan butona göre ayarlar.json dosyasını günceller."""
    dosya_yolu = "config/ayarlar.json"
    
    # Klasör yoksa hata vermemesi için basit bir kontrol
    if not os.path.exists("config"):
        os.makedirs("config")

    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            ayarlar = json.load(f)
    except:
        # Dosya okunamazsa varsayılan ayarları oluştur
        ayarlar = {"calisma_saatleri": ["09:30", "13:15", "17:48", "20:20", "00:06"]}
        
    ayarlar["otonom_mod"] = otonom_mu
    
    with open(dosya_yolu, "w", encoding="utf-8") as f:
        json.dump(ayarlar, f, indent=4)

def log_yaz(mesaj):
    """Terminal çıktılarını arayüzdeki siyah ekrana yansıtır."""
    log_ekrani.config(state=tk.NORMAL)
    log_ekrani.insert(tk.END, mesaj + "\n")
    log_ekrani.see(tk.END) # Her zaman en alta kaydır
    log_ekrani.config(state=tk.DISABLED)

def sistemi_baslat(otonom_mu):
    global process
    
    # Önce JSON ayarını güncelle
    ayari_guncelle(otonom_mu)
    
    mod_isim = "🤖 OTONOM" if otonom_mu else "👤 MANUEL (ONAYLI)"
    log_yaz(f"\n{'='*50}")
    log_yaz(f">>> SİSTEM {mod_isim} MODDA BAŞLATILIYOR <<<")
    log_yaz(f"{'='*50}\n")
    
    # Arayüzü Güncelle (Başlat butonlarını gizle, Durdur'u göster)
    btn_otonom.pack_forget()
    btn_manuel.pack_forget()
    btn_durdur.pack(pady=15)
    durum_etiketi.config(text=f"Durum: AÇIK VE DİNLEMEDE ({mod_isim})", fg="#00FF00")
    
    def run_script():
        global process
        # Otomasyon dosyasını arka planda çalıştır
        process = subprocess.Popen(
            [sys.executable, "otomasyon.py"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            encoding='utf-8'
        )
        
        # Çıktıları anlık olarak arayüze aktar
        for line in iter(process.stdout.readline, ''):
            if line:
                log_yaz(line.strip())
            else:
                break
            
    # Arayüzün donmaması için işlemi ayrı bir thread'de (paralelde) başlat
    threading.Thread(target=run_script, daemon=True).start()

def sistemi_durdur():
    global process
    if process:
        process.terminate()
        process = None
    
    log_yaz("\n>>> SİSTEM DURDURULDU <<<\n")
    durum_etiketi.config(text="Durum: KAPALI", fg="#ff4c4c")
    
    # Butonları eski haline getir
    btn_durdur.pack_forget()
    btn_otonom.pack(pady=5)
    btn_manuel.pack(pady=5)

# --- GUI (Arayüz) TASARIMI ---
root = tk.Tk()
root.title("Lyla X Otomasyonu")
root.geometry("650x550")
root.configure(bg="#1e1e1e") # Koyu arka plan

# Başlık
baslik = tk.Label(root, text="Lyla Otomasyon Merkezi", font=("Segoe UI", 18, "bold"), bg="#1e1e1e", fg="white")
baslik.pack(pady=10)

# Durum Bilgisi
durum_etiketi = tk.Label(root, text="Durum: KAPALI", font=("Segoe UI", 12, "bold"), bg="#1e1e1e", fg="#ff4c4c")
durum_etiketi.pack(pady=5)

# Butonlar
btn_otonom = tk.Button(root, text="🤖 OTONOM BAŞLAT (Full Oto)", font=("Segoe UI", 12, "bold"), bg="#8a2be2", fg="white", width=35, height=2, relief="flat", cursor="hand2", command=lambda: sistemi_baslat(True))
btn_otonom.pack(pady=5)

btn_manuel = tk.Button(root, text="👤 MANUEL BAŞLAT (Telegram Onaylı)", font=("Segoe UI", 12, "bold"), bg="#008cba", fg="white", width=35, height=2, relief="flat", cursor="hand2", command=lambda: sistemi_baslat(False))
btn_manuel.pack(pady=5)

btn_durdur = tk.Button(root, text="SİSTEMİ DURDUR", font=("Segoe UI", 12, "bold"), bg="#ff4c4c", fg="white", width=35, height=2, relief="flat", cursor="hand2", command=sistemi_durdur)
# Durdur butonu başlangıçta gizli

# Log Ekranı (Matrix stili)
log_ekrani = scrolledtext.ScrolledText(root, bg="black", fg="#00FF00", font=("Consolas", 10), width=80, height=20, state=tk.DISABLED)
log_ekrani.pack(pady=15, padx=10)

root.mainloop()