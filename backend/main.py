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
    
    # Ekranın alt %40'ını garanti olarak al
    y_bas = int(h * 0.60)
    alt_kisim = img[y_bas:h, 0:w]
    
    # Sarı/Ahşap renk filtresi
    alt_sinir = np.array([9, 75, 0])
    ust_sinir = np.array([179, 255, 252])

    hsv = cv2.cvtColor(alt_kisim, cv2.COLOR_BGR2HSV)
    maske = cv2.inRange(hsv, alt_sinir, ust_sinir)

    # --- TOPLU LAZER KESİM ---
    # Taşları tek tek ezmek yerine, taşların olduğu YATAY ŞERİDİ buluyoruz
    coords = cv2.findNonZero(maske)
    if coords is None:
        return ""

    x, y, w_box, h_box = cv2.boundingRect(coords)

    # Şeridi kes (Bu sayede butonlar ve siyah çubuklar çöpe gider, taşlar kare kalır!)
    rack_strip = alt_kisim[y:y+h_box, 0:w]
    sh, sw, _ = rack_strip.shape
    slot_w = sw / 7.0 

    okunan_harfler = ""
    tr_harita = {"oz": "ö", "ch": "ç", "sh": "ş", "ue": "ü", "gh": "ğ", "iu": "ı", "i": "i"}

    for i in range(7):
        x1 = int(i * slot_w)
        x2 = int((i + 1) * slot_w)
        margin = int(slot_w * 0.08) # Taşların kenarındaki ince boşluğu atla
        
        hucre = rack_strip[0:sh, x1+margin:x2-margin]
        if hucre.size == 0: continue

        # Bu hücrede cidden sarı taş var mı? (Belki boşluktur)
        h_hsv = cv2.cvtColor(hucre, cv2.COLOR_BGR2HSV)
        h_maske = cv2.inRange(h_hsv, alt_sinir, ust_sinir)
        
        if cv2.countNonZero(h_maske) > (hucre.size * 0.15):
            # Taş var, harfi oku! Oran bozulmadığı için şak diye tanıyacak.
            harf, skor = en_iyi_eslesmeyi_bul(hucre, referanslar)
            
            if harf != "?":
                temiz_harf = harf.split("_")[0] if "_" in harf else harf
                final_harf = tr_harita.get(temiz_harf, temiz_harf)
                okunan_harfler += final_harf.upper()
            else:
                # Sapsarı bir taş var ama harf yok (Gerçek JOKER!)
                okunan_harfler += "*"
    
    return okunan_harfler

@app.post("/resim-coz")
async def coz(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        tahta_matrisi, _ = tahtayi_oku(img)
        el_harfleri_str = eldeki_harfleri_oku_guvenli(img)

        # Hata kontrolleri
        if not tahta_matrisi or len(tahta_matrisi) == 0:
            return {"durum": "hamle_yok", "onerilen_kelimeler": [], "el_harfleri": []}

        if not el_harfleri_str:
            return {"durum": "hamle_yok", "onerilen_kelimeler": [], "el_harfleri": []}

        # Çözücü
        el_temiz = el_harfleri_str.lower().replace(" ", "")
        hamleler = motor.hamle_bul(tahta_matrisi, el_temiz)

        if not hamleler:
            return {"durum": "hamle_yok", "onerilen_kelimeler": [], "el_harfleri": list(el_harfleri_str)}

        return {"durum": "basarili", "onerilen_kelimeler": hamleler[:30], "el_harfleri": list(el_harfleri_str)}

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

@app.get("/")
def read_root():
    return {"durum": "Hazır"}