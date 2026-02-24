import cv2
import os

# --- AYARLAR ---
DOSYA_ADI = "d1.jpg"
CIKTI_KLASORU = "ham_harfler"

# Resmi Oku
img = cv2.imread(DOSYA_ADI)
if img is None:
    print(f"❌ HATA: {DOSYA_ADI} bulunamadı! Lütfen backend klasörüne atın.")
    exit()

h, w, _ = img.shape
print(f"📸 Resim Boyutu: {w}x{h}")

# Klasörü oluştur
if not os.path.exists(CIKTI_KLASORU):
    os.makedirs(CIKTI_KLASORU)

# --- TAHTA GEOMETRİSİ ---
tahta_bas_y = int(h * 0.292)
tahta_boy = w 
hucre_boy = tahta_boy / 15

print("🚀 Tahta kesiliyor, GRİ yapılıyor ve 30x30'a küçültülüyor...")

sayac = 0
for satir in range(15):
    for sutun in range(15):
        # Koordinat hesabı
        y = int(tahta_bas_y + (satir * hucre_boy))
        x = int(sutun * hucre_boy)
        
        # Kareyi kes
        crop = img[y:y+int(hucre_boy), x:x+int(hucre_boy)]
        
        # 1. GRİYE ÇEVİR
        gri_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        # 2. BOYUTU KÜÇÜLT (30x30 Standart)
        # Bu sayede eski ve yeni referanslar uyumlu olur
        kucuk_crop = cv2.resize(gri_crop, (60, 60))
        
        # Kaydet
        hedef = f"{CIKTI_KLASORU}/{satir+1}_{sutun+1}.jpg"
        cv2.imwrite(hedef, kucuk_crop)
        sayac += 1

print(f"✅ İşlem Tamam! '{CIKTI_KLASORU}' klasörüne {sayac} adet 30x30 GRİ kare kaydedildi.")
print("👉 Şimdi ayıklama işlemine başlayabilirsin!")