from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

from tahta_v11_final import tahtayi_oku, referanslari_yukle, en_iyi_eslesmeyi_bul
from solver import motor 

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def eldeki_harfleri_oku_guvenli(img):
    referanslar = referanslari_yukle()
    if not referanslar: return ""

    h, w, _ = img.shape
    y_bas = int(h * 0.75)
    el_resmi = img[y_bas:h, 0:w]
    eh, ew, _ = el_resmi.shape
    slot_w = ew / 7.0 

    okunan_harfler = ""
    tr_harita = {"oz": "ö", "ch": "ç", "sh": "ş", "ue": "ü", "gh": "ğ", "iu": "ı", "i": "i", "joker": "*", "yildiz": "*"}

    alt_sinir = np.array([9, 75, 0])
    ust_sinir = np.array([179, 255, 252])

    for i in range(7):
        x1 = int(i * slot_w)
        x2 = int((i + 1) * slot_w)
        margin = int(slot_w * 0.1)
        hucre = el_resmi[0:eh, x1+margin:x2-margin]
        
        if hucre.size == 0: continue

        hsv = cv2.cvtColor(hucre, cv2.COLOR_BGR2HSV)
        maske = cv2.inRange(hsv, alt_sinir, ust_sinir)
        
        if cv2.countNonZero(maske) > (hucre.size * 0.05):
            harf, skor = en_iyi_eslesmeyi_bul(hucre, referanslar)
            if harf != "?":
                temiz_harf = harf.split("_")[0] if "_" in harf else harf
                final_harf = tr_harita.get(temiz_harf, temiz_harf)
                okunan_harfler += final_harf.upper()
    
    return okunan_harfler

@app.post("/resim-coz")
async def coz(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        tahta_matrisi, _ = tahtayi_oku(img)
        
        # 1. HATA İHTİMALİ: Tahta Okunamadı
        if not tahta_matrisi or len(tahta_matrisi) == 0:
            return {"durum": "basarili", "onerilen_kelimeler": [{"kelime": "TAHTABOS", "puan": 0, "baslangic": [7,7], "yon": "Yatay", "jokerler": []}], "el_harfleri": ["H","A","T","A"]}

        el_harfleri_str = eldeki_harfleri_oku_guvenli(img)

        # 2. HATA İHTİMALİ: El Okunamadı
        if not el_harfleri_str:
            return {"durum": "basarili", "onerilen_kelimeler": [{"kelime": "ELBOMBOS", "puan": 0, "baslangic": [7,7], "yon": "Yatay", "jokerler": []}], "el_harfleri": ["H","A","T","A"]}

        el_temiz = el_harfleri_str.lower().replace(" ", "")
        hamleler = motor.hamle_bul(tahta_matrisi, el_temiz)

        # 3. HATA İHTİMALİ: Çözücü Kelime Bulamadı
        if not hamleler:
            return {"durum": "basarili", "onerilen_kelimeler": [{"kelime": "HAMLEYOK", "puan": 0, "baslangic": [7,7], "yon": "Yatay", "jokerler": []}], "el_harfleri": list(el_harfleri_str)}

        return {"durum": "basarili", "onerilen_kelimeler": hamleler[:30], "el_harfleri": list(el_harfleri_str)}

    except Exception as e:
        # 4. HATA İHTİMALİ: Python Kodu Çöktü
        return {"durum": "basarili", "onerilen_kelimeler": [{"kelime": "COKTU", "puan": 999, "baslangic": [7,7], "yon": "Yatay", "jokerler": []}], "el_harfleri": ["H","A","T","A"]}

@app.get("/")
def read_root():
    return {"durum": "Hazır"}