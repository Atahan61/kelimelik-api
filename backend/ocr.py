import cv2
import pytesseract

# --- AYARLAR ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def harfleri_tani(resim_yolu):
    try:
        img = cv2.imread(resim_yolu)
        if img is None: return ""

        h, w, _ = img.shape

        # --- SENİN KALİBRASYON AYARLARIN ---
        y1 = int(h * 0.755)
        y2 = int(h * 0.825)
        x1 = int(w * 0.01)
        x2 = int(w * 0.99)

        # 1. Kırpma
        kirpilmis = img[y1:y2, x1:x2]

        # --- YENİ EKLENEN SİHİR: BÜYÜTME (UPSCALE) ---
        # Resmi 3 kat büyütüyoruz ki Tesseract harfleri net görsün.
        yukseklik, genislik = kirpilmis.shape[:2]
        kirpilmis = cv2.resize(kirpilmis, (genislik*3, yukseklik*3), interpolation=cv2.INTER_CUBIC)
        # ---------------------------------------------

        # 2. Griye Çevir
        gri = cv2.cvtColor(kirpilmis, cv2.COLOR_BGR2GRAY)

        # 3. Threshold (Siyah-Beyaz)
        _, siyah_beyaz = cv2.threshold(gri, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 4. Tesseract ile Oku
        config = '--psm 7 -c tessedit_char_whitelist=ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ'
        ham_metin = pytesseract.image_to_string(siyah_beyaz, lang='tur', config=config)

        # 5. Temizlik
        temiz_harfler = ""
        for karakter in ham_metin:
            if karakter.isalpha():
                temiz_harfler += karakter
        
        temiz_harfler = temiz_harfler.replace("İ", "i").replace("I", "ı").lower()

        # 6. Eksikleri Joker (?) ile tamamla
        if len(temiz_harfler) < 7:
            # Sadece makul sayıda eksik varsa tamamla (Örn: 1-2 harf eksikse)
            # Eğer "SK" gibi sadece 2 harf okuduysa, belki de resim çok kötüdür, 
            # yine de dolduralım şansımızı deneyelim.
            eksik = 7 - len(temiz_harfler)
            temiz_harfler += "?" * eksik

        return temiz_harfler

    except Exception as e:
        print(f"Hata: {e}")
        return ""