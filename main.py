import streamlit as st
import calculator as calc


YIL_KEY = "select_year"
ALAN_KEY = "alan_secim"
YEARS = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]


def guvenli_net_oku(dogru_key: str, yanlis_key: str, max_soru: int) -> tuple[int, int]:
    """
    Streamlit'in number_input min/max dogrulamasi guvenilir degil (bilinen bir
    Streamlit sinirlamasi: https://github.com/streamlit/streamlit/issues/867) -
    hem +/- butonlari hem klavye girisi bazen sinir disi ham degeri
    session_state'e gecirebiliyor, ustelik on_change callback'i degeri
    duzeltse bile ekrandaki kutu bunu her zaman yansitmayabiliyor.

    Bu yuzden GIRISTE duzeltmeye guvenmek yerine, HESAPLAMADAN hemen once
    burada tekrar dogruluyoruz - ekran gecici olarak yanlis gorunse bile
    hesap her zaman dogru degerlerle yapilir.
    """
    dogru = min(max(int(st.session_state.get(dogru_key, 0)), 0), max_soru)
    yanlis = min(max(int(st.session_state.get(yanlis_key, 0)), 0), max_soru)
    if dogru + yanlis > max_soru:
        yanlis = max_soru - dogru
    return dogru, yanlis


def secim_sabitle(key: str, varsayilan: str):
    """
    Pills/segmented_control 'tek secim' modunda bile tekrar tiklaninca
    None donebiliyor. Bu callback None gorunce bir onceki gecerli degere
    geri doner, boylece secim hep dolu kalir.
    """
    onceki_key = f"_{key}_onceki"
    if st.session_state.get(key) is None:
        st.session_state[key] = st.session_state.get(onceki_key, varsayilan)
    else:
        st.session_state[onceki_key] = st.session_state[key]


def _dogru_degisti(dogru_key: str, yanlis_key: str, max_soru: int):
    """
    Dogru alani degisince: once kendini [0, max_soru]'ya sikistirir, sonra
    dogru+yanlis toplami max_soru'yu asarsa yanlisi dusurur. Klavyeyle
    sinir disi (-5, 56 gibi) girilen degerler icin de bu koruma calisir,
    cunku on_change her degisiklikte (yazip Enter'a basinca da) tetiklenir.
    """
    dogru = min(max(int(st.session_state[dogru_key]), 0), max_soru)
    st.session_state[dogru_key] = dogru
    if dogru + st.session_state[yanlis_key] > max_soru:
        st.session_state[yanlis_key] = max_soru - dogru


def _yanlis_degisti(dogru_key: str, yanlis_key: str, max_soru: int):
    """_dogru_degisti ile ayni mantik, yanlis alani degistiginde calisir."""
    yanlis = min(max(int(st.session_state[yanlis_key]), 0), max_soru)
    st.session_state[yanlis_key] = yanlis
    if st.session_state[dogru_key] + yanlis > max_soru:
        st.session_state[dogru_key] = max_soru - yanlis


st.set_page_config(layout="wide", page_title="YKS Puan Hesaplama", page_icon=":bar_chart:")

st.title("YKS Hesaplama Motoru")
st.subheader("Yusuf Bayraktar")

st.write("---")


st.info("Son yapılan değişikliklere göre AYT Matematik Testi 23. sorunun cevabı 'A' olarak değiştirilmiştir.")
st.success("2026 sıralama tahmini çok yakında!")

st.space("small")


# --- Veri yukleme: burada cache'liyoruz, calculator.py streamlit'ten bagimsiz kalsin diye ---
@st.cache_data
def veri_getir(yil: int, puan_turu: str) -> dict:
    return calc.yukle_yil_verisi(yil, puan_turu)


col_obp_label, col_obp, col_last_year = st.columns([0.05, 0.06, 0.35], border=False, gap="small", vertical_alignment="center")
col_obp_label.write("Diploma Notu")
diploma_notu = col_obp.number_input("Diploma Notu", min_value=0.0, max_value=100.0, value=80.0, step=1.0, format="%.1f", key="diploma_notu", label_visibility="collapsed")
on = col_last_year.toggle("Önceki sene yerleştim", value=False)


if YIL_KEY not in st.session_state:
    st.session_state[YIL_KEY] = YEARS[-1]
yil = int(st.session_state[YIL_KEY])


st.space("small")


col_tyt, col_ayt = st.columns(2, border=True, width="stretch", gap="medium")
with col_tyt:
    st.markdown("<h3 style='text-align:center;'>TYT Puan Hesaplama</h3>", unsafe_allow_html=True)  # st.write("TYT Puan Hesaplama")
    st.space(40)
    col_ders, col_dogru, col_yanlis, col_net = st.columns([2, 1, 1, 1])
    with col_ders:
        st.space(60)
        st.write("Türkçe")
        st.space(20)
        st.write("Sosyal Bilimler")
        st.space(20)
        st.write("Temel Matematik")
        st.space(20)
        st.write("Fen Bilimleri")
    with col_dogru:
        st.write("Doğru")
        st.space(10)
        st.number_input("türkçe doğru", min_value=0, max_value=40, key="tyt_td",
                         on_change=_dogru_degisti, args=("tyt_td", "tyt_ty", 40), label_visibility="collapsed")
        st.space(5)
        st.number_input("sosyal bilimler doğru", min_value=0, max_value=20, key="tyt_sd",
                         on_change=_dogru_degisti, args=("tyt_sd", "tyt_sy", 20), label_visibility="collapsed")
        st.space(5)
        st.number_input("temel matematik doğru", min_value=0, max_value=40, key="tyt_md",
                         on_change=_dogru_degisti, args=("tyt_md", "tyt_my", 40), label_visibility="collapsed")
        st.space(5)
        st.number_input("fen bilimleri doğru", min_value=0, max_value=20, key="tyt_fd",
                         on_change=_dogru_degisti, args=("tyt_fd", "tyt_fy", 20), label_visibility="collapsed")
    with col_yanlis:
        st.write("Yanlış")
        st.space(10)
        st.number_input("türkçe yanlış", min_value=0, max_value=40, key="tyt_ty",
                         on_change=_yanlis_degisti, args=("tyt_td", "tyt_ty", 40), label_visibility="collapsed")
        st.space(5)
        st.number_input("sosyal bilimler yanlış", min_value=0, max_value=20, key="tyt_sy",
                         on_change=_yanlis_degisti, args=("tyt_sd", "tyt_sy", 20), label_visibility="collapsed")
        st.space(5)
        st.number_input("temel matematik yanlış", min_value=0, max_value=40, key="tyt_my",
                         on_change=_yanlis_degisti, args=("tyt_md", "tyt_my", 40), label_visibility="collapsed")
        st.space(5)
        st.number_input("fen bilimleri yanlış", min_value=0, max_value=20, key="tyt_fy",
                         on_change=_yanlis_degisti, args=("tyt_fd", "tyt_fy", 20), label_visibility="collapsed")
    with col_net:
        st.write("Net")
        st.space(15)
        _td, _ty = guvenli_net_oku("tyt_td", "tyt_ty", 40)
        st.write(f"{calc.net_hesapla(_td, _ty):.2f}")
        st.space(20)
        _sd, _sy = guvenli_net_oku("tyt_sd", "tyt_sy", 20)
        st.write(f"{calc.net_hesapla(_sd, _sy):.2f}")
        st.space(20)
        _md, _my = guvenli_net_oku("tyt_md", "tyt_my", 40)
        st.write(f"{calc.net_hesapla(_md, _my):.2f}")
        st.space(20)
        _fd, _fy = guvenli_net_oku("tyt_fd", "tyt_fy", 20)
        st.write(f"{calc.net_hesapla(_fd, _fy):.2f}")
    
with col_ayt:
    cont_alan = st.container(border=False, horizontal_alignment="center", gap=None)#, height="content", vertical_alignment="center")
    cont_alan.markdown("<h3 style='text-align:center;'>AYT Puan Hesaplama</h3>", unsafe_allow_html=True)  # cont_alan.write("AYT Puan Hesaplama")
    options = ["Sayısal", "Eşit Ağırlık", "Sözel"]
    selection = cont_alan.pills(
        "Alan Seçimi", options, selection_mode="single", default="Sayısal",
        key=ALAN_KEY, on_change=secim_sabitle, args=(ALAN_KEY, "Sayısal"),
        label_visibility="collapsed"
    )
    col_ders, col_dogru, col_yanlis, col_net = st.columns([2, 1, 1, 1])
    with col_ders:
        st.space(60)
        st.write("Matematik")
        st.space(20)
        st.write("Fizik")
        st.space(20)
        st.write("Kimya")
        st.space(20)
        st.write("Biyoloji")
    with col_dogru:
        st.write("Doğru")
        st.space(10)
        st.number_input("matematik doğru", min_value=0, max_value=40, key="ayt_md",
                         on_change=_dogru_degisti, args=("ayt_md", "ayt_my", 40), label_visibility="collapsed")
        st.space(5)
        st.number_input("fizik doğru", min_value=0, max_value=14, key="ayt_fd",
                         on_change=_dogru_degisti, args=("ayt_fd", "ayt_fy", 14), label_visibility="collapsed")
        st.space(5)
        st.number_input("kimya doğru", min_value=0, max_value=13, key="ayt_kd",
                         on_change=_dogru_degisti, args=("ayt_kd", "ayt_ky", 13), label_visibility="collapsed")
        st.space(5)
        st.number_input("biyoloji doğru", min_value=0, max_value=13, key="ayt_bd",
                         on_change=_dogru_degisti, args=("ayt_bd", "ayt_by", 13), label_visibility="collapsed")
    with col_yanlis:
        st.write("Yanlış")
        st.space(10)
        st.number_input("matematik yanlış", min_value=0, max_value=40, key="ayt_my",
                         on_change=_yanlis_degisti, args=("ayt_md", "ayt_my", 40), label_visibility="collapsed")
        st.space(5)
        st.number_input("fizik yanlış", min_value=0, max_value=14, key="ayt_fy",
                         on_change=_yanlis_degisti, args=("ayt_fd", "ayt_fy", 14), label_visibility="collapsed")
        st.space(5)
        st.number_input("kimya yanlış", min_value=0, max_value=13, key="ayt_ky",
                         on_change=_yanlis_degisti, args=("ayt_kd", "ayt_ky", 13), label_visibility="collapsed")
        st.space(5)
        st.number_input("biyoloji yanlış", min_value=0, max_value=13, key="ayt_by",
                         on_change=_yanlis_degisti, args=("ayt_bd", "ayt_by", 13), label_visibility="collapsed")
    with col_net:
        st.write("Net")
        st.space(15)
        _md, _my = guvenli_net_oku("ayt_md", "ayt_my", 40)
        st.write(f"{calc.net_hesapla(_md, _my):.2f}")
        st.space(20)
        _fd, _fy = guvenli_net_oku("ayt_fd", "ayt_fy", 14)
        st.write(f"{calc.net_hesapla(_fd, _fy):.2f}")
        st.space(20)
        _kd, _ky = guvenli_net_oku("ayt_kd", "ayt_ky", 13)
        st.write(f"{calc.net_hesapla(_kd, _ky):.2f}")
        st.space(20)
        _bd, _by = guvenli_net_oku("ayt_bd", "ayt_by", 13)
        st.write(f"{calc.net_hesapla(_bd, _by):.2f}")


st.write("---")


# --- Tum girdileri tek dict'te topla, calculator'a gonderilecek format bu ---
# guvenli_net_oku ile okuyoruz ki ekranda gecici olarak yanlis bir deger
# gorunse bile hesaplama her zaman sinirlar icinde, dogru degerlerle yapilsin
_td, _ty = guvenli_net_oku("tyt_td", "tyt_ty", 40)
_sd, _sy = guvenli_net_oku("tyt_sd", "tyt_sy", 20)
_tmd, _tmy = guvenli_net_oku("tyt_md", "tyt_my", 40)
_fd, _fy = guvenli_net_oku("tyt_fd", "tyt_fy", 20)
_amd, _amy = guvenli_net_oku("ayt_md", "ayt_my", 40)
_afd, _afy = guvenli_net_oku("ayt_fd", "ayt_fy", 14)
_akd, _aky = guvenli_net_oku("ayt_kd", "ayt_ky", 13)
_abd, _aby = guvenli_net_oku("ayt_bd", "ayt_by", 13)

tum_sonuclar = {
    "turkce":          {"dogru": _td, "yanlis": _ty},
    "sosyal_bilimler": {"dogru": _sd, "yanlis": _sy},
    "temel_matematik": {"dogru": _tmd, "yanlis": _tmy},
    "fen_bilimleri":   {"dogru": _fd, "yanlis": _fy},
    "matematik":       {"dogru": _amd, "yanlis": _amy},
    "fizik":           {"dogru": _afd, "yanlis": _afy},
    "kimya":           {"dogru": _akd, "yanlis": _aky},
    "biyoloji":        {"dogru": _abd, "yanlis": _aby},
}

alan_puan_turu = {"Sayısal": "SAY", "Eşit Ağırlık": "EA", "Sözel": "SOZ"}
puan_turu = alan_puan_turu.get(selection)  # type: ignore

tyt_net_toplam = sum(
    calc.net_hesapla(tum_sonuclar[d]["dogru"], tum_sonuclar[d]["yanlis"]) for d in calc.TYT_DERSLER
)
ayt_net_toplam = sum(
    calc.net_hesapla(tum_sonuclar[d]["dogru"], tum_sonuclar[d]["yanlis"]) for d in calc.SAY_DERSLER
)


if puan_turu not in calc.GECERLI_PUAN_TURLERI:
    st.warning(f"{selection} puan türü hesaplaması yakında eklenecek, şimdilik sadece Sayısal destekleniyor.")

else:
    netler = calc.sonuclari_nete_cevir(tum_sonuclar)
    if all(net > 0 for net in netler.values()):
    
        data = veri_getir(yil, puan_turu)
        sonuc = calc.sıralama_ve_puan_hesapla(tum_sonuclar, data, yil, puan_turu, diploma_notu / 2 if on else diploma_notu)

        ham_puan_delta_text = ""
        yer_puan_delta_text = "Ham puan + OBP %50" if on else "Ham puan + OBP"
        sira_delta_text = ""

        sira_delta_color = "green"

        previous_year = YEARS[0]
        if YEARS.index(str(yil)) != 0:
            previous_year = int(YEARS[YEARS.index(str(yil)) - 1])
            data_previous = veri_getir(previous_year, puan_turu)
            sonuc_previous = calc.sıralama_ve_puan_hesapla(tum_sonuclar, data_previous, previous_year, puan_turu, diploma_notu / 2 if on else diploma_notu)
            ham_puan_delta_text = f"{(sonuc['ham_puan'] - sonuc_previous['ham_puan']):.1f} geçen yıla göre"
            sira_fark = (sonuc['yerlestirme_sira'] - sonuc_previous['yerlestirme_sira'])
            sira_delta_text = f"{sira_fark:,} geçen yıla göre"
            sira_delta_color = "green" if sira_fark < 0 else "red"
            


        col_tyt_net, col_ayt_net = st.columns(2)

        col_tyt_net.metric(label="TYT Neti", value=f"{tyt_net_toplam:.2f}", border=True)
        col_ayt_net.metric(label="AYT Neti", value=f"{ayt_net_toplam:.2f}", border=True)


        col_hpuan, col_ypuan, col_sira = st.columns(3, border=False, width="stretch", gap="small")

        

        col_hpuan.metric(label=f"Ham Puan ({puan_turu})", value=f"{sonuc['ham_puan']:.2f}".replace(".", ","), border=True, delta=ham_puan_delta_text) # delta="+3.2 geçen yıla göre", delta_color="green"
        col_ypuan.metric(label="Yerleştirme Puanı", value=f"{sonuc['yerlestirme_puani']:.2f}".replace(".", ","), delta=yer_puan_delta_text, delta_color="off", delta_arrow="off", border=True)
        col_sira.metric(label="Tahmini Sıralama", value=f"{sonuc['yerlestirme_sira']:,}".replace(",", "."), border=True, delta=sira_delta_text, delta_color=sira_delta_color)


        cont_yuzde = st.container(border=True, gap=None)

        col_yuzde_text1, col_yuzde_text2 = cont_yuzde.columns([0.77, 0.23], border=False, gap="small", vertical_alignment="center")

        col_yuzde_text1.caption("Yüzdelik Dilim")
        #col_yuzde_text2.caption(f"Adayların %{sonuc['yuzdelik_dilim']:.2f}'inden iyisin")
        cont_yuzde.progress(sonuc["yuzdelik_dilim"] / 100)

        with col_yuzde_text2:
            with st.container(horizontal=True, horizontal_alignment="right", border=False):
                st.caption(f"Adayların %{sonuc['yuzdelik_dilim']:.2f}'inden iyisin")
        


        st.write("---")


        sira = st.container(border=False, horizontal_alignment="center")

        col_years_text, col_years = sira.columns([1, 1], border=False, gap="xsmall", vertical_alignment="center")

        col_years_text.caption("Sıralama Tahmini için Yıl Seçiniz")

        
        with col_years:
            with st.container(horizontal=True, horizontal_alignment="right", border=False):
                st.pills(
                    "Yıl Seçimi", YEARS, selection_mode="single", key=YIL_KEY,
                    on_change=secim_sabitle, args=(YIL_KEY, YEARS[-1]),
                    label_visibility="collapsed", default=YEARS[-1]
                )

        ozet_tablo = {
            "Puan Türü":     ["TYT", "SAY", "EA", "SÖZ"],
            "Ham Puan":      [f"{sonuc["ham_puan_tyt"]:.5f}", f"{sonuc["ham_puan"]:.5f}", "-", "-"],
            "Ham Sıralama":  [f"{sonuc["ham_sira_tyt"]:,}", f"{sonuc["ham_sira"]:,}", "-", "-"],
            "Yer. Puanı":    [f"{sonuc["yerlestirme_puani_tyt"]:.5f}", f"{sonuc["yerlestirme_puani"]:.5f}", "-", "-"],
            "Yer. Sıralama": [f"{sonuc["yerlestirme_sira_tyt"]:,}", f"{sonuc["yerlestirme_sira"]:,}", "-", "-"]
        }

        sira.table(ozet_tablo)
    else:
        st.warning("Hesaplama için netlerini tam girmelisin.")