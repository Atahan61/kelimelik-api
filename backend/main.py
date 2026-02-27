from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np

from tahta_v11_final import tahtayi_oku, eldeki_harfleri_oku
from solver import motor 

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.post("/resim-coz")
async def coz(file: UploadFile = File(...)):
    try:
        print("--- YENI ISTEK GELDI ---")
        
        # 1. Resim Kontrolü
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        print(f"1. Resim Boyutu: {img.shape if img is not None else 'RESIM YOK'}")

        # 2. Tahta Kontrolü
        tahta_matrisi, _ = tahtayi_oku(img)
        dolu_kare_sayisi = sum(1 for satir in tahta_matrisi for hucre in satir if hucre is not None and str(hucre) != "?")
        print(f"2. Tahtadaki Dolu Kare Sayisi: {dolu_kare_sayisi}")

        # 3. El Kontrolü
        el_harfleri_str = eldeki_harfleri_oku(img)
        print(f"3. Okunan El Harfleri: '{el_harfleri_str}'")

        # 4. Sözlük Kontrolü
        print(f"4. Sozlukteki Kelime Sayisi: {motor.kelime_sayisi}")

        if not el_harfleri_str:
            print("=> SONUC: El harfleri bos oldugu icin hamle yok donduruldu.")
            return {"durum": "hamle_yok", "onerilen_kelimeler": [], "el_harfleri": []}

        # 5. Çözücü Kontrolü
        el_temiz = el_harfleri_str.lower().replace(" ", "")
        print(f"5. Motora Gonderilen Harfler: '{el_temiz}'")
        
        hamleler = motor.hamle_bul(tahta_matrisi, el_temiz)
        print(f"6. Bulunan Hamle Sayisi: {len(hamleler) if hamleler else 0}")

        if not hamleler:
            print("=> SONUC: Motor hicbir kelime bulamadi.")
            return {"durum": "hamle_yok", "onerilen_kelimeler": [], "el_harfleri": list(el_harfleri_str)}

        print("=> SONUC: Basarili! Hamleler gonderiliyor.")
        return {"durum": "basarili", "onerilen_kelimeler": hamleler[:30], "el_harfleri": list(el_harfleri_str)}

    except Exception as e:
        print(f"!!! KRITIK HATA: {str(e)}")
        return {"durum": "hata", "mesaj": str(e)}

@app.get("/")
def read_root():
    return {"durum": "Hazır"}