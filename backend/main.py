from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from tahta_v11_final import tahtayi_oku, referanslari_yukle, en_iyi_eslesmeyi_bul
from solver import KelimelikSolver

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
solver = KelimelikSolver()

def ozel_el_okuyucu(img):
    """Eldeki taşları Kelimelik'in ahşap/sarı rengine göre okur"""
    try:
        referanslar = referanslari_yukle()
        if not referanslar: return ""

        h, w, _ = img.shape
        y_bas = int(h * 0.80) # Ekranın alt %20'si (Eldeki taşların olduğu yer)
        el_resmi = img[y_bas:h, 0:w]

        eh, ew, _ = el_resmi.shape
        slot_w = ew / 7.0

        okunan = ""
        tr_harita = {"oz": "ö", "ch": "ç", "sh": "ş", "ue": "ü", "gh": "ğ", "iu": "ı", "i": "i", "joker": "*", "yildiz": "*"}

        # KELİMELİK TAŞ RENGİ (Sarı/Ahşap Doğru Renk Filtresi)
        alt_sinir = np.array([9, 75, 0])
        ust_sinir = np.array([179, 255, 252])

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
        print("El okuma hatasi:", e)
        return ""

@app.post("/resim-coz")
async def coz(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Tahtayı Oku
        tahta_matrisi, _ = tahtayi_oku(img)

        # 2. Eli Kendi Özel Okuyucumuzla Oku (Renk hatası düzeltildi)
        el_harfleri_str = ozel_el_okuyucu(img)

        # HATA TESPİTİ 1: El Gerçekten Boş mu Okundu?
        if not el_harfleri_str or len(el_harfleri_str) == 0:
             return {
                "durum": "basarili",
                "onerilen_kelimeler": [{"kelime": "ELBOS", "puan": 404, "baslangic": (7,5), "yon": "Yatay", "jokerler": []}],
                "el_harfleri": ["B", "O", "Ş"]
             }

        # 3. Motoru çalıştır
        hamleler = solver.motor.hamle_bul(tahta_matrisi, el_harfleri_str.lower().replace(" ", ""))

        # HATA TESPİTİ 2: Motor mu kelime bulamadı?
        if not hamleler or len(hamleler) == 0:
             return {
                "durum": "basarili",
                "onerilen_kelimeler": [{"kelime": "KELIMEYOK", "puan": 0, "baslangic": (7,3), "yon": "Yatay", "jokerler": []}],
                "el_harfleri": list(el_harfleri_str)
             }

        # 4. Her şey normalse gerçek sonuçları dön
        return {
            "durum": "basarili",
            "onerilen_kelimeler": hamleler[:30],
            "el_harfleri": list(el_harfleri_str)
        }

    except Exception as e:
        # HATA TESPİTİ 3: Sunucu Çöktü mü?
        return {
            "durum": "basarili",
            "onerilen_kelimeler": [{"kelime": "COKTU", "puan": 999, "baslangic": (7,5), "yon": "Yatay", "jokerler": []}],
            "el_harfleri": ["H", "A", "T", "A"]
        }

@app.get("/")
def read_root():
    return {"durum": "Hazır", "versiyon": "v1.1 (Saglam Motor)"}