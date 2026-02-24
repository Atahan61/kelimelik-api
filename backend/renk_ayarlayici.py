import cv2
import numpy as np

def hicbir_sey_yapma(x):
    pass

def renk_ayarlayici(resim_yolu):
    img = cv2.imread(resim_yolu)
    if img is None: return

    # Resmi küçült (Ekrana sığsın)
    img = cv2.resize(img, (0,0), fx=0.5, fy=0.5) 
    
    cv2.namedWindow("Renk Ayarlari")

    # Trackbar (Kaydırma Çubukları) Oluştur
    # HSV formatında renk aralığı (Hue, Saturation, Value)
    cv2.createTrackbar("H-Min", "Renk Ayarlari", 0, 179, hicbir_sey_yapma)
    cv2.createTrackbar("S-Min", "Renk Ayarlari", 0, 255, hicbir_sey_yapma)
    cv2.createTrackbar("V-Min", "Renk Ayarlari", 0, 255, hicbir_sey_yapma)
    
    cv2.createTrackbar("H-Max", "Renk Ayarlari", 179, 179, hicbir_sey_yapma)
    cv2.createTrackbar("S-Max", "Renk Ayarlari", 255, 255, hicbir_sey_yapma)
    cv2.createTrackbar("V-Max", "Renk Ayarlari", 255, 255, hicbir_sey_yapma)

    while True:
        # HSV formatına çevir (Renk ayrımı için en iyisi)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Trackbar değerlerini oku
        h_min = cv2.getTrackbarPos("H-Min", "Renk Ayarlari")
        s_min = cv2.getTrackbarPos("S-Min", "Renk Ayarlari")
        v_min = cv2.getTrackbarPos("V-Min", "Renk Ayarlari")
        h_max = cv2.getTrackbarPos("H-Max", "Renk Ayarlari")
        s_max = cv2.getTrackbarPos("S-Max", "Renk Ayarlari")
        v_max = cv2.getTrackbarPos("V-Max", "Renk Ayarlari")

        # Maske oluştur (Alt ve Üst sınırlar)
        alt_sinir = np.array([h_min, s_min, v_min])
        ust_sinir = np.array([h_max, s_max, v_max])
        
        maske = cv2.inRange(hsv, alt_sinir, ust_sinir)

        # Maskeyi resimle birleştirip göster
        sonuc = cv2.bitwise_and(img, img, mask=maske)

        cv2.imshow("Orijinal", img)
        cv2.imshow("Maske (Siyah-Beyaz)", maske)
        cv2.imshow("Sonuc (Renkli)", sonuc)

        # 'q' tuşuna basınca çık
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print(f"--- BULUNAN DEĞERLER ---")
            print(f"ALT SINIR: [{h_min}, {s_min}, {v_min}]")
            print(f"ÜST SINIR: [{h_max}, {s_max}, {v_max}]")
            break

    cv2.destroyAllWindows()

renk_ayarlayici("deneme.jpg")