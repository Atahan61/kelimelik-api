import cv2

def el_izgara_ciz(resim_yolu):
    img = cv2.imread(resim_yolu)
    if img is None: return

    h, w, _ = img.shape

    # Istaka genelde ekranın alt %80'inden sonra başlar
    # Referans çizgileri çizelim
    gosterim = img.copy()
    
    # Kırmızı Çizgiler (Yatay Konum Belirlemek İçin)
    adim = int(h * 0.02) # %2 aralıklarla çizgi
    baslangic = int(h * 0.70) # %70'ten başla
    
    for y in range(baslangic, h, adim):
        cv2.line(gosterim, (0, y), (w, y), (0, 0, 255), 2)
        cv2.putText(gosterim, f"%{int((y/h)*100)}", (10, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # --- GÖSTER ---
    # Resmi ekrana sığacak kadar küçültelim
    gosterim = cv2.resize(gosterim, (0,0), fx=0.5, fy=0.5)
    
    print("Resimdeki Kırmızı Çizgilere bak.")
    print("Harfler hangi yüzdeler (%) arasında kalıyor?")
    print("Örn: %85 ile %95 arası")
    
    cv2.imshow("Istaka Bulucu", gosterim)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

el_izgara_ciz("deneme.jpg")