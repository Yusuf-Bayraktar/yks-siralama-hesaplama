from functools import lru_cache
from pathlib import Path
from scipy.interpolate import PchipInterpolator


import numpy as np
import pandas as pd



# Proje kok dizinini burada sabitliyoruz, main.py neredeyse ona gore
BASE_DIR = Path(__file__).resolve().parent

GECERLI_YILLAR = [2019, 2020, 2021, 2022, 2023, 2024, 2025]  # 2026
GECERLI_PUAN_TURLERI = ["TYT", "SAY"]  # , "EA", "SOZ"]


TYT_DERSLER = ["turkce", "sosyal_bilimler", "temel_matematik", "fen_bilimleri"]
SAY_DERSLER = ["matematik", "fizik", "kimya", "biyoloji"]
# EA_DERSLER = ["edebiyat", "tarih_1", "cografya_1", "matematik"]
# SOZEL_DERSLER = ["edebiyat", "tarih_1", "cografya_1", "tarih_2", "cografya_2", "felsefe", "din"]



def net_hesapla(dogru: int, yanlis: int) -> float:
    return dogru - yanlis / 4


def ham_puan_hesapla(netler: dict, katsayilar: dict):
    """
    netler: ders -> net sayisi
    katsayilar: ders -> katsayi
    """
    ham_puan = katsayilar["baslangic_puani"] + sum(netler[ders] * katsayilar[ders] for ders in netler)
    return ham_puan


def yerlestirme_puani_hesapla(ham_puan: float, obp: float) -> float:
    """
    obp: 0-100 araliginda ise diploma notu kabul edilir (x0.6),
         100-500 araliginda ise dogrudan OBP kabul edilir (x0.12).
         Ikisi matematiksel olarak ayni sonucu verir: OBP = diploma_notu * 5
    """
    if obp > 100 and obp <= 500:
        return ham_puan + obp * 0.12
    elif obp >= 0 and obp <= 100:
        return ham_puan + obp * 0.6
    else:
        raise ValueError(f"OBP degeri gecersiz: {obp}")



@lru_cache(maxsize=64)
def _pchip_olustur(puan_alt: tuple, sayi: tuple) -> PchipInterpolator:
    """
    PCHIP interpolatoru kurmak (kubik fit) veri boyutu kucuk olsa da
    (~20-30 satir) her Streamlit rerun'unda (her tus vuruşunda) sifirdan
    tekrar tekrar kurmak yerine, ayni (puan_alt, sayi) cifti icin bir kere
    kurup onbelleklemek daha temiz. tuple kullanmamizin sebebi: lru_cache
    hashlenebilir argumanlar ister, DataFrame/np.array hashlenemez.
    """
    return PchipInterpolator(np.array(puan_alt), np.array(sayi))


def siralama_tahmin(puan: float, yiginsal_df: pd.DataFrame, puan_turu: str) -> int:
    """
    puan: kisinin puani (ham puan icin sinav_yiginsal, yerlestirme puani icin
          yerlestirme_yiginsal tablosunu kullan - ikisi ayri!)
    yiginsal_df: yukle_yiginsal(yil, tip) ciktisi (puan_alt'e gore kucukten
                 buyuge sirali olmali - yukle_yiginsal zaten bunu yapiyor)
    puan_turu: 'TYT', 'SAY', 'EA', 'SOZ' -> kolon adi

    NOT: Duz np.interp yerine PCHIP (monoton kubik) interpolasyon kullaniyoruz.
    Gercek ÖSYM verileriyle test edildiginde PCHIP, dogrusal interpolasyona gore
    hatayi ~%1-4'ten ~%0.1-0.5'e dusuruyor - cunku gercek dagilim egrisi bucket'lar
    arasinda duz cizgi degil, kavisli; PCHIP bu kavisi yakalarken monoton azalan
    yapiyi da bozmuyor (asiri sapma/overshoot yapmiyor).
    """
    puan_alt = yiginsal_df["puan_alt"].to_numpy(dtype=float)
    sayi = yiginsal_df[puan_turu].to_numpy(dtype=float)

    # Sinir disi durumlar: tablonun en ustunden/altindan tasarsa
    if puan >= puan_alt[-1]:
        return int(sayi[-1])
    if puan <= puan_alt[0]:
        return int(sayi[0])

    interpolator = _pchip_olustur(tuple(puan_alt), tuple(sayi))
    tahmini_sira = float(interpolator(puan))
    return int(round(tahmini_sira))


def toplam_aday_getir(yiginsal_df: pd.DataFrame, puan_turu: str) -> int:
    """
    Bir puan turunde toplam gecerli aday sayisi = yiginsal tablodaki en
    yuksek kumulatif sayi (en dusuk puan_alt satiri). aday_sayilari.csv'ye
    gerek kalmadan dogrudan yiginsal veriden cikarilabilir.
    """
    return int(yiginsal_df[puan_turu].max())


def sonuclari_nete_cevir(sonuclar: dict) -> dict:
    """
    Sonuclari net sayisina cevirir.
    """
    return {ders: net_hesapla(sonuclar[ders]["dogru"], sonuclar[ders]["yanlis"]) for ders in sonuclar}


def yuzdelik_dilim_hesapla(siralama: int, toplam_aday: int) -> float:
    """
    Adaylarin yuzde kacindan daha iyi oldugunu doner (0-100).
    siralama kucuk = iyi, o yuzden 100'den cikariyoruz.
    """
    return round((1 - siralama / toplam_aday) * 100, 3)


# @st.cache_data
def yukle_test_istatistikleri(yil: int) -> pd.DataFrame:
    """
    Ilgili yilin test bazli ortalama/std degerlerini doner.
    Kolonlar: year, oturum, test, soru_sayisi, son_sinif_aday,
              son_sinif_ortalama, son_sinif_std, tum_aday,
              tum_ortalama, tum_std
    """
    path = BASE_DIR / "data" / "test_istatistikleri" / f"{yil}_test_istatistikleri.csv"
    if not path.exists():
        raise FileNotFoundError(f"Test istatistikleri bulunamadi: {path}")
    return pd.read_csv(path)


# @st.cache_data
def yukle_katsayi(puan_turu: str) -> pd.DataFrame:
    """
    puan_turu: 'TYT' veya 'SAY' (ileride 'EA' / 'SOZ' eklenecek)
    Donen DataFrame'de index = ders adi, kolonlar = yillar.
    """
    dosya_adi = {
        "TYT": "tyt_katsayi_puan.csv",
        "SAY": "say_katsayi_puan.csv",
        # "EA": "ea_katsayi_puan.csv",   -> eklenince ac
        # "SOZ": "soz_katsayi_puan.csv", -> eklenince ac
    }
    if puan_turu not in dosya_adi:
        raise ValueError(f"Bilinmeyen puan turu: {puan_turu}")
 
    path = BASE_DIR / "data" / dosya_adi[puan_turu]
    if not path.exists():
        raise FileNotFoundError(f"Katsayi dosyasi bulunamadi: {path}")
 
    df = pd.read_csv(path)
    return df.set_index("ders")


# @st.cache_data
def yukle_yiginsal(yil: int, tip: str) -> pd.DataFrame:
    """
    tip: 'sinav' veya 'yerlestirme'
    Kolonlar: year, puan_alt, TYT, SAY (bazi yillarda EA, SOZ da olabilir)
    Kumulatif dagilim: puan_alt azaldikca sayilar artar.
    """
    klasor = {
        "sinav": "sinav_puani_yiginsal",
        "yerlestirme": "yerlestirme_puani_yiginsal",
    }
    if tip not in klasor:
        raise ValueError(f"Bilinmeyen tip: {tip}")
 
    path = BASE_DIR / "data" / klasor[tip] / f"{yil}_{tip}_puani_yiginsal.csv"
    if not path.exists():
        raise FileNotFoundError(f"Yiginsal veri bulunamadi: {path}")
 
    # puan_alt kucukten buyuge siralanmis olsun, interpolasyon icin lazim
    return pd.read_csv(path).sort_values("puan_alt").reset_index(drop=True)


# @st.cache_data
def yukle_aday_sayilari(yil: int) -> pd.DataFrame:
    """
    Kolonlar: year, oturum, basvuran, giren, girmeyen, gecersiz, gecerli
    """
    path = BASE_DIR / "data" / "aday_sayilari" / f"{yil}_aday_sayilari.csv"
    if not path.exists():
        raise FileNotFoundError(f"Aday sayilari bulunamadi: {path}")
    return pd.read_csv(path)


def yukle_yil_verisi(yil: int, puan_turu: str) -> dict:
    """
    Bir yil + puan turu icin hesaplamada ihtiyac duyulan her seyi
    tek seferde toplayip doner. main.py bunu cache_data ile sarmalayip
    cagiracak.
    """
    return {
        # "test_istatistikleri": yukle_test_istatistikleri(yil),  # hesaplama için gerek yok
        "katsayilar": yukle_katsayi("TYT" if puan_turu == "TYT" else puan_turu),
        "tyt_katsayilari": yukle_katsayi("TYT"),  # SAY/EA/SOZ hesaplarken TYT testleri de lazim
        "sinav_yiginsal": yukle_yiginsal(yil, "sinav"),
        "yerlestirme_yiginsal": yukle_yiginsal(yil, "yerlestirme"),
        "aday_sayilari": yukle_aday_sayilari(yil),   # hesaplama için gerek yok
    }



def sıralama_ve_puan_hesapla(sonuclar: dict, data: dict, yil: int, puan_turu: str, obp: float):
    """
    sonuclar: ders -> {"dogru": int, "yanlis": int}  (TYT + AYT dersleri birlikte)
    data: yukle_yil_verisi(yil, puan_turu) ciktisi (main.py'da onceden/cache'li yuklenip verilir)
    yil: katsayi tablosundaki dogru yil kolonunu secmek icin
    puan_turu: "TYT" veya "SAY"  # EA ve SOZEL eklenecek
    obp: 0-100 (diploma notu) veya 100-500 (dogrudan OBP)
 
    NOT: Bu fonksiyon artik veriyi kendi yuklemiyor - disk erisimi/caching
    main.py'nin sorumlulugunda, calculator.py saf hesaplama katmani olarak kaliyor.
    """
    netler = sonuclari_nete_cevir(sonuclar)
    netler_tyt = {ders: netler[ders] for ders in TYT_DERSLER}
 
    ham_puan_tyt = ham_puan_hesapla(netler_tyt, data["tyt_katsayilari"].to_dict()[f"{yil}"])
    ham_puan_puan_turu = ham_puan_hesapla(netler, data["katsayilar"].to_dict()[f"{yil}"])
 
    yerlestirme_puani_tyt = yerlestirme_puani_hesapla(ham_puan_tyt, obp=obp)
    yerlestirme_puani_puan_turu = yerlestirme_puani_hesapla(ham_puan_puan_turu, obp=obp)
 
    ham_sira_tyt = siralama_tahmin(ham_puan_tyt, data["sinav_yiginsal"], "TYT")
    ham_sira_puan_turu = siralama_tahmin(ham_puan_puan_turu, data["sinav_yiginsal"], puan_turu)
 
    yerlestirme_sira_tyt = siralama_tahmin(yerlestirme_puani_tyt, data["yerlestirme_yiginsal"], "TYT")
    yerlestirme_sira_puan_turu = siralama_tahmin(yerlestirme_puani_puan_turu, data["yerlestirme_yiginsal"], puan_turu)
 
    toplam_aday_puan_turu = toplam_aday_getir(data["yerlestirme_yiginsal"], puan_turu)
    yuzdelik_dilim_puan_turu = yuzdelik_dilim_hesapla(yerlestirme_sira_puan_turu, toplam_aday_puan_turu)

    return {
        "netler": netler,
        "ham_puan_tyt": ham_puan_tyt,
        "ham_puan": ham_puan_puan_turu,
        "yerlestirme_puani_tyt": yerlestirme_puani_tyt,
        "yerlestirme_puani": yerlestirme_puani_puan_turu,
        "ham_sira_tyt": ham_sira_tyt,
        "ham_sira": ham_sira_puan_turu,
        "yerlestirme_sira_tyt": yerlestirme_sira_tyt,
        "yerlestirme_sira": yerlestirme_sira_puan_turu,
        "yuzdelik_dilim": yuzdelik_dilim_puan_turu,
    }



def main():
    # Örnek Hesaplama
    tyt_sonuclar = {
        "turkce":           {"dogru": 23, "yanlis": 5},
        "sosyal_bilimler":  {"dogru": 16, "yanlis": 4},
        "temel_matematik":  {"dogru": 32, "yanlis": 0},
        "fen_bilimleri":    {"dogru": 20, "yanlis": 0}
    }

    ayt_sonuclar = {
        "matematik":        {"dogru": 39, "yanlis": 1},
        "fizik":            {"dogru": 12, "yanlis": 2},
        "kimya":            {"dogru": 13, "yanlis": 0},
        "biyoloji":         {"dogru": 10, "yanlis": 3}
    }

    tum_sonuclar = {**tyt_sonuclar, **ayt_sonuclar}
    yil = 2025
    obp = 95

    data = yukle_yil_verisi(yil, "SAY")
    sonuc = sıralama_ve_puan_hesapla(tum_sonuclar, data, yil, "SAY", obp)

    for k, v in sonuc.items():
        print(f"{k}: {v}")



if __name__ == "__main__":
    main()