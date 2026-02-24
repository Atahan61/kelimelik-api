import cv2
import numpy as np
import os

# --- AYARLAR ---
REFERANS_KLASORU = "referanslar_ham" 

def dosya_oku_gri(dosya_yolu):
    """Referans resimleri için: Dosyayı GRİ okur (Türkçe karakter destekli)"""
    try:
        with open(dosya_yolu, "rb") as f:
            bytes_data = bytearray(f.read())
            numpy_array = np.asarray(bytes_data, dtype=np.uint8)
            # GRİ OKU (IMREAD_GRAYSCALE = 0)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_GRAYSCALE)
            return img
    except Exception as e:
        return None

def dosya_oku_renkli(dosya_yolu):
    """Ana resim için: Dosyayı RENKLİ okur (Türkçe karakter destekli)"""
    try:
        with open(dosya_yolu, "rb") as f:
            bytes_data = bytearray(f.read())
            numpy_array = np.asarray(bytes_data, dtype=np.uint8)
            # RENKLİ OKU (IMREAD_COLOR = 1)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
            return img
    except Exception as e:
        return None

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
            
            # Referansları GRİ okuyoruz
            img = dosya_oku_gri(yol)
            
            if img is not None:
                img = cv2.resize(img, (60, 60))
                referanslar[harf_adi] = img
            else:
                print(f"UYARI: {dosya} yüklenemedi!")
    
    print("Referans yükleme tamamlandı.\n")
    return referanslar

def en_iyi_eslesmeyi_bul(hucre_resmi, referanslar):
    en_iyi_skor = -1
    en_iyi_harf = "?"
    
    # Hücre renkli geldiyse griye çevir (Eşleştirme gri yapılır)
    if len(hucre_resmi.shape) == 3:
        hucre_gri = cv2.cvtColor(hucre_resmi, cv2.COLOR_BGR2GRAY)
    else:
        hucre_gri = hucre_resmi
        
    hucre_gri = cv2.resize(hucre_gri, (60, 60))

    for harf, ref_resim in referanslar.items():
        # Eşleştirme
        sonuc = cv2.matchTemplate(hucre_gri, ref_resim, cv2.TM_CCOEFF_NORMED)
        skor = np.max(sonuc)
        
        if skor > en_iyi_skor:
            en_iyi_skor = skor
            en_iyi_harf = harf

    # Eşik Değeri: %70
    if en_iyi_skor > 0.70:
        return en_iyi_harf, en_iyi_skor
    else:
        return "?", en_iyi_skor

def tahtayi_oku_final(resim_yolu):
    referanslar = referanslari_yukle()
    if not referanslar: return []

    # 1. ANA RESMİ RENKLİ OKU
    img = dosya_oku_renkli(resim_yolu)
    if img is None: 
        print("Ana resim okunamadı!")
        return []

    h, w, _ = img.shape

    # 2. TAHTAYI KES
    y_bas = int(h * 0.292)
    y_bit = y_bas + w
    if y_bit > h: y_bit = h
    tahta = img[y_bas:y_bit, 0:w]
    
    th, tw, _ = tahta.shape
    hucre_h = th / 15.0
    hucre_w = tw / 15.0

    # 3. RENK FİLTRESİ
    hsv = cv2.cvtColor(tahta, cv2.COLOR_BGR2HSV)
    alt_sinir = np.array([9, 75, 0])
    ust_sinir = np.array([179, 255, 252])
    maske = cv2.inRange(hsv, alt_sinir, ust_sinir)

    print("--- TAHTA ANALİZİ (V11 - Renkli & Türkçe & VIP Yıldız) ---")
    
    kontrol_resmi = tahta.copy()
    
    # Çözücü motorun "None" bekleme ihtimaline karşı boş matrisi None ile dolduruyoruz
    matris = [[None for _ in range(15)] for _ in range(15)]

    for satir in range(15):
        satir_metni = "" 
        for sutun in range(15):
            y1 = int(satir * hucre_h)
            y2 = int((satir + 1) * hucre_h)
            x1 = int(sutun * hucre_w)
            x2 = int((sutun + 1) * hucre_w)

            hucre_maske = maske[y1:y2, x1:x2]
            harf_kutusu = tahta[y1:y2, x1:x2]
            
            ham_harf = "?"
            skor = 0
            
            # 1. AŞAMA: Normal Taş Kontrolü (Baraj %65'ten %10'a düşürüldü)
            if cv2.countNonZero(hucre_maske) > (hucre_maske.size * 0.10):
                ham_harf, skor = en_iyi_eslesmeyi_bul(harf_kutusu, referanslar)
            
            # 2. AŞAMA: YILDIZ İÇİN VİP GEÇİŞ (Görünmezlik Pelerini Çözümü)
            # Eğer sarı maske barajı geçemediyse veya harf bulunamadıysa ("?"), 
            # Bu karede sarı renk içermeyen bir YILDIZ olabilir! Sadece yıldızları ara.
            if ham_harf == "?":
                hg = cv2.cvtColor(harf_kutusu, cv2.COLOR_BGR2GRAY) if len(harf_kutusu.shape) == 3 else harf_kutusu
                hg = cv2.resize(hg, (60, 60))
                
                for k, ref_img in referanslar.items():
                    # Referans isminde yildiz veya yıldız geçiyorsa
                    if "yildiz" in k or "yıldız" in k:
                        res = cv2.matchTemplate(hg, ref_img, cv2.TM_CCOEFF_NORMED)
                        max_val = np.max(res)
                        if max_val > 0.60:  # Yıldız için eşik değeri biraz esnetildi (%60)
                            ham_harf = "yıldız"
                            skor = max_val
                            break

            if ham_harf != "?":
                # 1. Alt çizgiden sonrasını at (oz_1 -> oz, d_turuncu -> d)
                temiz_harf = ham_harf.split("_")[0] if "_" in ham_harf else ham_harf

                # 2. Türkçe Karakter Haritası
                tr_harita = {
                    "oz": "ö", "ch": "ç", "sh": "ş",
                    "ue": "ü", "gh": "ğ", "iu": "ı", 
                    "i": "i", "joker": "*", "yildiz": "yıldız"
                }
                
                final_harf = tr_harita.get(temiz_harf, temiz_harf)
                
                matris[satir][sutun] = final_harf
                satir_metni += f"[{final_harf}]"
                
                renk = (0, 255, 0) if final_harf != "?" else (0, 0, 255)
                cv2.rectangle(kontrol_resmi, (x1, y1), (x2, y2), renk, 2)
                
                # Görsele yazarken büyük harfle yaz
                yazi = f"{final_harf.upper()} {skor:.2f}"
                cv2.putText(kontrol_resmi, yazi, (x1, y2-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,0,255), 1)
            else:
                matris[satir][sutun] = None
                satir_metni += "[ ]"
        
        # Satırları hizalı yazdırmak için :2d kullanıyoruz
        print(f"{satir+1:2d}: {satir_metni}")

    print("\n--- İŞLEM TAMAMLANDI ---")
    
    # Sunucu modunda olduğumuz için imshow kapatılabilir veya hata vermesin diye try-except konabilir
    try:
        kontrol_resmi = cv2.resize(kontrol_resmi, (0,0), fx=0.8, fy=0.8)
        # cv2.imshow("Sonuc", kontrol_resmi) # Sunucuda ekran açılmaz, gerekirse yorum satırı yap
        # cv2.waitKey(1)
    except:
        pass
    
    return matris

if __name__ == "__main__":
    tahtayi_oku_final("deneme.jpg")