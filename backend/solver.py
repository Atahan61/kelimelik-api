import os
import time
from collections import Counter
import copy

# --- AYARLAR ---
HARF_PUANLARI = {
    'a': 1, 'b': 3, 'c': 4, 'ç': 4, 'd': 3, 'e': 1, 'f': 7, 'g': 5, 
    'ğ': 8, 'h': 5, 'ı': 2, 'i': 1, 'j': 10, 'k': 1, 'l': 1, 'm': 2, 
    'n': 1, 'o': 2, 'ö': 7, 'p': 5, 'r': 1, 's': 2, 'ş': 4, 't': 1, 
    'u': 2, 'ü': 3, 'v': 7, 'y': 3, 'z': 4, '?': 0 
}

# --- KELİMELİK BONUS MATRİSİ (Senin Verdiğin) ---
# 0:Normal, 1:2H, 2:3H, 3:2K, 4:3K
BONUS_MATRISI = [
    [0,0,4,0,0,1,0,0,0,1,0,0,4,0,0],
    [0,2,0,0,0,0,1,0,1,0,0,0,0,2,0],
    [4,0,0,0,0,0,0,3,0,0,0,0,0,0,4],
    [0,0,0,3,0,0,0,0,0,0,0,3,0,0,0],
    [0,0,0,0,2,0,0,0,0,0,2,0,0,0,0],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0],
    [0,0,3,0,0,0,0,0,0,0,0,0,3,0,0], # Orta Satır (7. Satır)
    [0,1,0,0,0,0,1,0,1,0,0,0,0,1,0],
    [1,0,0,0,0,1,0,0,0,1,0,0,0,0,1],
    [0,0,0,0,2,0,0,0,0,0,2,0,0,0,0],
    [0,0,0,3,0,0,0,0,0,0,0,3,0,0,0],
    [4,0,0,0,0,0,0,3,0,0,0,0,0,0,4],
    [0,2,0,0,0,0,1,0,1,0,0,0,0,2,0],
    [0,0,4,0,0,1,0,0,0,1,0,0,4,0,0]
]

def turkce_kucult(kelime):
    if not kelime: return ""
    return kelime.replace("İ", "i").replace("I", "ı").lower()

class TrieNode:
    def __init__(self):
        self.cocuklar = {}
        self.kelime_sonu = False

class KelimeAgaci:
    def __init__(self):
        self.kok = TrieNode()
        self.kelime_sayisi = 0

    def kelime_ekle(self, kelime):
        node = self.kok
        for harf in kelime:
            if harf not in node.cocuklar:
                node.cocuklar[harf] = TrieNode()
            node = node.cocuklar[harf]
        node.kelime_sonu = True
        self.kelime_sayisi += 1

    def veriyi_yukle(self, dosya_yolu):
        print(f"--- Sözlük Yükleniyor: {dosya_yolu} ---")
        if not os.path.exists(dosya_yolu):
            print("!!! HATA: Sözlük dosyası bulunamadı !!!")
            return False

        # KELİMELİK RESMİ 2 HARFLİ KELİMELER LİSTESİ
        GECERLI_IKILILER = {
            "ab","aç","ad","af","ağ","ah","ak","al","am","an","ar","as","aş","at","av","ay","az",
            "be","bu","ce","çe","de","do","dü","eh","ek","el","em","en","er","es","eş","et","ev","ey",
            "fa","fe","ge","go","ha","he","hu","ıh","ır","ıs","iç","id","iğ","il","im","in","ip","is","iş","it","iz","je",
            "ke","ki","la","le","me","mi","mö","ne","nü","od","of","oh","ok","ol","om","on","ot","oy",
            "öç","öd","öf","ök","ön","öz","pe","pi","ra","re","se","si","su","sü","şe","şu","ta","te","ti","tu",
            "uç","uf","un","ur","us","ut","uz","uy","üç","ün","üf","üs","ve","ya","ye","yo","ze"
        }

        t0 = time.time()
        try:
            with open(dosya_yolu, "r", encoding="utf-8") as f:
                for satir in f:
                    ham = satir.strip()
                    
                    # 1. Boşluk içerenleri veya tek harflileri atla
                    if " " in ham or len(ham) < 2: continue
                    
                    # 2. Özel isimleri ve kısaltmaları atla (Eğer sözlükte baş harfi büyükse)
                    if ham[0].isupper() or ham[0] in "ÇĞİÖŞÜ":
                        continue
                        
                    kucuk_kelime = turkce_kucult(ham)
                    
                    # 3. GÜMRÜK KONTROLÜ: 2 harfliyse ve resmi listede yoksa ÇÖPE AT! (ag, ga, vb.)
                    if len(kucuk_kelime) == 2 and kucuk_kelime not in GECERLI_IKILILER:
                        continue
                        
                    self.kelime_ekle(kucuk_kelime)
                    
            print(f"Sözlük Hazır. {self.kelime_sayisi} kelime yüklendi. ({time.time()-t0:.2f}sn)")
            return True
        except Exception as e:
            print(f"Sözlük okuma hatası: {e}")
            return False

    def kelime_var_mi(self, kelime):
        node = self.kok
        for harf in kelime:
            if harf not in node.cocuklar:
                return False
            node = node.cocuklar[harf]
        return node.kelime_sonu

    # --- ANA HESAPLAMA MOTORU ---
    def hamle_bul(self, tahta_matris_orj, el_harfleri):
        baslangic = time.time()
        print(f"Hamle hesaplanıyor... El: {el_harfleri}")
        
        # --- 1. MATRİSİ KOPYALA VE YILDIZI BUL ---
        # Orjinal matrisi bozmuyoruz ki API'ye giden çıktı görseli bozulmasın
        tahta_matris = copy.deepcopy(tahta_matris_orj)
        self.yildiz_coord = None
        
        for r in range(len(tahta_matris)):
            for c in range(len(tahta_matris[r])):
                # Eğer hücrede yıldız yazıyorsa koordinatını kaydet ve yolu aç!
                if tahta_matris[r][c] and str(tahta_matris[r][c]).lower() == "yıldız":
                    self.yildiz_coord = (r, c)
                    tahta_matris[r][c] = None  # Çözücü onu taş sanıp yolu kapatmasın!
        
        hamleler = []
        
        # 1. YATAY HAMLELERİ ARA
        hamleler.extend(self._yonlu_arama(tahta_matris, el_harfleri, yon="Yatay"))
        
        # 2. DİKEY HAMLELERİ ARA (Tahtayı transpoze et)
        tahta_dikey = [list(x) for x in zip(*tahta_matris)]
        dikey_hamleler = self._yonlu_arama(tahta_dikey, el_harfleri, yon="Dikey")
        
        # Dikey hamlelerin koordinatlarını düzelt (r, c -> c, r)
        for h in dikey_hamleler:
            r, c = h['baslangic']
            h['baslangic'] = (c, r)
            hamleler.append(h)

        # 3. PUANA GÖRE SIRALA (En yüksek en üstte)
        hamleler.sort(key=lambda x: x['puan'], reverse=True)

        if self.yildiz_coord:
            yr, yc = self.yildiz_coord
            tahta_matris[yr][yc] = "yıldız"
        
        print(f"Hesaplama Bitti: {len(hamleler)} hamle bulundu. ({time.time()-baslangic:.2f}sn)")
        return hamleler

    def _yonlu_arama(self, tahta, el, yon):
        bulunanlar = []
        el_sayaci = Counter(el)
        
        rows = len(tahta)
        cols = len(tahta[0])

        # Tahta tamamen boş mu? (İlk hamle kuralı için)
        tahta_bos = all(all(cell is None for cell in row) for row in tahta)

        for r in range(rows):
            satir = tahta[r]
            
            # Eğer satır tamamen boşsa ve tahta doluysa, 
            # sadece üstünde/altında harf olan sütunlara bakmalıyız (Performans için).
            # Şimdilik "Satır Çözücü" hepsine bakıyor.
            
            olasi_yerlesimler = self._satir_coz(satir, el_sayaci)
            
            for kelime, c_bas, joker_kullanimlari in olasi_yerlesimler:
                # 1. ÇAPRAZ KONTROL (Geçerlilik)
                gecerli, yan_puan = self._capraz_kontrol(tahta, r, c_bas, kelime, yon)
                
                if gecerli:
                    # 2. İLK HAMLE KONTROLÜ (7,7 Merkezden geçmeli)
                    if tahta_bos:
                        c_bitis = c_bas + len(kelime) - 1
                        if not (c_bas <= 7 <= c_bitis and r == 7):
                            continue 

                    # 3. BAĞLANTI KONTROLÜ (Tahta doluysa bir yere değmeli)
                    if not tahta_bos:
                        if not self._baglanti_var_mi(satir, c_bas, kelime, yan_puan > 0):
                            continue

                    # 4. PUAN HESAPLA
                    ana_puan = self._puan_hesapla(r, c_bas, kelime, yon, joker_kullanimlari, tahta)
                    toplam_puan = ana_puan + yan_puan
                    
                    bulunanlar.append({
                        'kelime': kelime,
                        'puan': toplam_puan,
                        'baslangic': (r, c_bas),
                        'yon': yon,
                        'jokerler': joker_kullanimlari
                    })
        
        return bulunanlar

    def _satir_coz(self, satir, el_sayaci):
        """
        Bir satırdaki boşluklara elimizdeki harfleri yerleştirerek
        sözlükte olan kelimeleri bulur.
        """
        sonuclar = []
        cols = len(satir)
        
        # Her sütunu potansiyel başlangıç noktası olarak dene
        for c in range(cols):
            # Eğer solumda harf varsa, ben kelime başlangıcı olamam (bitişiklik kuralı)
            if c > 0 and satir[c-1] is not None:
                continue
                
            self._recursive_find(self.kok, satir, c, el_sayaci, [], [], sonuclar, c, False)
            
        return sonuclar

    def _recursive_find(self, node, satir, index, el, mevcut, jokerler, sonuclar, bas_c, harf_koyduk):
        # Kelime bitti mi? (Sözlükte var mı?)
        if node.kelime_sonu:
            # Bitişiklik kontrolü: Kelimeden hemen sonra harf gelmemeli (Sağ taraf boş olmalı)
            valid_end = True
            if index < len(satir) and satir[index] is not None:
                valid_end = False
            
            # En az 1 harf koyduysak (veya mevcut kelimeyi uzattıysak) kaydet
            if valid_end and harf_koyduk:
                sonuclar.append(("".join(mevcut), bas_c, list(jokerler)))

        # Sınır kontrolü
        if index >= len(satir):
            return

        hucre = satir[index]

        if hucre is not None:
            # Tahtada harf var, uymak zorundayız
            if hucre in node.cocuklar:
                self._recursive_find(node.cocuklar[hucre], satir, index+1, el, mevcut + [hucre], jokerler, sonuclar, bas_c, harf_koyduk)
        else:
            # Boşluk, elden koyabiliriz
            # Optimizasyon: Sadece Trie'de gidebileceğimiz yolları dene
            possible_chars = set(el.keys())
            
            for harf in possible_chars:
                if el[harf] > 0:
                    if harf == '*': # Joker
                         # Joker ise, Trie'de o an gidilebilecek TÜM harfleri dene
                         for k in node.cocuklar:
                             el['*'] -= 1
                             # Joker olduğunu belirtmek için index'i kaydet
                             self._recursive_find(node.cocuklar[k], satir, index+1, el, mevcut + [k], jokerler + [index], sonuclar, bas_c, True)
                             el['*'] += 1
                    else:
                        # Normal harf
                        if harf in node.cocuklar:
                            el[harf] -= 1
                            self._recursive_find(node.cocuklar[harf], satir, index+1, el, mevcut + [harf], jokerler, sonuclar, bas_c, True)
                            el[harf] += 1

    def _capraz_kontrol(self, tahta, r, c_bas, kelime, yon):
        """
        Yeni koyduğumuz harflerin oluşturduğu dikey kelimeleri (yan kelimeleri) kontrol eder.
        """
        toplam_yan_puan = 0
        rows = len(tahta)
        
        for i, harf in enumerate(kelime):
            c_curr = c_bas + i
            
            # Bu kare tahtada zaten dolu muydu? Doluysa atla.
            if tahta[r][c_curr] is not None:
                continue 

            # Bu boş kareye harf koyduk. Yukarıda veya aşağıda komşu var mı?
            ust_var = (r > 0 and tahta[r-1][c_curr] is not None)
            alt_var = (r < rows-1 and tahta[r+1][c_curr] is not None)
            
            if ust_var or alt_var:
                # Yukarı git başı bul
                r_start = r
                while r_start > 0 and tahta[r_start-1][c_curr] is not None:
                    r_start -= 1
                
                # Aşağı git sonu bul
                r_end = r
                while r_end < rows-1 and tahta[r_end+1][c_curr] is not None:
                    r_end += 1
                
                # Yan kelimeyi oluştur
                yan_kelime = ""
                yan_puan_temp = 0
                
                for k in range(r_start, r_end + 1):
                    if k == r:
                        okunan = harf # Bizim koyduğumuz
                        # Yan kelimede de bonus geçerlidir!
                        # Bonus hesaplamak için orijinal koordinat lazım.
                        # Eğer 'yon' Yatay ise koordinat (r, c_curr)
                        # Eğer 'yon' Dikey ise koordinat (c_curr, r) -> çünkü tahta transpoze geldi
                        real_r, real_c = (r, c_curr) if yon == "Yatay" else (c_curr, r)
                        
                        bonus = BONUS_MATRISI[real_r][real_c]
                        
                        h_carpani = 1
                        if bonus == 1: h_carpani = 2
                        if bonus == 2: h_carpani = 3
                        
                        k_carpani = 1
                        if bonus == 3: k_carpani = 2
                        if bonus == 4: k_carpani = 3
                        
                        yan_puan_temp += (HARF_PUANLARI.get(okunan, 0) * h_carpani)
                        # Not: Kelime çarpanını (k_carpani) yan_puan_temp'e en son uygulayacağız
                        
                    else:
                        okunan = tahta[k][c_curr]
                        yan_puan_temp += HARF_PUANLARI.get(okunan, 0)
                    
                    yan_kelime += okunan
                
                # Oluşan yan kelime sözlükte var mı?
                if not self.kelime_var_mi(yan_kelime):
                    return False, 0 # Geçersiz hamle!
                
                # Yan kelime çarpanını şimdi uygula (Bizim koyduğumuz karedeki bonus tüm kelimeyi çarpar)
                real_r, real_c = (r, c_curr) if yon == "Yatay" else (c_curr, r)
                bonus = BONUS_MATRISI[real_r][real_c]
                if bonus == 3: yan_puan_temp *= 2
                if bonus == 4: yan_puan_temp *= 3
                
                toplam_yan_puan += yan_puan_temp

        return True, toplam_yan_puan

    def _baglanti_var_mi(self, satir, c_bas, kelime, yan_baglanti_var):
        # 1. Kesişim var mı? (Mevcut taşın üstünden geçtik mi?)
        for i, harf in enumerate(kelime):
            if satir[c_bas + i] is not None:
                return True 
        
        # 2. Uca ekleme var mı?
        c_bitis = c_bas + len(kelime)
        if c_bas > 0 and satir[c_bas - 1] is not None: return True
        if c_bitis < len(satir) and satir[c_bitis] is not None: return True
        
        # 3. Dikey bağlantı var mı?
        if yan_baglanti_var: return True
        
        return False

    def _puan_hesapla(self, r, c, kelime, yon, joker_indices, tahta):
        puan = 0
        kelime_carpani = 1
        kullanilan_tas_sayisi = 0
        yildiz_bonusu = 0  # <--- YENİ: 3 Yıldız (+25) Bonusu
        
        for i, harf in enumerate(kelime):
            curr_c = c + i
            real_r, real_c = (r, curr_c) if yon == "Yatay" else (curr_c, r)
            
            # Joker puanı her zaman 0'dır
            harf_puani = 0 if (c + i) in joker_indices else HARF_PUANLARI.get(harf, 0)
            h_carpani = 1
            
            # Matrisin kendi ekseninde boş mu kontrolü
            if tahta[r][curr_c] is None or tahta[r][curr_c] == "?":
                kullanilan_tas_sayisi += 1
                
                # Standart harf ve kelime katları
                bonus = BONUS_MATRISI[real_r][real_c]
                if bonus == 1: h_carpani = 2
                if bonus == 2: h_carpani = 3
                if bonus == 3: kelime_carpani *= 2
                if bonus == 4: kelime_carpani *= 3
                
                # --- YENİ: Eğer taşı tam da 3 Yıldızın üstüne koyduysak ---
                if self.yildiz_coord == (real_r, real_c):
                    yildiz_bonusu = 25
            
            puan += harf_puani * h_carpani
            
        toplam_puan = (puan * kelime_carpani) + yildiz_bonusu
        
        # Tombala (+30 Puan) Kuralı
        if kullanilan_tas_sayisi == 7:
            toplam_puan += 30
            
        return toplam_puan

# --- ORİJİNAL MOTOR BAŞLATMA ---
motor = KelimeAgaci()

# Sözlük dosyasını otomatik bul ve garanti altına al
import os
_aranan_sozlukler = ["sozluk.txt", "kelimeler.txt", "turkce_kelimeler.txt"]
_sozluk_yuklendi = False

# Render'da klasör yapıları değişebileceği için tüm ihtimalleri tarıyoruz
for klasor in ["", "backend/", "../"]:
    for dosya in _aranan_sozlukler:
        yol = os.path.join(klasor, dosya)
        if os.path.exists(yol):
            print(f"Sözlük bulundu: {yol}")
            basari = motor.veriyi_yukle(yol)
            if basari:
                _sozluk_yuklendi = True
                break
    if _sozluk_yuklendi:
        break

if not _sozluk_yuklendi:
    print("!!! KRİTİK HATA: SÖZLÜK DOSYASI BULUNAMADI, KELİME ÜRETİLEMEZ !!!")