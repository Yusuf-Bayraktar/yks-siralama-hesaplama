from streamlit_extras import buy_me_a_coffee as cof
from streamlit_extras import metric_cards as mcard


import streamlit as st
import calculator as calc


YIL_KEY = "select_year"
ALAN_KEY = "alan_secim"
YEARS = ["2019", "2020", "2021", "2022", "2023", "2024", "2025"]


def guvenli_net_oku(dogru_key: str, yanlis_key: str, max_soru: int) -> tuple[int, int]:
    dogru = min(max(int(st.session_state.get(dogru_key, 0)), 0), max_soru)
    yanlis = min(max(int(st.session_state.get(yanlis_key, 0)), 0), max_soru)
    if dogru + yanlis > max_soru:
        yanlis = max_soru - dogru
    return dogru, yanlis


def secim_sabitle(key: str, varsayilan: str):
    onceki_key = f"_{key}_onceki"
    if st.session_state.get(key) is None:
        st.session_state[key] = st.session_state.get(onceki_key, varsayilan)
    else:
        st.session_state[onceki_key] = st.session_state[key]


def ders_satiri_ciz(ders_adi: str, dogru_key: str, yanlis_key: str, max_soru: int):
    c_ders, c_dogru, c_yanlis, c_net = st.columns([1.5, 1.2, 1.2, 0.5], vertical_alignment="center")
    c_ders.write(ders_adi)
    c_dogru.number_input(
        f"{ders_adi} doğru", min_value=0, max_value=max_soru, key=dogru_key,
        on_change=_dogru_degisti, args=(dogru_key, yanlis_key, max_soru),
        label_visibility="collapsed",
    )
    c_yanlis.number_input(
        f"{ders_adi} yanlış", min_value=0, max_value=max_soru, key=yanlis_key,
        on_change=_yanlis_degisti, args=(dogru_key, yanlis_key, max_soru),
        label_visibility="collapsed",
    )
    _d, _y = guvenli_net_oku(dogru_key, yanlis_key, max_soru)
    c_net.markdown(
        f'<span style="color:#5B6EF5; font-weight:500;">{calc.net_hesapla(_d, _y):.2f}</span>',
        unsafe_allow_html=True,
    )


TYT_UI_TANIMLARI = [
    ("Türkçe", "tyt_td", "tyt_ty", 40),
    ("Sosyal Bilimler", "tyt_sd", "tyt_sy", 20),
    ("Temel Matematik", "tyt_md", "tyt_my", 40),
    ("Fen Bilimleri", "tyt_fd", "tyt_fy", 20),
]
AYT_UI_TANIMLARI = [
    ("Matematik", "ayt_md", "ayt_my", 40),
    ("Fizik", "ayt_fd", "ayt_fy", 14),
    ("Kimya", "ayt_kd", "ayt_ky", 13),
    ("Biyoloji", "ayt_bd", "ayt_by", 13),
]


def _dogru_degisti(dogru_key: str, yanlis_key: str, max_soru: int):
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


st.set_page_config(layout="wide", page_title="YKS Puan Hesaplama", page_icon="assets/logo.ico")

st.markdown(
    """
    <style>
    @media (max-width: 640px) {
        div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
            gap: 4px !important;
        }
        div[data-testid="stHorizontalBlock"] div[data-testid="stHorizontalBlock"] > div {
            min-width: 0 !important;
        }
 
        .st-key-diploma_row [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }
        .st-key-diploma_row [data-testid="stHorizontalBlock"] > div {
            min-width: 0 !important;
        }
 
        .st-key-net_ozet_row [data-testid="stHorizontalBlock"] {
            flex-wrap: nowrap !important;
        }
        .st-key-net_ozet_row [data-testid="stHorizontalBlock"] > div {
            min-width: 0 !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("YKS Hesaplama Motoru")
st.subheader("Yusuf Bayraktar")

st.write("---")


st.info("Son yapılan değişikliklere göre AYT Matematik Testi 23. sorunun cevabı 'A' olarak değiştirilmiştir.")
st.success("2026 sıralama tahmini çok yakında!")

st.space("small")


@st.cache_data
def veri_getir(yil: int, puan_turu: str) -> dict:
    return calc.yukle_yil_verisi(yil, puan_turu)


diploma_row = st.container(key="diploma_row")
col_obp_label, col_obp, col_last_year = diploma_row.columns([0.15, 0.18, 0.35], border=False, gap="small", vertical_alignment="center")
col_obp_label.write("Diploma Notu")
diploma_notu = col_obp.number_input("Diploma Notu", min_value=0.0, max_value=100.0, value=80.0, step=1.0, format="%.1f", key="diploma_notu", label_visibility="collapsed")
on = col_last_year.toggle("Önceki sene yerleştim", value=False)


if YIL_KEY not in st.session_state:
    st.session_state[YIL_KEY] = YEARS[-1]
yil = int(st.session_state[YIL_KEY])


st.space("small")


col_tyt, col_ayt = st.columns(2, border=True, width="stretch", gap="medium")
with col_tyt:
    st.markdown(
        '<div style="height:4px; background:#378ADD; border-radius:4px; margin-bottom:14px;"></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h3 style='text-align:center; font-size:1.5rem; font-weight:600;'>TYT Puan Hesaplama</h3>",
        unsafe_allow_html=True,
    )
    st.space(30)
    header = st.columns([1.5, 1.2, 1.2, 0.5])
    header[1].write("Doğru")
    header[2].write("Yanlış")
    header[3].write("Net")
    for _ders_adi, _dk, _yk, _maxs in TYT_UI_TANIMLARI:
        ders_satiri_ciz(_ders_adi, _dk, _yk, _maxs)

with col_ayt:
    st.markdown(
        '<div style="height:4px; background:#F5B25B; border-radius:4px; margin-bottom:14px;"></div>',
        unsafe_allow_html=True,
    )
    cont_alan = st.container(border=False, horizontal_alignment="center", gap="small")
    cont_alan.markdown(
        "<h3 style='text-align:center; font-size:1.5rem; font-weight:600;'>AYT Puan Hesaplama</h3>",
        unsafe_allow_html=True,
    )
    options = ["Sayısal", "Eşit Ağırlık", "Sözel"]
    selection = cont_alan.pills(
        "Alan Seçimi", options, selection_mode="single", default="Sayısal",
        key=ALAN_KEY, on_change=secim_sabitle, args=(ALAN_KEY, "Sayısal"),
        label_visibility="collapsed"
    )
    header = st.columns([1.5, 1.2, 1.2, 0.5])
    header[1].write("Doğru")
    header[2].write("Yanlış")
    header[3].write("Net")
    for _ders_adi, _dk, _yk, _maxs in AYT_UI_TANIMLARI:
        ders_satiri_ciz(_ders_adi, _dk, _yk, _maxs)


st.write("---")


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
puan_turu = alan_puan_turu.get(selection)

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
            


        net_ozet_row = st.container(key="net_ozet_row")
        col_tyt_net, col_ayt_net = net_ozet_row.columns(2)

        col_tyt_net.metric(label="TYT Neti", value=f"{tyt_net_toplam:.2f}", border=True)
        col_ayt_net.metric(label="AYT Neti", value=f"{ayt_net_toplam:.2f}", border=True)


        col_hpuan, col_ypuan, col_sira = st.columns(3, border=False, width="stretch", gap="small")

        
        col_hpuan.metric(label=f"Ham Puan ({puan_turu})", value=f"{sonuc['ham_puan']:.2f}".replace(".", ","), border=True, delta=ham_puan_delta_text) # delta="+3.2 geçen yıla göre", delta_color="green"
        col_ypuan.metric(label="Yerleştirme Puanı", value=f"{sonuc['yerlestirme_puani']:.2f}".replace(".", ","), delta=yer_puan_delta_text, delta_color="off", delta_arrow="off", border=True)
        col_sira.metric(label="Tahmini Sıralama", value=f"{sonuc['yerlestirme_sira']:,}".replace(",", "."), border=True, delta=sira_delta_text, delta_color=sira_delta_color)

        # mcard.style_metric_cards()

        cont_yuzde = st.container(border=True, gap=None)
        cont_yuzde.markdown(
            f"""<div style="display:flex; justify-content:space-between; align-items:center;
                        opacity:0.6; font-size:0.875rem; white-space:nowrap; gap:12px;
                        margin-bottom:18px;">
                <span style="white-space:nowrap;">Yüzdelik Dilim</span>
                <span style="white-space:nowrap;">Adayların %{sonuc['yuzdelik_dilim']:.2f}'inden iyisin</span>
            </div>""",
            unsafe_allow_html=True
        )
        cont_yuzde.progress(sonuc["yuzdelik_dilim"] / 100)


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


cof.button(username="yusuf-bayraktar", floating=False, width=221)


st.write("aff")