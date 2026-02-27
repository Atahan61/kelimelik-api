from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

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

        h, w, _ = img.shape
        
        # 1. ORİJİNAL KESİM (Alt %15)
        el_15 = img[int(h * 0.85):h, 0:w]
        hsv_15 = cv2.cvtColor(el_15, cv2.COLOR_BGR2HSV)
        b_15 = cv2.countNonZero(cv2.inRange(hsv_15, np.array([0, 0, 100]), np.array([180, 50, 255])))
        s_15 = cv2.countNonZero(cv2.inRange(hsv_15, np.array([9, 75, 0]), np.array([179, 255, 252])))
        
        # 2. GENİŞ KESİM (Alt %25)
        el_25 = img[int(h * 0.75):h, 0:w]
        hsv_25 = cv2.cvtColor(el_25, cv2.COLOR_BGR2HSV)
        b_25 = cv2.countNonZero(cv2.inRange(hsv_25, np.array([0, 0, 100]), np.array([180, 50, 255])))
        s_25 = cv2.countNonZero(cv2.inRange(hsv_25, np.array([9, 75, 0]), np.array([179, 255, 252])))

        # Raporu kelime listesi gibi telefona yolluyoruz! (Puan kısmı = Piksel Sayısı)
        rapor_hamleleri = [
            {"kelime": "ESKIBEYAZ", "puan": b_15, "baslangic": [7,7], "yon": "Yatay", "jokerler": []},
            {"kelime": "ESKISARI", "puan": s_15, "baslangic": [8,7], "yon": "Yatay", "jokerler": []},
            {"kelime": "YENIBEYAZ", "puan": b_25, "baslangic": [9,7], "yon": "Yatay", "jokerler": []},
            {"kelime": "YENISARI", "puan": s_25, "baslangic": [10,7], "yon": "Yatay", "jokerler": []}
        ]

        return {
            "durum": "basarili", 
            "onerilen_kelimeler": rapor_hamleleri, 
            "el_harfleri": ["T","E","S","T"]
        }

    except Exception as e:
        return {
            "durum": "basarili", 
            "onerilen_kelimeler": [{"kelime": "COKTU", "puan": 999, "baslangic": [7,7], "yon": "Yatay"}], 
            "el_harfleri": ["H","A","T","A"]
        }