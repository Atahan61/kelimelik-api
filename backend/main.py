from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from tahta_v11_final import tahtayi_oku, referanslari_yukle, en_iyi_eslesmeyi_bul
from solver import KelimelikSolver

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
solver = KelimelikSolver()

def saglam_el_okuyucu(img):
    """Farklı ekran boyutlarındaki telefonlar için Evrensel El Okuyucu"""
    try:
        referanslar = referanslari_yukle()
        if not referanslar: return ""

        h, w, _ = img.shape
        
        # YENİ NESİL KESİM: Sadece en alt %15 değil, alt %25'e geniş geniş bakalım
        # Böylece uzun/kısa her telefonda eldeki taşlar bu karenin içine kesin düşer!
        y_bas = int(h * 0.75) 
        el_resmi = img[y_bas:h, 0:w]
        eh, ew, _ = el_resmi.shape
        slot_w = ew / 7.0

        okunan = ""
        tr_harita = {"oz": "ö", "ch": "ç", "sh": "ş", "ue": "ü", "gh": "ğ", "iu": "ı", "i": "i", "joker": "*", "yildiz": "*"}

        # BAŞARILI OLAN ORİJİNAL RENK MASKESİ (Beyaz/Krem/Açık Gri)
        alt_sinir = np.array([0, 0, 100])
        ust_sinir = np.array([180, 50, 255])

        for i in range(7):
            x1 = int(i * slot_w)
            x2 = int((i + 1) * slot_w)
            margin = int(slot_w * 0.1)
            hucre = el_resmi[0:eh, x1+margin:x2-margin]

            hsv = cv2.cvtColor(hucre, cv2.COLOR_BGR2HSV)
            maske = cv2.inRange(hsv, alt_sinir, ust_sinir)

            if cv2.countNonZero(maske) > (hucre.size * 0.05):
                harf, skor = en_iyi_eslesmeyi_bul(hucre, referanslar)
                if harf != "?":
                    temiz_harf = harf.split("_")[0] if "_" in harf else harf
                    okunan += tr_harita.get(temiz_harf, temiz_harf).upper()

        return okunan
    except Exception as e:
        print("Okuma Hatası:", e)
        return ""

@app.post("/resim-coz")
async def coz(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Tahtayı Oku
        tahta_matrisi, _ = tahtayi_oku(img)

        # 2. Eli Kendi Yeni Okuyucumuzla Oku
        el_harfleri_str = saglam_el_okuyucu(img)

        if not el_harfleri_str:
            return {"durum": "hamle_yok"} # Harf yoksa hamle de yok

        # 3. Motoru çalıştır
        hamleler = solver.motor.hamle_bul(tahta_matrisi, el_harfleri_str.lower().replace(" ", ""))

        if not hamleler:
            return {"durum": "hamle_yok"}

        # 4. Gerçek Sonuçları Dön
        return {
            "durum": "basarili",
            "onerilen_kelimeler": hamleler[:30],
            "el_harfleri": list(el_harfleri_str)
        }

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

@app.get("/")
def read_root():
    return {"durum": "Hazır", "versiyon": "v1.2 (Evrensel Cözüm)"}