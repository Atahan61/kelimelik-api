from fastapi import FastAPI, File, UploadFile
from contextlib import asynccontextmanager
import shutil
import os

# --- BİZİM YENİ GÖZLERİMİZ ---
from tahta_v11_final import tahtayi_oku_final
from el_okuyucu_v2 import eli_oku

# --- BEYİN ---
from solver import motor 

# --- YENİ BAŞLANGIÇ SİSTEMİ (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uygulama başlarken çalışacak kodlar
    print("\n🚀 KELİMELİK BOTU BAŞLATILIYOR...")
    
    if os.path.exists("dictionary.txt"):
        motor.veriyi_yukle("dictionary.txt")
    elif os.path.exists("kelimeler.txt"):
        motor.veriyi_yukle("kelimeler.txt")
    else:
        print("⚠️ UYARI: Sözlük dosyası bulunamadı! (kelimeler.txt veya dictionary.txt)")
    
    yield # Uygulama burada çalışmaya devam eder
    
    # Uygulama kapanırken çalışacak kodlar (Gerekirse buraya eklenir)
    print("🛑 Sistem kapatılıyor...")

# Uygulamayı lifespan ile başlatıyoruz
app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"durum": "Hazır", "versiyon": "v2.1 (Lifespan)"}

def harfi_temizle(ham_harf):
    """ 'd2', 's_el' gibi isimleri 'd', 's' haline getirir. """
    temiz = ""
    if ham_harf == "?" or ham_harf is None:
        return "?"
    
    for karakter in ham_harf:
        if karakter.isalpha() or karakter == "*": 
            temiz += karakter
            
    return temiz.lower()

@app.post("/resim-coz")
async def resim_coz(file: UploadFile = File(...)):
    # 1. Gelen resmi kaydet
    temp_dosya = "temp.jpg"
    with open(temp_dosya, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print(f"\n--- YENİ İSTEK GELDİ: {file.filename} ---")

    # 2. TAHTAYI OKU
    raw_tahta = tahtayi_oku_final(temp_dosya)
    
    # Matrisi temizle
    tahta_matris = []
    for satir in raw_tahta:
        yeni_satir = []
        for hucre in satir:
            if hucre and hucre != "?":
                yeni_satir.append(harfi_temizle(hucre))
            else:
                yeni_satir.append(None)
        tahta_matris.append(yeni_satir)

    # 3. ELİ OKU
    raw_el = eli_oku(temp_dosya)
    el_harfleri = [harfi_temizle(h) for h in raw_el]
    
    print(f"Tahta Okundu. El: {el_harfleri}")

    # 4. SOLVER (ÇÖZÜCÜ) ÇAĞIR
    print("🧠 Solver düşünmeye başladı...")
    bulunanlar = []
    
    # Hata olmaması için kontrol
    try:
        if hasattr(motor, "hamle_bul"):
            bulunanlar = motor.hamle_bul(tahta_matris, el_harfleri)
        else:
            print("HATA: motor.hamle_bul fonksiyonu bulunamadı!")
    except Exception as e:
        print(f"Solver Hatası: {e}")

    # En iyi hamleleri terminale de yazalım
    if bulunanlar:
        print(f"\n🏆 EN İYİ HAMLELER:")
        for i, hamle in enumerate(bulunanlar[:5]):
            print(f"{i+1}. {hamle['kelime'].upper()} ({hamle['puan']} P) -> {hamle['yon']} {hamle['baslangic']}")
    else:
        print("❌ Hiç hamle bulunamadı.")

    # 5. SONUCU DÖNDÜR
    return {
        "el_harfleri": el_harfleri,
        "tahta_durumu": tahta_matris, 
        "onerilen_kelimeler": bulunanlar[:20] 
    }