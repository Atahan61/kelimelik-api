from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

# Senin kendi orijinal okuma dosyandan fonksiyonları alıyoruz
from tahta_v11_final import tahtayi_oku, eldeki_harfleri_oku
from solver import KelimelikSolver

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

solver = KelimelikSolver()

@app.post("/resim-coz")
async def coz(file: UploadFile = File(...)):
    try:
        # 1. Resmi Al
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 2. Tahtayı ve Eli Oku (Senin orijinal fonksiyonların)
        tahta_matrisi, _ = tahtayi_oku(img)
        el_harfleri_str = eldeki_harfleri_oku(img)

        # Eğer harf okuyamadıysa boş liste dön (Flutter tarafında 'hamle bulunamadı' yazar)
        if not el_harfleri_str:
            return {
                "durum": "hamle_yok",
                "onerilen_kelimeler": [],
                "el_harfleri": []
            }

        # 3. Çözücüyü Çalıştır ve Tüm Listeyi Al
        el_temiz = el_harfleri_str.lower().replace(" ", "")
        hamleler = solver.motor.hamle_bul(tahta_matrisi, el_temiz)

        if not hamleler:
            return {
                "durum": "hamle_yok",
                "onerilen_kelimeler": [],
                "el_harfleri": list(el_harfleri_str)
            }

        # 4. Sonucu Gönder
        return {
            "durum": "basarili",
            "onerilen_kelimeler": hamleler[:30], # İlk 30 kelimeyi liste olarak gönder
            "el_harfleri": list(el_harfleri_str) # Harfleri liste olarak gönder
        }

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

@app.get("/")
def read_root():
    return {"durum": "Hazır", "versiyon": "v1.0 (Orijinal Sistem)"}