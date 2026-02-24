import cv2
import numpy as np
import os

# --- SENİN GÜNCEL AYARLARIN ---
# Buraya en son "kutular karelere oturdu" dediğin değerleri yaz!
Y_BAS_ORAN = 0.756
Y_BIT_ORAN = 0.825
X_BAS_ORAN = 0.025
X_BIT_ORAN = 0.975

# Kayıt Klasörü
if not os.path.exists("referanslar_ham"):
    os.makedirs("referanslar_ham")

def dosya_oku_renkli(dosya_yolu):
    try:
        with open(dosya_yolu, "rb") as f:
            bytes = bytearray(f.read())
            numpy_array = np.asarray(bytes, dtype=np.uint8)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
            return img
    except: return None

def el_harflerini_kaydet(resim_yolu):
    img = dosya_oku_renkli(resim_yolu)
    if img is None: return

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

    # Renk Filtresi
    hsv = cv2.cvtColor(el_bolgesi, cv2.COLOR_BGR2HSV)
    alt_sinir = np.array([9, 75, 0])
    ust_sinir = np.array([179, 255, 252])
    maske = cv2.inRange(hsv, alt_sinir, ust_sinir)
    
    print("\n--- EL HARFLERİ KAYDEDİLİYOR ---")
    
    for i in range(7):
        x1 = int(i * slot_w)
        x2 = int((i + 1) * slot_w)
        
        # Maskeden slotu kes
        slot_maske = maske[:, x1:x2]
        
        # Doluluk kontrolü (> %30)
        if cv2.countNonZero(slot_maske) > (slot_maske.size * 0.30):
            # Harfin sınırlarını bul (Cımbızla çek)
            points = cv2.findNonZero(slot_maske)
            if points is not None:
                x, y, w_h, h_h = cv2.boundingRect(points)
                
                # Sadece harfin olduğu kutucuğu kes (Renkli resimden)
                roi = el_bolgesi[y:y+h_h, x1+x:x1+x+w_h]
                
                # --- STANDARTLAŞTIRMA ---
                # 30x30 boyutuna getir ve GRİ yap
                roi_resized = cv2.resize(roi, (30, 30))
                roi_gri = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2GRAY)
                
                # Kaydet
                dosya_adi = f"referanslar_ham/el_harf_{i+1}.png"
                cv2.imwrite(dosya_adi, roi_gri)
                print(f"Kaydedildi: {dosya_adi}")

    print("\nLütfen 'referanslar_ham' klasörüne git ve bu yeni dosyaların ismini değiştir.")
    print("Örnek: 'el_harf_1.png' resminde 'D' varsa, adını 'd_el.png' yap.")

el_harflerini_kaydet("deneme.jpg")