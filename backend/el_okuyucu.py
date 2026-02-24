import cv2
import numpy as np
import os

# --- AYARLAR ---
REFERANS_KLASORU = "referanslar_ham" 

# --- KOORDİNATLAR (Senin verdiğin değerler) ---
Y_BAS_ORAN = 0.756
Y_BIT_ORAN = 0.825
X_BAS_ORAN = 0.025
X_BIT_ORAN = 0.975

def dosya_oku_gri(dosya_yolu):
    try:
        with open(dosya_yolu, "rb") as f:
            bytes = bytearray(f.read())
            numpy_array = np.asarray(bytes, dtype=np.uint8)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_GRAYSCALE)
            return img
    except: return None

def dosya_oku_renkli(dosya_yolu):
    try:
        with open(dosya_yolu, "rb") as f:
            bytes = bytearray(f.read())
            numpy_array = np.asarray(bytes, dtype=np.uint8)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
            return img
    except: return None

def referanslari_yukle():
    referanslar = {}
    if not os.path.exists(REFERANS_KLASORU):
        print(f"HATA: '{REFERANS_KLASORU}' klasörü bulunamadı!")
        return {}

    dosyalar = os.listdir(REFERANS_KLASORU)
    print(f"--- REFERANSLAR YÜKLENİYOR ({len(dosyalar)} dosya) ---")
    
    for dosya in dosyalar:
        if dosya.endswith(".png") or dosya.endswith(".jpg"):
            harf_adi = os.path.splitext(dosya)[0].lower()
            yol = os.path.join(REFERANS_KLASORU, dosya)
            img = dosya_oku_gri(yol)
            if img is not None:
                img = cv2.resize(img, (30, 30))
                referanslar[harf_adi] = img
    return referanslar

def en_iyi_eslesmeyi_bul(hucre_resmi, referanslar):
    en_iyi_skor = -1
    en_iyi_harf = "?"
    
    if len(hucre_resmi.shape) == 3:
        hucre_gri = cv2.cvtColor(hucre_resmi, cv2.COLOR_BGR2GRAY)
    else:
        hucre_gri = hucre_resmi
        
    hucre_gri = cv2.resize(hucre_gri, (30, 30))

    for harf, ref_resim in referanslar.items():
        sonuc = cv2.matchTemplate(hucre_gri, ref_resim, cv2.TM_CCOEFF_NORMED)
        skor = np.max(sonuc)
        if skor > en_iyi_skor:
            en_iyi_skor = skor
            en_iyi_harf = harf

    if en_iyi_skor > 0.65: # Eşik değeri biraz daha esnek olabilir
        return en_iyi_harf, en_iyi_skor
    else:
        return "?", en_iyi_skor

def eli_oku(resim_yolu):
    referanslar = referanslari_yukle()
    if not referanslar: return []

    img = dosya_oku_renkli(resim_yolu)
    if img is None: return []

    h, w, _ = img.shape

    # 1. EL BÖLGESİNİ KES
    y_bas = int(h * Y_BAS_ORAN)
    y_bit = int(h * Y_BIT_ORAN)
    x_bas = int(w * X_BAS_ORAN)
    x_bit = int(w * X_BIT_ORAN)
    
    el_bolgesi = img[y_bas:y_bit, x_bas:x_bit]
    h_el, w_el, _ = el_bolgesi.shape
    
    # 7 Eşit Parça
    slot_w = w_el / 7

    # Renk Filtresi (Taşları bulmak için)
    hsv = cv2.cvtColor(el_bolgesi, cv2.COLOR_BGR2HSV)
    alt_sinir = np.array([9, 75, 0])
    ust_sinir = np.array([179, 255, 252])
    maske = cv2.inRange(hsv, alt_sinir, ust_sinir)
    
    print("\n--- EL ANALİZİ ---")
    el_harfleri = []
    gosterim = el_bolgesi.copy()

    for i in range(7):
        x1 = int(i * slot_w)
        x2 = int((i + 1) * slot_w)
        
        # Maskeden slotu kes
        slot_maske = maske[:, x1:x2]
        
        # Doluluk kontrolü
        if cv2.countNonZero(slot_maske) > (slot_maske.size * 0.40):
            # Harfi bul ve kes
            points = cv2.findNonZero(slot_maske)
            if points is not None:
                x, y, w_h, h_h = cv2.boundingRect(points)
                
                # Koordinatları slota göre ayarla
                roi = el_bolgesi[y:y+h_h, x1+x:x1+x+w_h]
                
                # Eşleştirme
                harf, skor = en_iyi_eslesmeyi_bul(roi, referanslar)
                
                # Çıktı
                el_harfleri.append(harf)
                
                # Çizim
                cv2.rectangle(gosterim, (x1+x, y), (x1+x+w_h, y+h_h), (0,255,0), 2)
                cv2.putText(gosterim, f"{harf.upper()}", (x1+5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        else:
            # Boş slot
            pass

    print(f"Bulunan Harfler: {el_harfleri}")
    
    cv2.imshow("El Okuyucu", gosterim)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return el_harfleri

if __name__ == "__main__":
    eli_oku("deneme.jpg")