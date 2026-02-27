from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from tahta_v11_final import tahtayi_oku, eldeki_harfleri_oku
from solver import KelimelikSolver

app = FastAPI()

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

solver = KelimelikSolver()

@app.post("/resim-coz")
async def coz(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Tahtayı ve Harfleri Oku
        tahta_matrisi, _ = tahtayi_oku(img)
        el_harfleri_str = eldeki_harfleri_oku(img)

        # 2. Motoru çalıştır ve TÜM hamleleri bul
        hamleler = solver.motor.hamle_bul(tahta_matrisi, el_harfleri_str.lower().replace(" ", ""))

        # 3. Eski formatta (Liste olarak) geri döndür
        return {
            "durum": "basarili",
            "onerilen_kelimeler": hamleler[:30], # İlk 30 hamleyi gönderir
            "el_harfleri": list(el_harfleri_str) # Flutter tarafı liste bekliyor
        }
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

@app.get("/")
def read_root():
    return {"durum": "Hazır", "versiyon": "v1.0 (Eski Kararlı Sürüm)"}