import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import calendar
from sklearn.ensemble import RandomForestRegressor
import os

st.set_page_config(page_title="Operasyon Simülatörü", layout="wide")

# ---------- Tatiller ----------
tam_tatiller = {
    "2024-01-01","2024-04-10","2024-04-11","2024-04-12","2024-04-23","2024-05-01",
    "2024-05-19","2024-06-16","2024-06-17","2024-06-18","2024-06-19","2024-07-15",
    "2024-08-30","2024-10-29","2025-01-01","2025-03-30","2025-03-31","2025-04-01",
    "2025-04-23","2025-05-01","2025-05-19","2025-06-06","2025-06-07","2025-06-08",
    "2025-06-09","2025-07-15","2025-08-30","2025-10-29",
}
arifeler = {"2024-04-09","2024-06-15","2024-10-28","2024-12-31","2025-03-29","2025-06-05","2025-10-28"}
tam_tatiller = {dt.date.fromisoformat(x) for x in tam_tatiller}
arifeler = {dt.date.fromisoformat(x) for x in arifeler}

# ---------- SLA + uyarı ----------
def sla_tahmin(hacim, havuz):
    yuk = hacim / havuz
    return max(0.0, min(1.0, 1.1296 - 0.006522 * yuk))

def uyari_rengi(yuk):
    if yuk < 34.5: return "🟢 Normal"
    elif yuk < 41.4: return "🟡 Dikkat"
    else: return "🔴 Kritik"

# ---------- Veri + model (bir kez kurulur) ----------
@st.cache_resource
def hazirla():
    BASE = os.path.dirname(__file__)
    g = pd.read_csv(os.path.join(BASE, "gunluk_ozet.csv"), encoding="utf-8-sig")
    g["baslama_tarihi"] = pd.to_datetime(g["baslama_tarihi"])
    g = g.sort_values("baslama_tarihi").reset_index(drop=True)
    g["ma_14"] = g["gunluk_hacim"].shift(1).rolling(14).mean()
    g = g.dropna().reset_index(drop=True)
    g["oran"] = g["gunluk_hacim"] / g["ma_14"]
    X = pd.get_dummies(g[["gun_adi","ay_no","tatil_oncesi_mi","ay_sonu_mu","arife_mi"]],
                       columns=["gun_adi","ay_no"])
    rf = RandomForestRegressor(n_estimators=300, random_state=42)
    rf.fit(X, g["oran"])
    seviye = g["gunluk_hacim"].tail(14).mean()
    esnek_oran = (g["yonlendirilebilir"] / g["gunluk_hacim"]).mean()
    ort_ekip = int(g["isbasi_sayi"].mean())
    return rf, list(X.columns), seviye, esnek_oran, ort_ekip

rf, X_kolon, seviye, esnek_oran, ort_ekip = hazirla()

# ---------- Gelecek tarih -> tahmini hacim ----------
def gelecek_tahmin(tarih):
    gun_map = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",4:"Friday",5:"Saturday",6:"Sunday"}
    satir = {
        "gun_adi": gun_map[tarih.weekday()],
        "ay_no": tarih.month,
        "tatil_oncesi_mi": 1 if (tarih+dt.timedelta(days=1) in tam_tatiller or tarih+dt.timedelta(days=2) in tam_tatiller) else 0,
        "ay_sonu_mu": 1 if tarih.day >= calendar.monthrange(tarih.year, tarih.month)[1]-2 else 0,
        "arife_mi": 1 if tarih in arifeler else 0,
    }
    df1 = pd.get_dummies(pd.DataFrame([satir]), columns=["gun_adi","ay_no"])
    df1 = df1.reindex(columns=X_kolon, fill_value=0)
    return rf.predict(df1)[0] * seviye

# ---------- Simülatör ----------
def simule(hacim, baz_ekip, yeni_ekip, yon_oran, yonlendirilebilir):
    baz_yuk = hacim / baz_ekip
    baz_sla = sla_tahmin(hacim, baz_ekip)
    kaydirilan = int(yonlendirilebilir * yon_oran)
    senaryo_hacim = hacim - kaydirilan
    senaryo_yuk = senaryo_hacim / yeni_ekip
    senaryo_sla = sla_tahmin(senaryo_hacim, yeni_ekip)
    return baz_yuk, senaryo_yuk, baz_sla, senaryo_sla, kaydirilan

SLA_HEDEF = 0.90

def optimum_bul(hacim, baz_ekip, yonlendirilebilir):
    en_iyi = None
    for ekip in range(baz_ekip - 5, baz_ekip + 1):
        if ekip < 1:
            continue
        for yon in [0, 0.1, 0.2, 0.3]:
            r = simule(hacim, baz_ekip, ekip, yon, yonlendirilebilir)
            sla = r[3]
            uygun = sla >= SLA_HEDEF
            aday = {"ekip": ekip, "yon": yon, "sla": sla, "uygun": uygun}
            if en_iyi is None:
                en_iyi = aday
            else:
                # Karşılaştırma önceliği:
                # 1) SLA hedefini tutturan kazanır
                # 2) tutuyorsa: önce daha az kişi, sonra daha az yönlendirme
                # 3) ikisi de tutmuyorsa: daha yüksek SLA
                if aday["uygun"] and not en_iyi["uygun"]:
                    en_iyi = aday
                elif aday["uygun"] and en_iyi["uygun"]:
                    if (aday["ekip"], aday["yon"]) < (en_iyi["ekip"], en_iyi["yon"]):
                        en_iyi = aday
                elif not aday["uygun"] and not en_iyi["uygun"]:
                    if aday["sla"] > en_iyi["sla"]:
                        en_iyi = aday
    return en_iyi

def yillik_hesap(yil, baz_ekip):
    gun = dt.date(yil, 1, 1)
    son = dt.date(yil, 12, 31)
    top_hacim = top_sla = gun_say = 0
    ek_islem_optimum = 0
    while gun <= son:
        if gun not in tam_tatiller:
            h = gelecek_tahmin(gun)
            ylb = h * esnek_oran
            baz_sla = sla_tahmin(h, baz_ekip)
            o = optimum_bul(h, baz_ekip, ylb)
            ek_islem_optimum += (o["sla"] - baz_sla) * h
            top_hacim += h
            top_sla += baz_sla
            gun_say += 1
        gun += dt.timedelta(days=1)
    return {
        "toplam_hacim": top_hacim,
        "ort_sla": top_sla / gun_say,
        "ek_islem_optimum": ek_islem_optimum,
        "gun_say": gun_say
    }

_hacim_cache = {}

def yil_hacimleri(yil):
    """Yılın tüm günlerinin tahmini hacmini BİR KEZ hesaplar (cache'lenir)."""
    if yil not in _hacim_cache:
        gun = dt.date(yil, 1, 1)
        son = dt.date(yil, 12, 31)
        liste = []
        while gun <= son:
            if gun not in tam_tatiller:
                liste.append(gelecek_tahmin(gun))
            gun += dt.timedelta(days=1)
        _hacim_cache[yil] = liste
    return _hacim_cache[yil]

def tr_sayi(n):
    return f"{n:,.0f}".replace(",", ".")

def yil_simule(yil, ekip, yon_oran):
    hacimler = yil_hacimleri(yil)          # önceden hesaplanmış hacimler
    top_hacim = top_sla = 0
    for h in hacimler:
        ylb = h * esnek_oran
        r = simule(h, ekip, ekip, yon_oran, ylb)
        top_sla += r[3]
        top_hacim += h
    return top_hacim, top_sla / len(hacimler), len(hacimler)

def yillik_optimum_ekip(yil, baz_ekip):
    yil_hacimleri(yil)                     # önce hacimleri hazırla (bir kez)
    en_iyi = None
    for ekip in range(baz_ekip, baz_ekip + 20):
        for yon in [0, 0.1, 0.2, 0.3]:
            _, ort_sla, _ = yil_simule(yil, ekip, yon)
            if ort_sla >= 0.90:
                en_iyi = {"ekip": ekip, "yon": yon, "sla": ort_sla}
                break
        if en_iyi:
            break
    if en_iyi is None:
        _, ort_sla, _ = yil_simule(yil, baz_ekip + 19, 0.3)
        en_iyi = {"ekip": baz_ekip + 19, "yon": 0.3, "sla": ort_sla}
    return en_iyi

# ---------- Arayüz ----------
st.title("Operasyonel Yoğunluk ve Verimlilik Simülatörü")

sekme_gun, sekme_yil = st.tabs(["📊 Günlük Simülasyon", "📅 Yıllık Hesap"])

# ===== GÜNLÜK SEKME =====
with sekme_gun:
    col_giris, col_sonuc = st.columns([1, 2], gap="large")

    with col_giris:
        st.subheader("⚙️ Senaryo Ayarları")
        tarih = st.date_input("Gün seç", dt.date(2026, 3, 12))
        yeni_ekip = st.slider("Ekip sayısı", 40, 70, ort_ekip)
        yon_oran = st.slider("Yönlendirme oranı (%)", 0, 50, 0) / 100

    hacim = gelecek_tahmin(tarih)
    yonlendirilebilir = hacim * esnek_oran
    b_yuk, s_yuk, b_sla, s_sla, kay = simule(
        hacim, ort_ekip, yeni_ekip, yon_oran, yonlendirilebilir)

    ek_islem = (s_sla - b_sla) * hacim
    geciken_islem = (1 - s_sla) * hacim

    with col_sonuc:
        durum = uyari_rengi(s_yuk)
        renk = {"🟢": "#16a34a", "🟡": "#ca8a04", "🔴": "#dc2626"}[durum[0]]
        st.markdown(
            f"""
            <div style="border-left:6px solid {renk};
                        background:rgba(128,128,128,0.12);
                        padding:14px 18px; border-radius:8px; margin-bottom:16px;">
                <div style="font-size:13px; opacity:0.7;">{tarih} · Tahmini hacim</div>
                <div style="font-size:28px; font-weight:700;">{hacim:.0f} işlem</div>
                <div style="font-size:15px; margin-top:4px;">{durum}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### Operasyonel Sonuç")
        m1, m2 = st.columns(2)
        m1.metric("Kişi başı yük(İşlem Adedi)", f"{s_yuk:.1f}", f"{s_yuk - b_yuk:.1f}")
        m2.metric("SLA (hedefte biten)", f"%{s_sla*100:.1f}", f"%{(s_sla - b_sla)*100:.1f} puan")
        m3, m4 = st.columns(2)
        m3.metric("Müdahale etkisi", f"{ek_islem:+.0f} işlem",
                  help="Bu senaryonun baz duruma göre ek olarak zamanında bitirdiği işlem")
        m4.metric("Geciken işlem (toplam)", f"{geciken_islem:.0f}")

    st.divider()
    st.markdown("##### 🎯 Bu Günün Optimumu")
    st.caption("SLA ≥ %90 hedefini en az kaynakla (kişi + yönlendirme) tutturan ayar.")
    if st.button("Optimum ayarı bul", type="primary"):
        o = optimum_bul(hacim, ort_ekip, yonlendirilebilir)
        opt_ek = (o["sla"] - b_sla) * hacim
        durum2 = "✅ SLA hedefi tutuyor" if o["uygun"] else "⚠️ SLA hedefine ulaşılamıyor (en iyi seçildi)"
        st.success(
            f"**Önerilen ayar: {o['ekip']} kişi · %{int(o['yon']*100)} yönlendirme**  \n"
            f"SLA: %{o['sla']*100:.1f}  ({durum2})  \n"
            f"Baz duruma göre ek zamanında biten işlem: **{opt_ek:+.0f}**"
        )

# ===== YILLIK SEKME =====
with sekme_yil:
    st.subheader("📅 Yıllık Planlama")

    c1, c2 = st.columns([1, 2])
    with c1:
        yil_sec = st.selectbox("Planlama yılı", [2026, 2025, 2024])
    with c2:
        st.markdown(
            f"""
            <div style="background:rgba(128,128,128,0.12); padding:12px 16px;
                        border-radius:8px; margin-top:4px;">
                <span style="opacity:0.7; font-size:13px;">Mevcut durum</span><br>
                <b>{ort_ekip} kişi</b> · günlük ortalama aktif personel
                <span style="opacity:0.6;">(izin/rapor sonrası sahada olan)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")

    # --- 1. Mevcut ekiple ---
    st.markdown("##### 1️⃣ Mevcut Ekiple Yıl Sonucu")
    if st.button("Mevcut ekiple hesapla", type="primary", key="yil_mevcut"):
        with st.spinner("Hesaplanıyor..."):
            th, osla, gs = yil_simule(yil_sec, ort_ekip, 0)
        st.session_state["yil_mevcut_sonuc"] = (th, osla, gs)

    if "yil_mevcut_sonuc" in st.session_state:
        th, osla, gs = st.session_state["yil_mevcut_sonuc"]
        a1, a2, a3 = st.columns(3)
        a1.metric("Toplam işlem", tr_sayi(th))
        a2.metric("Ortalama SLA", f"%{osla*100:.1f}")
        a3.metric("Hedef durumu", "✅ Üstünde" if osla >= 0.90 else "⚠️ Altında")
        st.caption(f"{gs} iş günü · {ort_ekip} aktif kişi · yönlendirme yok")

    st.divider()

    # --- 2. Optimum kadro ---
    st.markdown("##### 2️⃣ SLA ≥ %90 için Optimum Kadro")
    st.caption("Hedefi tutturan en küçük sabit kadro ve gereken yönlendirme.")
    if st.button("Optimum kadroyu bul", type="primary", key="yil_opt"):
        with st.spinner("Kadrolar deneniyor..."):
            st.session_state["yil_opt_sonuc"] = yillik_optimum_ekip(yil_sec, ort_ekip)

    if "yil_opt_sonuc" in st.session_state:
        o = st.session_state["yil_opt_sonuc"]
        fark = o["ekip"] - ort_ekip
        st.success(f"**Önerilen kadro: {o['ekip']} aktif kişi · %{int(o['yon']*100)} yönlendirme**")
        s1, s2, s3 = st.columns(3)
        s1.metric("Yıllık ort. SLA", f"%{o['sla']*100:.1f}")
        s2.metric("Mevcuda göre fark", f"{fark:+d} kişi")
        s3.metric("Yönlendirme", f"%{int(o['yon']*100)}")

    st.divider()

    # --- 3. Kendi senaryosu ---
    st.markdown("##### 3️⃣ Kendi Senaryonu Dene")
    ys1, ys2 = st.columns(2)
    with ys1:
        y_ekip = st.slider("Aktif personel", 40, 80, ort_ekip, key="yil_ekip")
    with ys2:
        y_yon = st.slider("Yönlendirme (%)", 0, 50, 0, key="yil_yon") / 100
    if st.button("Bu senaryoyu hesapla", key="yil_senaryo"):
        with st.spinner("Hesaplanıyor..."):
            th, osla, gs = yil_simule(yil_sec, y_ekip, y_yon)
        st.session_state["yil_senaryo_sonuc"] = (th, osla, gs, y_ekip, y_yon)

    if "yil_senaryo_sonuc" in st.session_state:
        th, osla, gs, ye, yy = st.session_state["yil_senaryo_sonuc"]
        b1, b2, b3 = st.columns(3)
        b1.metric("Toplam işlem", tr_sayi(th))
        b2.metric("Ortalama SLA", f"%{osla*100:.1f}")
        b3.metric("Hedef durumu", "✅ Üstünde" if osla >= 0.90 else "⚠️ Altında")
        st.caption(f"{gs} iş günü · {ye} aktif kişi · %{int(yy*100)} yönlendirme")