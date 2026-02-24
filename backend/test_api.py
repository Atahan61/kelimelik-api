import requests

DOSYA_YOLU = "d1.jpg"  # Test etmek istediğin resim
URL = "http://127.0.0.1:8000/resim-coz"

print(f"📡 İstek gönderiliyor: {DOSYA_YOLU}...\n")

with open(DOSYA_YOLU, "rb") as f:
    dosyalar = {"file": (DOSYA_YOLU, f, "image/jpeg")}
    cevap = requests.post(URL, files=dosyalar)

if cevap.status_code == 200:
    veri = cevap.json()
    el_harfleri = veri.get("el_harfleri", [])
    tahta_durumu = veri.get("tahta_durumu", [])
    oneriler = veri.get("onerilen_kelimeler", [])
    
    print("========================================")
    print("✅ SUNUCU CEVABI BAŞARILI!")
    print("========================================")
    
    # --- YENİ EKLENEN KISIM: TAHTA MATRİSİ ---
    print("\n🟩 TAHTA DURUMU (Matris):")
    if tahta_durumu:
        for i, satir in enumerate(tahta_durumu):
            satir_gorsel = ""
            for hucre in satir:
                # Hücre doluysa harfi yaz, boşsa veya ? ise [ ] bırak
                if hucre and hucre != "?":
                    satir_gorsel += f"[{hucre.lower()}]"
                else:
                    satir_gorsel += "[ ]"
            
            # Satır numaralarını (1-15) hizalı yazdırmak için :2d kullanıyoruz
            print(f"{i + 1:2d}: {satir_gorsel}")
    else:
        print("Tahta verisi alınamadı veya boş.")

    # --- ELDEKİ HARFLER ---
    print("\n🖐️ ELDEKİ HARFLER (Slot Doğrulaması):")
    for index, harf in enumerate(el_harfleri):
        gorunen_harf = harf.lower() if harf else "?"
        print(f"   👉 Slot {index + 1}: {gorunen_harf}")
        
    # --- ÖNERİLEN HAMLELER ---
    print("\n🏆 ÖNERİLEN HAMLELER (İlk 5):")
    if oneriler:
        for i, hamle in enumerate(oneriler[:5]):
            # Önce Türkçe "i" ve "ı" dönüşümünü manuel yapıyoruz, sonra .upper() uyguluyoruz
            kelime_gorsel = hamle['kelime'].replace("i", "İ").replace("ı", "I").upper()
            print(f"{i+1}. {kelime_gorsel} ({hamle['puan']} P) -> {hamle['yon']} {hamle['baslangic']}")
    else:
        print("❌ Hiç hamle bulunamadı.")
else:
    print(f"❌ Sunucu Hatası: {cevap.status_code}")
    print(cevap.text)