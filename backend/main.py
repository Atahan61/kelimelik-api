from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from tahta_v11_final import tahtayi_oku, eldeki_harfleri_oku 
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

solver = KelimelikSolver()

async def resmi_isle(file: UploadFile):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

@app.post("/resim-coz")
async def coz(
    file: UploadFile = File(...),
    manuel_el: str = Form(None)
):
    try:
        img = await resmi_isle(file)
        tahta_matrisi, _ = tahtayi_oku(img)

        # Manuel giriş varsa onu kullan, yoksa kendin oku
        if manuel_el and manuel_el.strip() != "":
             el_harfleri = manuel_el.strip()
        else:
             el_harfleri = eldeki_harfleri_oku(img)

        en_iyi_hamle, puan = solver.en_iyi_hamleyi_bul(tahta_matrisi, el_harfleri)

        if en_iyi_hamle:
            # DİKKAT: Artık okunan el_harfleri de telefona gönderiliyor!
            return {"durum": "basarili", "hamle": en_iyi_hamle, "el_harfleri": el_harfleri}
        else:
            return {"durum": "hamle_yok", "el_harfleri": el_harfleri}

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

@app.get("/")
def read_root():
    return {"durum": "Hazır", "versiyon": "v4.0 (Akıllı Düzeltme)"}