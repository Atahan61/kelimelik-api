import cv2
import numpy as np
import os

DOSYA_ADI = "d1.jpg" 
CIKTI_KLASORU = "ham_el_harfleri"

Y_BAS_ORAN = 0.756
Y_BIT_ORAN = 0.825
X_BAS_ORAN = 0.025
X_BIT_ORAN = 0.975

img = cv2.imread(DOSYA_ADI)
h, w, _ = img.shape

if not os.path.exists(CIKTI_KLASORU):
    os.makedirs(CIKTI_KLASORU)

el_bolgesi = img[int(h*Y_BAS_ORAN):int(h*Y_BIT_ORAN), int(w*X_BAS_ORAN):int(w*X_BIT_ORAN)]
h_el, w_el, _ = el_bolgesi.shape
slot_w = w_el / 7

hsv = cv2.cvtColor(el_bolgesi, cv2.COLOR_BGR2HSV)
maske = cv2.inRange(hsv, np.array([9, 75, 0]), np.array([179, 255, 252]))

sayac = 0
for i in range(7):
    x1 = int(i * slot_w)
    x2 = int((i + 1) * slot_w)
    slot_maske = maske[:, x1:x2]
    
    if cv2.countNonZero(slot_maske) > (slot_maske.size * 0.30):
        points = cv2.findNonZero(slot_maske)
        x, y, w_h, h_h = cv2.boundingRect(points)
        
        # MÜKEMMEL KESİM: Arka plan boşluklarını çöpe at, sadece taşı al!
        slot_crop = el_bolgesi[y:y+h_h, x1+x:x1+x+w_h]
        
        gri_crop = cv2.cvtColor(slot_crop, cv2.COLOR_BGR2GRAY)
        kucuk_crop = cv2.resize(gri_crop, (60, 60))
        
        hedef = f"{CIKTI_KLASORU}/el_slot_{i+1}.jpg"
        cv2.imwrite(hedef, kucuk_crop)
        sayac += 1

print("✅ İşlem Tamam! Arka plan boşlukları atıldı, taşlar tam ortalanarak kesildi.")