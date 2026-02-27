from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

from tahta_v11_final import tahtayi_oku, eldeki_harfleri_oku
from solver import motor 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/resim-coz")
async def coz(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        tahta_matrisi, _ = tahtayi_oku(img)
        el_harfleri_str = eldeki_harfleri_oku(img)

        # 1. HATA İHTİMALİ: Sözlük Yüklenmedi (0 kelime var)
        if motor.kelime_sayisi == 0:
            return {
                "durum": "basarili", 
                "onerilen_kelimeler": [{"kelime": "SOZLUKBOS", "puan": 0, "baslangic": [7,7], "yon": "Yatay"}], 
                "el_harfleri": ["H","A","T","A"]
            }

        # 2. HATA İHTİMALİ: Harfler Okunamadı
        if not el_harfleri_str or len(el_harfleri_str.strip()) == 0:
            return {
                "durum": "basarili", 
                "onerilen_kelimeler": [{"kelime": "ELBOMBOS", "puan": 0, "baslangic": [7,7], "yon": "Yatay"}], 
                "el_harfleri": ["H","A","T","A"]
            }

        # 3. ÇÖZÜCÜ ÇALIŞIYOR
        el_temiz = el_harfleri_str.lower().replace(" ", "")
        hamleler = motor.hamle_bul(tahta_matrisi, el_temiz)

        # 4. HATA İHTİMALİ: Motor her şeyi okudu ama kelime üretemedi
        if not hamleler:
            return {
                "durum": "basarili", 
                "onerilen_kelimeler": [{"kelime": "HAMLEYOK", "puan": len(el_temiz), "baslangic": [7,7], "yon": "Yatay"}], 
                "el_harfleri": list(el_harfleri_str)
            }

        # HER ŞEY KUSURSUZ ÇALIŞIYORSA
        return {
            "durum": "basarili",
            "onerilen_kelimeler": hamleler[:30], 
            "el_harfleri": list(el_harfleri_str)
        }

    except Exception as e:
        # 5. HATA İHTİMALİ: Kod Çöktü
        return {
            "durum": "basarili", 
            "onerilen_kelimeler": [{"kelime": "SISTEMCOKTU", "puan": 999, "baslangic": [7,7], "yon": "Yatay"}], 
            "el_harfleri": ["H","A","T","A"]
        }