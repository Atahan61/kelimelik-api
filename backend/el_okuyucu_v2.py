import cv2
import numpy as np
import os

# --- AYARLAR ---
REFERANS_KLASORU = "referanslar_ham" 
Y_BAS_ORAN = 0.756
Y_BIT_ORAN = 0.825
X_BAS_ORAN = 0.025
X_BIT_ORAN = 0.975

def dosya_oku_renkli(dosya_yolu):
    try:
        with open(dosya_yolu, "rb") as f:
            bytes_data = bytearray(f.read())
            numpy_array = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
            return img
    except Exception as e: 
        print(f"❌ Renk okuma hatası: {e}")
        return None

def dosya_oku_gri(dosya_yolu):
    try:
        with open(dosya_yolu, "rb") as f:
            bytes_data = bytearray(f.read())
            numpy_array = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_GRAYSCALE)
            return img
    except: return None

def referanslari_yukle():
    print("📥 El Okuyucu: Referanslar yükleniyor...")
    referanslar = {}
    if not os.path.exists(REFERANS_KLASORU):
        print(f"❌ HATA: '{REFERANS_KLASORU}' klasörü bulunamadı!")
        return {}

    dosyalar = os.listdir(REFERANS_KLASORU)
    
    for dosya in dosyalar:
        if dosya.endswith(".png") or dosya.endswith(".jpg"):
            ham_isim = os.path.splitext(dosya)[0].lower()
            
            if "_" in ham_isim:
                harf_adi = ham_isim.split('_')[0] 
            else:
                harf_adi = ham_isim
            
            # Türkçe Karakter Haritası
            tr_harita = {
                "oz": "ö", "ch": "ç", "sh": "ş",
                "ue": "ü", "gh": "ğ", "iu": "ı", 
                "i": "i", "joker": "*"
            }
            
            final_harf = tr_harita.get(harf_adi, harf_adi)
                
            if final_harf not in referanslar:
                referanslar[final_harf] = []

            yol = os.path.join(REFERANS_KLASORU, dosya)
            img = dosya_oku_gri(yol)
            if img is not None:
                img = cv2.resize(img, (60, 60))
                referanslar[final_harf].append(img)
    
    print(f"✅ El Okuyucu: {len(referanslar)} farklı harf (HD) başarıyla yüklendi.")
    return referanslar

def en_iyi_eslesmeyi_bul(hucre_resmi, referanslar):
    en_iyi_skor = -1
    en_iyi_harf = "?"
    
    if len(hucre_resmi.shape) == 3:
        hucre_gri = cv2.cvtColor(hucre_resmi, cv2.COLOR_BGR2GRAY)
    else:
        hucre_gri = hucre_resmi
        
    hucre_gri = cv2.resize(hucre_gri, (60, 60))

    for harf, resim_listesi in referanslar.items():
        for ref_resim in resim_listesi:
            sonuc = cv2.matchTemplate(hucre_gri, ref_resim, cv2.TM_CCOEFF_NORMED)
            skor = np.max(sonuc)
            
            if skor > en_iyi_skor:
                en_iyi_skor = skor
                en_iyi_harf = harf

    if en_iyi_skor > 0.45:
        return en_iyi_harf, en_iyi_skor
    else:
        return "?", en_iyi_skor

def eli_oku(resim_yolu):
    print("\n--- 🖐️ EL ANALİZİ BAŞLIYOR ---")
    
    referanslar = referanslari_yukle()
    if not referanslar: 
        print("❌ El Okuyucu İptal: Referanslar boş!")
        return []

    img = dosya_oku_renkli(resim_yolu)
    if img is None: 
        print("❌ El Okuyucu İptal: Ana resim bulunamadı!")
        return []

    h, w, _ = img.shape
    y_bas = int(h * Y_BAS_ORAN)
    y_bit = int(h * Y_BIT_ORAN)
    x_bas = int(w * X_BAS_ORAN)
    x_bit = int(w * X_BIT_ORAN)
    
    el_bolgesi = img[y_bas:y_bit, x_bas:x_bit]
    h_el, w_el, _ = el_bolgesi.shape
    slot_w = w_el / 7

    hsv = cv2.cvtColor(el_bolgesi, cv2.COLOR_BGR2HSV)
    alt_sinir = np.array([9, 75, 0])
    ust_sinir = np.array([179, 255, 252])
    maske = cv2.inRange(hsv, alt_sinir, ust_sinir)
    
    el_harfleri = []

    for i in range(7):
        x1 = int(i * slot_w)
        x2 = int((i + 1) * slot_w)
        slot_maske = maske[:, x1:x2]
        
        if cv2.countNonZero(slot_maske) > (slot_maske.size * 0.30):
            points = cv2.findNonZero(slot_maske)
            if points is not None:
                x, y, w_h, h_h = cv2.boundingRect(points)
                
                if w_h > 5 and h_h > 10:
                    roi = el_bolgesi[y:y+h_h, x1+x:x1+x+w_h]
                    harf, skor = en_iyi_eslesmeyi_bul(roi, referanslar)
                    el_harfleri.append(harf)
                    print(f"Slot {i+1}: {harf.upper()} (Skor: {skor:.4f})")

                    # --- DEBUG EKLENTISI (SADECE SLOT 6 İÇİN) ---
                    if i == 5: # Slot 6 (0'dan başladığı için 5)
                        print("   🕵️‍♂️ SLOT 6 ÖZEL İNCELEME:")
                        hucre_gri = cv2.resize(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY), (60, 60))
                        for test_harf in ['e', 'l']:
                            if test_harf in referanslar:
                                for idx, test_res in enumerate(referanslar[test_harf]):
                                    test_skor = np.max(cv2.matchTemplate(hucre_gri, test_res, cv2.TM_CCOEFF_NORMED))
                                    print(f"      🆚 {test_harf.upper()} Referansı {idx+1} Skoru: {test_skor:.4f}")
                    # -----------------------------------------------
                else:
                    print(f"Slot {i+1}: Küçük gürültü")
        else:
            print(f"Slot {i+1}: Boş")

    print(f"🖐️ Bulunan El: {el_harfleri}")
    print("--- 🖐️ EL ANALİZİ BİTTİ ---\n")
    return el_harfleri

if __name__ == "__main__":
    eli_oku("deneme.jpg")