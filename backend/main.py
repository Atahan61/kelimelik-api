# main.py (GÜNCELLENMİŞ VERSİYON)
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from tahta_v11_final import tahtayi_oku, eldeki_harfleri_oku  # Fonksiyonları içe aktar
from solver import KelimelikSolver
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Solver'ı başlat (Kelimeler yüklenir)
solver = KelimelikSolver()

# --- YARDIMCI FONKSİYON: Resmi Hazırla ---
async def resmi_isle(file: UploadFile):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

# --- YENİ ENDPOINT 1: Sadece Eldeki Harfleri Oku ---
@app.post("/eli-oku")
async def eli_oku_endpoint(file: UploadFile = File(...)):
    """
    Resmi alır, sadece eldeki harfleri okur ve string olarak döner.
    Örn: "A*BCEŞ"
    """
    try:
        img = await resmi_isle(file)
        # Sadece el okuma fonksiyonunu çağır
        el_harfleri_str = eldeki_harfleri_oku(img)
        return {"durum": "basarili", "el": el_harfleri_str}
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}


# --- GÜNCELLENMİŞ ENDPOINT 2: Çözüm ---
@app.post("/resim-coz")
async def coz(
    file: UploadFile = File(...),
    manuel_el: str = Form(None) # <-- YENİ: İsteğe bağlı manuel el bilgisi
):
    try:
        print("1. Resim alınıyor...")
        img = await resmi_isle(file)

        print("2. Tahta (OCR) okunuyor...")
        tahta_matrisi, _ = tahtayi_oku(img) # Artık tahtayi_oku'dan sadece matrisi alıyoruz

        # --- KRİTİK DEĞİŞİKLİK BURADA ---
        if manuel_el and manuel_el.strip() != "":
             # Eğer Flutter'dan manuel bir el bilgisi geldiyse, OCR yapma, onu kullan.
             print(f"3. Manuel el bilgisi kullanılacak: {manuel_el}")
             el_harfleri = manuel_el.strip()
        else:
             # Manuel bilgi yoksa, eski usul OCR ile kendin bul.
             print("3. Eldeki harfler (OCR) okunuyor...")
             el_harfleri = eldeki_harfleri_oku(img)
             print(f"   OCR Sonucu: {el_harfleri}")
        # --------------------------------

        print("4. Çözücü çalışıyor...")
        en_iyi_hamle, puan = solver.en_iyi_hamleyi_bul(tahta_matrisi, el_harfleri)

        if en_iyi_hamle:
            print(f"5. Çözüm bulundu: {en_iyi_hamle['kelime']} - {puan} Puan")
            return {"durum": "basarili", "hamle": en_iyi_hamle}
        else:
            print("5. Hamle bulunamadı.")
            return {"durum": "hamle_yok"}

    except Exception as e:
        print(f"HATA OLUŞTU: {e}")
        import traceback
        traceback.print_exc()
        return {"durum": "hata", "mesaj": str(e)}

@app.get("/")
def read_root():
    return {"durum": "Hazır", "versiyon": "v3.0 (Manuel Düzeltme)"}