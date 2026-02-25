import cv2
import numpy as np
import os

# --- AYARLAR ---
REFERANS_KLASORU = "referanslar_ham" 

def dosya_oku_gri(dosya_yolu):
    """Referans resimleri için: Dosyayı GRİ okur"""
    try:
        with open(dosya_yolu, "rb") as f:
            bytes_data = bytearray(f.read())
            numpy_array = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_GRAYSCALE)
            return img
    except Exception as e:
        return None

def dosya_oku_renkli(dosya_yolu):
    """Ana resim için: Dosyayı RENKLİ okur"""
    try:
        with open(dosya_yolu, "rb") as f:
            bytes_data = bytearray(f.read())
            numpy_array = np.asarray(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(numpy_array, cv2.IMREAD_COLOR)
            return img
    except Exception as e:
        return None

def referanslari_yukle():
    referanslar = {}
    if not os.path.exists(REFERANS_KLASORU):
        # Render sunucusunda klasör yolu farklı olabilir, kontrol edelim
        if os.path.exists(f"backend/{REFERANS_KLASORU}"):
             yol_prefix = f"backend/{REFERANS_KLASORU}"
        else:
             yol_prefix = REFERANS_KLASORU
    else:
        yol_prefix = REFERANS_KLASORU

    if not os.path.exists(yol_prefix):
         return {}

    dosyalar = os.listdir(yol_prefix)
    
    for dosya in dosyalar:
        if dosya.endswith(".png") or dosya.endswith(".jpg"):
            harf_adi = os.path.splitext(dosya)[0].lower()
            yol = os.path.join(yol_prefix, dosya)
            img = dosya_oku_gri(yol)
            if img is not None:
                img = cv2.resize(img, (60, 60))
                referanslar[harf_adi] = img
    return referanslar

def en_iyi_eslesmeyi_bul(hucre_resmi, referanslar):
    en_iyi_skor = -1
    en_iyi_harf = "?"
    
    if len(hucre_resmi.shape) == 3:
        hucre_gri = cv2.cvtColor(hucre_resmi, cv2.COLOR_BGR2GRAY)
    else:
        hucre_gri = hucre_resmi
        
    hucre_gri = cv2.resize(hucre_gri, (60, 60))

    for harf, ref_resim in referanslar.items():
        sonuc = cv2.matchTemplate(hucre_gri, ref_resim, cv2.TM_CCOEFF_NORMED)
        skor = np.max(sonuc)
        if skor > en_iyi_skor:
            en_iyi_skor = skor
            en_iyi_harf = harf

    if en_iyi_skor > 0.65: # Barajı biraz esnettik
        return en_iyi_harf, en_iyi_skor
    else:
        return "?", en_iyi_skor

# --- EKSİK OLAN FONKSİYON EKLENDİ ---
def eldeki_harfleri_oku(img_giris):
    """Eldeki harfleri (Rack) okur"""
    referanslar = referanslari_yukle()
    if not referanslar: return ""

    # Giriş kontrolü (Dosya yolu mu, resim mi?)
    if isinstance(img_giris, str):
        img = dosya_oku_renkli(img_giris)
    else:
        img = img_giris

    if img is None: return ""

    h, w, _ = img.shape
    
    # Kelimelik'te el (rack) genelde en alttadır.
    # Ekranın alt %15'lik kısmını alıyoruz.
    y_bas = int(h * 0.85)
    el_resmi = img[y_bas:h, 0:w]
    
    eh, ew, _ = el_resmi.shape
    slot_w = ew / 7.0 # Elde 7 harf yeri var

    okunan_harfler = ""
    tr_harita = {
        "oz": "ö", "ch": "ç", "sh": "ş",
        "ue": "ü", "gh": "ğ", "iu": "ı", 
        "i": "i", "joker": "*", "yildiz": "*"
    }

    for i in range(7):
        x1 = int(i * slot_w)
        x2 = int((i + 1) * slot_w)
        # Kenarlardan biraz kırp (parazit engellemek için)
        margin = int(slot_w * 0.1)
        hucre = el_resmi[0:eh, x1+margin:x2-margin]
        
        # Boş mu dolu mu kontrolü
        hsv = cv2.cvtColor(hucre, cv2.COLOR_BGR2HSV)
        # Beyaz taş veya Sarı taş rengi var mı?
        maske = cv2.inRange(hsv, np.array([0, 0, 100]), np.array([180, 50, 255]))
        
        if cv2.countNonZero(maske) > (hucre.size * 0.05):
            harf, skor = en_iyi_eslesmeyi_bul(hucre, referanslar)
            if harf != "?":
                temiz_harf = harf.split("_")[0] if "_" in harf else harf
                final_harf = tr_harita.get(temiz_harf, temiz_harf)
                okunan_harfler += final_harf.upper()
    
    return okunan_harfler

# --- İSMİ DÜZELTİLDİ VE PARAMETRE AYARLANDI ---
def tahtayi_oku(veri_giris):
    """
    Hem dosya yolu (str) hem de OpenCV resmi (numpy) kabul eder.
    main.py ile uyumlu olması için 2 değer döndürür: (matris, görsel)
    """
    referanslar = referanslari_yukle()
    if not referanslar: return [], None

    # 1. GİRİŞ KONTROLÜ (String mi Resim mi?)
    if isinstance(veri_giris, str):
        img = dosya_oku_renkli(veri_giris)
    else:
        img = veri_giris # Zaten resim gelmiş

    if img is None: 
        print("Ana resim okunamadı!")
        return [], None

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
    
    kontrol_resmi = tahta.copy()
    matris = [[None for _ in range(15)] for _ in range(15)]
    
    tr_harita = {
        "oz": "ö", "ch": "ç", "sh": "ş",
        "ue": "ü", "gh": "ğ", "iu": "ı", 
        "i": "i", "joker": "*", "yildiz": "yıldız"
    }

    for satir in range(15):
        for sutun in range(15):
            y1 = int(satir * hucre_h)
            y2 = int((satir + 1) * hucre_h)
            x1 = int(sutun * hucre_w)
            x2 = int((sutun + 1) * hucre_w)

            hucre_maske = maske[y1:y2, x1:x2]
            harf_kutusu = tahta[y1:y2, x1:x2]
            
            ham_harf = "?"
            skor = 0
            
            # 1. AŞAMA: Normal Taş Kontrolü
            if cv2.countNonZero(hucre_maske) > (hucre_maske.size * 0.10):
                ham_harf, skor = en_iyi_eslesmeyi_bul(harf_kutusu, referanslar)
            
            # 2. AŞAMA: YILDIZ KONTROLÜ
            if ham_harf == "?":
                hg = cv2.cvtColor(harf_kutusu, cv2.COLOR_BGR2GRAY) if len(harf_kutusu.shape) == 3 else harf_kutusu
                hg = cv2.resize(hg, (60, 60))
                for k, ref_img in referanslar.items():
                    if "yildiz" in k or "yıldız" in k:
                        res = cv2.matchTemplate(hg, ref_img, cv2.TM_CCOEFF_NORMED)
                        if np.max(res) > 0.60:
                            ham_harf = "yıldız"
                            skor = np.max(res)
                            break

            if ham_harf != "?":
                temiz_harf = ham_harf.split("_")[0] if "_" in ham_harf else ham_harf
                final_harf = tr_harita.get(temiz_harf, temiz_harf)
                
                matris[satir][sutun] = final_harf
            else:
                matris[satir][sutun] = None
                
    # DÖNÜŞ DEĞERİ DÜZELTİLDİ: (matris, resim)
    return matris, kontrol_resmi

if __name__ == "__main__":
    # Test bloğu
    tahtayi_oku("deneme.jpg")