# OPERASYONEL YOĞUNLUK TAHMİN SİSTEMİ
# ÇOK DETAYLI ÖDEV KILAVUZU (kod iskeletli)

> **Nasıl kullanılır:** Her görevde bir **kod iskeleti** var. `____` (alt çizgi) olan yerleri SEN dolduracaksın.
> Yorumlar (`#`) ne yaptığını anlatıyor. Önce anlamaya çalış, sonra doldur.
> Takıldığında: "Görev X.Y'de `____` kısmında takıldım" de.

---

# 📦 VERİ HATIRLATMA

**islem_detay.csv** sütunları:
`islem_id, musteri_id, musteri_tipi, islem_tipi, baslama_tarihi, baslama_zamani, baslama_ay, baslama_gun, baslama_hafta, tamamlama_tarihi, tamamlama_zamani, hedef_sure_dk, gercek_sure_dk, gecikme_dk, hedefte_bitti, havuz_kisi_sayisi`

**calisan_detay.csv** sütunları:
`calisan_id, takim, tarih, ay, gun, hafta, durum, gunluk_islem`

---

# ════════════════════════════════════════
# FAZ 0 — KURULUM VE VERİYİ TANIMA
# ════════════════════════════════════════

## Görev 0.1 — Kurulum
Terminal'de:
```
pip install pandas numpy matplotlib seaborn scikit-learn
```

## Görev 0.2 — `01_veri_yukle.py`
```python
import pandas as pd
import numpy as np

# CSV'leri oku (encoding utf-8-sig -> Turkce karakterler dogru)
df_islem = pd.read_csv("islem_detay.csv", encoding="utf-8-sig")
df_cal   = pd.read_csv("calisan_detay.csv", encoding="utf-8-sig")

# Tarih sutunlarini datetime'a cevir
df_islem["baslama_tarihi"]   = pd.to_datetime(df_islem["____"])   # hangi sutun?
df_islem["tamamlama_tarihi"] = pd.to_datetime(df_islem["____"])
df_cal["tarih"]              = pd.to_datetime(df_cal["____"])
```

## Görev 0.3 — Tanıma (her satırı ayrı çalıştır, çıktıyı oku)
```python
print(df_islem.shape)              # (satir, sutun)
print(df_islem.head())
print(df_islem.dtypes)
print(df_islem.describe())
print(df_islem.isnull().sum())     # hepsi 0 olmali

print(df_cal.shape)
print(df_cal["durum"].value_counts())   # isbasi/izinli/raporlu/tatil dagilimi
```

### ✅ KONTROL 0: islem 1.384.754 satır, eksik değer yok, tarihler datetime.

---

# ════════════════════════════════════════
# FAZ 1 — GÜNLÜK ÖZET TABLOSU
# ════════════════════════════════════════
*Yeni dosya: `02_gunluk_ozet.py` (başına Faz 0'daki okuma kodunu koy)*

## Görev 1.1 — İşlemden günlük temel metrikler
```python
gunluk = df_islem.groupby("baslama_tarihi").agg(
    gunluk_hacim = ("islem_id",          "____"),   # say -> "count"
    havuz_kisi   = ("havuz_kisi_sayisi", "____"),   # gun boyu sabit -> "first"
    sla_orani    = ("hedefte_bitti",     "____"),   # 0/1 ortalamasi -> "mean"
    ort_gecikme  = ("gecikme_dk",        "____"),   # ortalama -> "mean"
).reset_index()

print(gunluk.head())
print(gunluk.shape)   # ~700 satir olmali
```
**Not:** `reset_index()` → `baslama_tarihi`'yi normal sütun yapar (index olmaktan çıkarır).

## Görev 1.2 — İşlem tipi kırılımı
```python
# Her gun + her tip icin sayim, sonra tipleri sutuna yay
tip_gunluk = (
    df_islem.groupby(["baslama_tarihi", "islem_tipi"])
    .size()                    # her grubun satir sayisi
    .unstack(fill_value=0)     # islem_tipi degerlerini SUTUN yapar
    .reset_index()
)
print(tip_gunluk.head())   # sutunlar: baslama_tarihi, iptal, yurtdisi, yurtici

# gunluk tablosuna birlestir
gunluk = pd.merge(gunluk, tip_gunluk, on="____", how="left")   # ortak sutun?
```

## Görev 1.3 — Müşteri tipi kırılımı
```python
seg_gunluk = (
    df_islem.groupby(["baslama_tarihi", "____"])   # tarih + musteri_tipi
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
# sutun adlari karismasin diye yeniden adlandir (opsiyonel ama temiz)
seg_gunluk = seg_gunluk.rename(columns={
    "kurumsal": "seg_kurumsal",
    "KOBİ":     "seg_kobi",
    "bireysel": "seg_bireysel"
})
gunluk = pd.merge(gunluk, seg_gunluk, on="baslama_tarihi", how="left")
```

## Görev 1.4 — Çalışan durumundan günlük havuz
```python
durum_gunluk = (
    df_cal.groupby(["tarih", "durum"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
# sutunlar: tarih, izinli, raporlu, tatil, işbaşı
durum_gunluk = durum_gunluk.rename(columns={
    "işbaşı":  "isbasi_sayi",
    "izinli":  "izinli_sayi",
    "raporlu": "raporlu_sayi"
})

# gunluk ile birlestir: tarih sutunlari farkli isimli (baslama_tarihi vs tarih)
gunluk = pd.merge(
    gunluk, durum_gunluk,
    left_on="baslama_tarihi", right_on="____", how="left"   # right_on ne?
)
```

## Görev 1.5 — Takvim özellikleri
```python
gunluk["gun_adi"]   = gunluk["baslama_tarihi"].dt.____      # day_name() VEYA mevcut baslama_gun
gunluk["ay_no"]     = gunluk["baslama_tarihi"].dt.____      # month
gunluk["yil"]       = gunluk["baslama_tarihi"].dt.____      # year
gunluk["ayin_gunu"] = gunluk["baslama_tarihi"].dt.____      # day
gunluk["hafta"]     = gunluk["baslama_tarihi"].dt.isocalendar().week
```

## Görev 1.6 — Tatil bayrakları
Önce tatil set'ini tanımla (BENDEN İSTE — hazır vereceğim). Sonra:
```python
import datetime as dt

tam_tatiller = { ... }   # benden al, set of datetime.date

# tatil_mi: tarih tatil setinde mi?
gunluk["tatil_mi"] = gunluk["baslama_tarihi"].apply(
    lambda x: 1 if x.date() in ____ else 0      # hangi set?
)

# tatil_oncesi_mi: ertesi 1 veya 2 gun tatil mi?
def tatil_oncesi(tarih):
    yarin     = tarih.date() + dt.timedelta(days=1)
    obur_gun  = tarih.date() + dt.timedelta(days=2)
    if yarin in tam_tatiller or obur_gun in tam_tatiller:
        return 1
    return 0

gunluk["tatil_oncesi_mi"] = gunluk["baslama_tarihi"].apply(____)   # fonksiyon adi

# ay_sonu_mu: ayin son 3 gunu mu?
import calendar
def ay_sonu(tarih):
    son_gun = calendar.monthrange(tarih.year, tarih.month)[1]
    return 1 if tarih.day >= son_gun - 2 else 0

gunluk["ay_sonu_mu"] = gunluk["baslama_tarihi"].apply(ay_sonu)
```

## Görev 1.7 — Kişi başına yük (PROJENİN KALBİ)
```python
gunluk["kisi_basi_yuk"] = gunluk["____"] / gunluk["____"]   # hacim / isbasi_sayi
```

## Görev 1.8 — Kaydet
```python
gunluk.to_csv("gunluk_ozet.csv", index=False, encoding="utf-8-sig")
print("Kaydedildi:", gunluk.shape)
```

### ✅ KONTROL 1: ~700 satır, tüm sütunlar var, `kisi_basi_yuk` 20-50 arası.

---

# ════════════════════════════════════════
# FAZ 2 — KEŞİFSEL ANALİZ (EDA)
# ════════════════════════════════════════
*Yeni dosya: `03_eda.py`*

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

gunluk = pd.read_csv("gunluk_ozet.csv", encoding="utf-8-sig")
gunluk["baslama_tarihi"] = pd.to_datetime(gunluk["baslama_tarihi"])
```

## Görev 2.1 — Haftanın günü paterni
```python
# gun sirasi (dogru sirayla gostermek icin)
gun_sira = ["Pzt","Sal","Çar","Per","Cum","Cmt","Paz"]

gun_ort = gunluk.groupby("gun_adi")["gunluk_hacim"].mean()
gun_ort = gun_ort.reindex(____)    # gun_sira ile sirala

plt.figure(figsize=(8,4))
gun_ort.plot(kind="____")          # bar
plt.title("Gün Bazında Ortalama Hacim")
plt.ylabel("İşlem")
plt.show()
```
**Beklenen:** Salı + Cumartesi en yüksek.

## Görev 2.2 — Aylık trend (2024 vs 2025)
```python
aylik = gunluk.groupby(["yil","ay_no"])["gunluk_hacim"].mean().reset_index()

plt.figure(figsize=(10,4))
for y in [2024, 2025]:
    alt = aylik[aylik["yil"] == ____]          # o yili filtrele
    plt.plot(alt["ay_no"], alt["gunluk_hacim"], marker="o", label=str(y))
plt.legend(); plt.title("Aylık Ortalama Hacim"); plt.xlabel("Ay")
plt.show()
```

## Görev 2.3 — Tatil öncesi etki
```python
print(gunluk.groupby("tatil_oncesi_mi")["gunluk_hacim"].____())   # mean
# 0 = normal gun ort, 1 = tatil oncesi ort. 1 daha yuksek olmali.
```

## Görev 2.4 — Ay sonu etkisi
```python
print(gunluk.groupby("ay_sonu_mu")["gunluk_hacim"].mean())
```

## Görev 2.5 — SLA vs YÜK (KALP)
```python
plt.figure(figsize=(8,5))
plt.scatter(gunluk["kisi_basi_yuk"], gunluk["sla_orani"], alpha=0.3)
plt.xlabel("Kişi Başına Yük"); plt.ylabel("SLA Oranı")
plt.title("Yük Arttıkça SLA Düşüyor mu?")
plt.show()

# korelasyon (negatif bekleniyor)
kor = gunluk["kisi_basi_yuk"].____(gunluk["sla_orani"])   # corr
print("Korelasyon:", kor)
```

## Görev 2.6 — Yük gruplarında SLA
```python
gunluk["yuk_grup"] = pd.qcut(
    gunluk["kisi_basi_yuk"], 4,
    labels=["Düşük","Orta","Yüksek","Çok Yüksek"]
)
print(gunluk.groupby("yuk_grup", observed=True)["sla_orani"].mean())
```
**Beklenen:** Düşük ~0.98 → Çok Yüksek ~0.80.

## Görev 2.7 — Müşteri segment: kurumsal hangi gün yoğun
```python
seg_gun = gunluk.groupby("gun_adi")[["seg_kurumsal","seg_kobi","seg_bireysel"]].mean()
seg_gun = seg_gun.reindex(gun_sira)
seg_gun.plot(kind="bar", figsize=(10,5))
plt.title("Gün Bazında Segment Ortalaması")
plt.show()
```
**Beklenen:** Cuma'da `seg_kurumsal` zirve.

## Görev 2.8 — Esnek havuz büyüklüğü
```python
# esnek = bireysel + kobi, toplam islemin yuzde kaci?
gunluk["esnek_islem"] = gunluk["seg_bireysel"] + gunluk["seg_kobi"]
gunluk["esnek_oran"]  = gunluk["esnek_islem"] / gunluk["gunluk_hacim"]
print("Ortalama esnek oran:", gunluk["esnek_oran"].mean())
```

### ✅ KONTROL 2: Salı/Cmt zirve görünür, yük-SLA korelasyonu negatif, kurumsal Cuma yoğun.

---

# ════════════════════════════════════════
# FAZ 3 — TAHMİN MOTORU
# ════════════════════════════════════════
*Yeni dosya: `04_tahmin_motoru.py`*

```python
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

gunluk = pd.read_csv("gunluk_ozet.csv", encoding="utf-8-sig")
gunluk["baslama_tarihi"] = pd.to_datetime(gunluk["baslama_tarihi"])
```

## Görev 3.1 — Özellikleri hazırla (one-hot encoding)
```python
# Modele girecek ozellikler: gun, ay, bayraklar
ozellikler = gunluk[[
    "gun_adi", "ay_no", "tatil_oncesi_mi", "ay_sonu_mu", "yil"
]].copy()

# Kategorik gun_adi'yi sayisal sutunlara cevir (one-hot)
ozellikler = pd.get_dummies(ozellikler, columns=["____"])   # gun_adi

X = ozellikler
y = gunluk["gunluk_hacim"]
```

## Görev 3.2 — Train/Test (2024 eğit, 2025 test)
```python
egitim_maske = gunluk["yil"] == ____      # 2024
test_maske   = gunluk["yil"] == ____      # 2025

X_train, y_train = X[egitim_maske], y[egitim_maske]
X_test,  y_test  = X[test_maske],  y[test_maske]
print("Egitim:", X_train.shape, "Test:", X_test.shape)
```

## Görev 3.3 — Baseline (gün ortalaması)
```python
# Her gun adinin egitimdeki ortalamasi -> basit tahmin
gun_ort_train = gunluk[egitim_maske].groupby("gun_adi")["gunluk_hacim"].mean()

baseline_tahmin = gunluk[test_maske]["gun_adi"].map(____)   # gun_ort_train

mae_base = mean_absolute_error(y_test, baseline_tahmin)
print("Baseline MAE:", mae_base)
```

## Görev 3.4 — Linear Regression
```python
lin = LinearRegression()
lin.____(X_train, y_train)            # fit
tahmin_lin = lin.____(X_test)          # predict

mae_lin = mean_absolute_error(y_test, tahmin_lin)
print("Linear MAE:", mae_lin)
```

## Görev 3.5 — Random Forest
```python
rf = RandomForestRegressor(n_estimators=200, random_state=42)
rf.fit(X_train, y_train)
tahmin_rf = rf.predict(X_test)

mae_rf = mean_absolute_error(y_test, tahmin_rf)
print("RF MAE:", mae_rf)

# Hangi ozellik onemli?
onem = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=False)
print(onem.head(10))
```
**Karşılaştır:** `mae_base`, `mae_lin`, `mae_rf` — en düşük kazanır.

## Görev 3.6 — Tahmin vs Gerçek grafiği
```python
test_tarih = gunluk[test_maske]["baslama_tarihi"]

plt.figure(figsize=(14,4))
plt.plot(test_tarih, y_test.values, label="Gerçek", alpha=0.7)
plt.plot(test_tarih, tahmin_rf,     label="Tahmin (RF)", alpha=0.7)
plt.legend(); plt.title("2025 Gerçek vs Tahmin")
plt.show()
```

## Görev 3.7 — SLA tahmin fonksiyonu
```python
# Yuk gruplarinin ortalama SLA'sini kullan (Faz 2.6'dan)
def sla_tahmin(hacim, havuz):
    yuk = hacim / havuz
    if   yuk < 28:  return 0.97
    elif yuk < 33:  return 0.92
    elif yuk < 38:  return 0.86
    else:           return 0.80
    # NOT: esikleri kendi qcut sonucundan ayarla
```

## Görev 3.8 — Hacim tahmin fonksiyonu (sarmalayıcı)
```python
def hacim_tahmin(ozellik_satiri):
    # ozellik_satiri: X ile ayni sutunlara sahip tek satir
    return rf.predict(ozellik_satiri)[0]
```

### ✅ KONTROL 3: Model baseline'ı yendi mi? Tahmin-gerçek grafiği makul mü?

---

# ════════════════════════════════════════
# FAZ 4 — ÜRÜN 1: ERKEN UYARI + YÖNLENDİRME
# ════════════════════════════════════════
*Yeni dosya: `05_urun1_uyari.py`*

## Görev 4.1 — 5 günlük ileri tahmin
```python
import datetime as dt

bugun = dt.date(2025, 12, 1)     # ornek baslangic (test doneminden)
gunler_5 = []
sayac = 0
gun = bugun
while len(gunler_5) < 5:
    # tatil ve pazar atla (istersen)
    if gun.weekday() != 6 and gun not in tam_tatiller:
        gunler_5.append(gun)
    gun = gun + dt.timedelta(days=1)

# Her gun icin ozellik satiri olustur -> hacim_tahmin -> sla_tahmin
# (ozellik satirini X'in sutun yapisina uydurman gerekecek - burada yardim isteyebilirsin)
```

## Görev 4.2 — Uyarı eşiği + renk
```python
def uyari_rengi(yuk):
    if   yuk < 33:  return "🟢 Normal"
    elif yuk < 38:  return "🟡 Dikkat"
    else:           return "🔴 Yüksek"
```

## Görev 4.3 — Yönlendirme simülasyonu
```python
# Yogun gun: hacim H1, sakin ertesi gun: hacim H2, havuz P
# Esnek islem orani (Faz 2.8): esnek_oran
# Yonlendirme hedefi: esnek islemlerin %20'si

kaydirilacak = int(H1 * esnek_oran * 0.20)

H1_yeni = H1 - kaydirilacak
H2_yeni = H2 + kaydirilacak

sla_once_1  = sla_tahmin(H1, P)
sla_sonra_1 = sla_tahmin(H1_yeni, P)
print(f"Yogun gun SLA: {sla_once_1:.2f} -> {sla_sonra_1:.2f}")
```

## Görev 4.4 — Promosyon finansal hesap
```python
komisyon       = 50      # TL / islem (varsayim)
ihlal_maliyeti = 200     # TL / SLA ihlali (varsayim)
promosyon_oran = 1.0     # kaydirilan islemlerden komisyon alinmiyor

# Yonlendirme ile onlenen ihlal sayisi (yaklasik):
onlenen_ihlal = (sla_sonra_1 - sla_once_1) * H1   # SLA artisi x hacim

kazanc  = onlenen_ihlal * ihlal_maliyeti
maliyet = kaydirilacak * komisyon * promosyon_oran
print(f"Kazanç: {kazanc:.0f} TL, Maliyet: {maliyet:.0f} TL")
print("Promosyon KÂRLI" if kazanc > maliyet else "Promosyon zararlı")
```

### ✅ KONTROL 4: Yönlendirme SLA'yı artırıyor mu, promosyon kârlılığı çıkıyor mu?

---

# ════════════════════════════════════════
# FAZ 5 — ÜRÜN 2: İZİN/KAPASİTE SİMÜLASYONU
# ════════════════════════════════════════
*Yeni dosya: `06_urun2_kapasite.py`*

## Görev 5.1 — Kapasite simülatörü
```python
NORMAL_HAVUZ = 55   # ortalama isbasi (Faz 1'den kontrol et)

def kapasite_simule(tahmini_hacim, izinli_sayisi, normal_havuz=NORMAL_HAVUZ):
    havuz = normal_havuz - izinli_sayisi
    yuk = tahmini_hacim / havuz
    return sla_tahmin(tahmini_hacim, havuz), yuk
```

## Görev 5.2 — İzin senaryoları
```python
hacim = 2000   # ornek yogun gun
for izinli in [0, 2, 4, 6]:
    sla, yuk = kapasite_simule(hacim, izinli)
    print(f"İzinli {izinli}: havuz {55-izinli}, yük {yuk:.1f}, SLA {sla:.2f}")
```
**Beklenen:** izinli arttıkça SLA düşer.

## Görev 5.3 — Güvenli/riskli gün haritası
```python
# Onumuzdeki ay icin her gunun tahmini hacmini al
# 2 kisi izin senaryosunda SLA esigin altina duserse "riskli"
ESIK = 0.90
for gun in gelecek_gunler:           # tarih listesi
    h = hacim_tahmin(...)            # o gunun tahmini
    sla, _ = kapasite_simule(h, 2)
    durum = "RİSKLİ" if sla < ESIK else "uygun"
    print(gun, durum)
```

## Görev 5.4 — Sürpriz devamsızlık
```python
# Bugun beklenmedik 2 rapor -> o gun SLA etkisi
hacim_bugun = hacim_tahmin(...)
sla_normal, _ = kapasite_simule(hacim_bugun, 0)
sla_rapor,  _ = kapasite_simule(hacim_bugun, 2)
print(f"Normal: {sla_normal:.2f}, 2 rapor sonrası: {sla_rapor:.2f}")
```

### ✅ KONTROL 5: İzinli sayısı arttıkça SLA düşüyor, riskli günler işaretleniyor.

---

# ════════════════════════════════════════
# FAZ 6 — SUNUM (STREAMLIT)
# ════════════════════════════════════════
*Yeni dosya: `app.py`. Çalıştırma: `streamlit run app.py`*

```python
import streamlit as st
import pandas as pd

st.title("Operasyonel Yoğunluk Tahmin Sistemi")

sekme = st.sidebar.radio("Ürün", ["5 Günlük Tahmin", "Yönlendirme", "İzin Simülatörü"])

if sekme == "5 Günlük Tahmin":
    st.header("Önümüzdeki 5 Gün")
    # tahmin tablosunu st.dataframe(...) ile goster
    # uyari renklerini st.write ile yaz

elif sekme == "İzin Simülatörü":
    izinli = st.slider("İzinli kişi sayısı", 0, 10, 2)
    hacim  = st.number_input("Beklenen hacim", value=2000)
    # kapasite_simule cagir, sonucu st.metric(...) ile goster
```

---

# ════════════════════════════════════════
# FAZ 7 — PORTFÖY
# ════════════════════════════════════════
- [ ] `README.md`: problem, çözüm, mimari, sonuç, görseller
- [ ] "Veri sentetik" notu, sektör-bağımsız dil
- [ ] GitHub'a yükle
- [ ] LinkedIn paylaşımı

---

# 🗺️ AKIŞ
```
FAZ 0 → 1 → 2 → 3 → ÜRÜN 1 (4) → ÜRÜN 2 (5) → Sunum (6) → Portföy (7)
```
**Önce 0-4'ü bitir, çalışan Ürün 1 elde et. Sonra Ürün 2.**

## Çalışma şekli
- Her `____` boşluğunu sen doldur
- Takıldığında "Görev X.Y" diye sor
- Her kontrol noktasında dur, doğrula, ilerle
- Faz 1.6 tatil set'ini benden iste
