import cv2
import numpy as np
import os

# Kayıt klasörü
if not os.path.exists("referanslar_ham"):
    os.makedirs("referanslar_ham")

def referanslari_kaydet(resim_yolu):
    img = cv2.imread(resim_yolu)
    if img is None: return

    h, w, _ = img.shape

    # 1. KESME
    y_bas = int(h * 0.292)
    y_bit = y_bas + w
    if y_bit > h: y_bit = h
    tahta = img[y_bas:y_bit, 0:w]
    
    th, tw, _ = tahta.shape
    hucre_h = th / 15
    hucre_w = tw / 15

    # 2. RENK FİLTRESİ
    hsv = cv2.cvtColor(tahta, cv2.COLOR_BGR2HSV)
    alt_sinir = np.array([9, 75, 0])
    ust_sinir = np.array([179, 255, 252])
    maske = cv2.inRange(hsv, alt_sinir, ust_sinir)

    print("--- HARFLER KAYDEDİLİYOR ---")
    
    sayac = 0
    
    for satir in range(15):
        for sutun in range(15):
            y1 = int(satir * hucre_h)
            y2 = int((satir + 1) * hucre_h)
            x1 = int(sutun * hucre_w)
            x2 = int((sutun + 1) * hucre_w)

            hucre_maske = maske[y1:y2, x1:x2]
            
            # Doluluk Kontrolü (> %65)
            if cv2.countNonZero(hucre_maske) > (hucre_maske.size * 0.65):
                
                # --- HARFİ KES AL ---
                points = cv2.findNonZero(hucre_maske)
                if points is not None:
                    x, y, w_h, h_h = cv2.boundingRect(points)
                    
                    if w_h > 5 and h_h > 10:
                        harf_kutusu = tahta[y1:y2, x1:x2]
                        roi = harf_kutusu[y:y+h_h, x:x+w_h]
                        
                        # --- STANDARTLAŞTIRMA (ÇOK ÖNEMLİ) ---
                        # Eşleştirme yapabilmek için tüm resimler aynı boyutta olmalı
                        roi_resized = cv2.resize(roi, (30, 30)) # 30x30 piksel sabit boyut
                        
                        # Griye çevirip kaydedelim (Hafif yer kaplasın)
                        gri = cv2.cvtColor(roi_resized, cv2.COLOR_BGR2GRAY)
                        
                        dosya_adi = f"referanslar_ham/harf_{satir}_{sutun}.png"
                        cv2.imwrite(dosya_adi, gri)
                        sayac += 1
                        print(f"Kaydedildi: {dosya_adi}")

    print(f"\nToplam {sayac} adet harf resmi 'referanslar_ham' klasörüne kaydedildi.")

referanslari_kaydet("deneme.jpg")