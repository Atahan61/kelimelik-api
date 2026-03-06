from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Form
import cv2
import numpy as np

# Orijinal dosyandan gerekli parçaları alıyoruz
from tahta_v11_final import tahtayi_oku, referanslari_yukle, en_iyi_eslesmeyi_bul
from solver import motor 

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def eldeki_harfleri_oku_guvenli(img):
    """
    Senin el_ref_toplayici.py dosyanın BİREBİR aynısı olan kesim mantığı!
    Referanslar bu matematiğe göre toplandığı için %100 eşleşme sağlar.
    """
    referanslar = referanslari_yukle()
    if not referanslar: return ""

    h, w, _ = img.shape
    
    # SENİN BULDUĞUN MÜKEMMEL ORANLAR
    Y_BAS_ORAN = 0.756
    Y_BIT_ORAN = 0.825
    X_BAS_ORAN = 0.025
    X_BIT_ORAN = 0.975

    el_bolgesi = img[int(h*Y_BAS_ORAN):int(h*Y_BIT_ORAN), int(w*X_BAS_ORAN):int(w*X_BIT_ORAN)]
    h_el, w_el, _ = el_bolgesi.shape
    slot_w = w_el / 7.0

    hsv = cv2.cvtColor(el_bolgesi, cv2.COLOR_BGR2HSV)
    maske = cv2.inRange(hsv, np.array([9, 75, 0]), np.array([179, 255, 252]))

    okunan_harfler = ""
    tr_harita = {"oz": "ö", "ch": "ç", "sh": "ş", "ue": "ü", "gh": "ğ", "iu": "ı", "i": "i", "joker": "*", "yildiz": "*"}

    for i in range(7):
        x1 = int(i * slot_w)
        x2 = int((i + 1) * slot_w)
        slot_maske = maske[:, x1:x2]
        
        # Senin belirlediğin %30 barajı
        if cv2.countNonZero(slot_maske) > (slot_maske.size * 0.30):
            points = cv2.findNonZero(slot_maske)
            if points is not None:
                x, y, w_h, h_h = cv2.boundingRect(points)
                
                # MÜKEMMEL KESİM (Boşlukları at, sadece taşı al)
                slot_crop = el_bolgesi[y:y+h_h, x1+x:x1+x+w_h]
                
                # Senin kodundaki gibi griye çevir ve 60x60 yap (Referanslarla birebir aynı form)
                gri_crop = cv2.cvtColor(slot_crop, cv2.COLOR_BGR2GRAY)
                kucuk_crop = cv2.resize(gri_crop, (60, 60))
                
                # Artık referanslarla karşılaştırabiliriz
                harf, skor = en_iyi_eslesmeyi_bul(kucuk_crop, referanslar)
                
                if harf != "?":
                    temiz_harf = harf.split("_")[0] if "_" in harf else harf
                    final_harf = tr_harita.get(temiz_harf, temiz_harf)
                    okunan_harfler += final_harf.upper()
                else:
                    # %30'dan fazla sarı var ama harf tanınmadı = Gerçek JOKER!
                    okunan_harfler += "*"
                    
    return okunan_harfler


@app.post("/resim-coz")
async def coz(file: UploadFile = File(...), manuel_el: str = Form(None)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        tahta_matrisi, _ = tahtayi_oku(img)

        # Hata kontrolü 1: Tahta
        if not tahta_matrisi or len(tahta_matrisi) == 0:
            return {"durum": "hamle_yok", "onerilen_kelimeler": [], "el_harfleri": []}

        # ZEKİCE DOKUNUŞ: Eğer kullanıcı harfleri elle değiştirdiyse (manuel_el doluysa) onu kullan, 
        # yoksa resmi okumaya çalış.
        if manuel_el:
            el_harfleri_str = manuel_el
        else:
            el_harfleri_str = eldeki_harfleri_oku_guvenli(img)

        # Hata kontrolü 2: El
        if not el_harfleri_str:
            return {"durum": "hamle_yok", "onerilen_kelimeler": [], "el_harfleri": []}

        # Çözücü
        el_temiz = el_harfleri_str.replace("I", "ı").replace("İ", "i").lower().replace(" ", "")
        hamleler = motor.hamle_bul(tahta_matrisi, el_temiz)

        if not hamleler:
            return {"durum": "hamle_yok", "onerilen_kelimeler": [], "el_harfleri": list(el_harfleri_str.upper())}

        return {"durum": "basarili", "onerilen_kelimeler": hamleler[:30], "el_harfleri": list(el_harfleri_str.upper())}

    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

@app.get("/")
def read_root():
    return {"durum": "Hazır"}