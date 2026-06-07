import sys
sys.path.append(r"C:\Users\meteoguz\PycharmProjects\Operation\Data")
import pandas as pd, numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import calendar
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from yardimci import tam_tatiller, arifeler, sla_tahmin, uyari_rengi

pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 500)
gunluk = pd.read_csv("gunluk_ozet.csv", encoding="utf-8-sig")


gunluk["baslama_tarihi"] = pd.to_datetime(gunluk["baslama_tarihi"])
gunluk = gunluk.sort_values("baslama_tarihi").reset_index(drop=True)

gunluk["ma_14"] = gunluk["gunluk_hacim"].shift(1).rolling(14).mean()
gunluk = gunluk.dropna().reset_index(drop=True)

gunluk["oran"] = gunluk["gunluk_hacim"] / gunluk["ma_14"]

gunluk.head()

ozellikler = gunluk[["gun_adi", "ay_no", "tatil_oncesi_mi", "ay_sonu_mu", "arife_mi"]].copy()
ozellikler = pd.get_dummies(ozellikler, columns=["gun_adi", "ay_no"])

X = ozellikler
y = gunluk["oran"]

egitim_set = gunluk["yil"] == 2024
test_set = gunluk["yil"]== 2025

X_train, y_train = X[egitim_set], y[egitim_set]
X_test,  y_test  = X[test_set],  y[test_set]
print("Egitim:", X_train.shape, "Test:", X_test.shape)

rf = RandomForestRegressor(n_estimators=300, random_state=42)
rf.fit(X_train, y_train)
tahmin_rf = rf.predict(X_test)
mae_rf = mean_absolute_error(y_test, tahmin_rf)
print("RF MAE:", mae_rf)
onem = pd.Series(rf.feature_importances_, index=X.columns). sort_values(ascending=False)
print(onem.head(10))


# Tahmini oran x o gunun guncel seviyesi = hacim tahmini
seviye_test = gunluk[test_set]["ma_14"].values
hacim_tahmin = tahmin_rf * seviye_test

# Gercek hacim
gercek_hacim = gunluk[test_set]["gunluk_hacim"].values


mae = mean_absolute_error(gercek_hacim, hacim_tahmin)
print("MAE:", round(mae), " (~", round(mae/25,1), "kisi)")


# ========== BASELINE KARŞILAŞTIRMASI ==========
# Modelin gerçekten değer kattığını kanıtlamak için 2 basit yöntemle kıyasla

# Baseline 1: "Naive" — geçen haftanın aynı günü (7 gün önceki hacim)
gunluk["naive_7"] = gunluk["gunluk_hacim"].shift(7)
naive_test = gunluk[test_set].dropna(subset=["naive_7"])
mae_naive = mean_absolute_error(naive_test["gunluk_hacim"], naive_test["naive_7"])

# Baseline 2: "Ortalama" — her günün geçmiş ortalaması (gün adına göre)
gun_ort = gunluk[egitim_set].groupby("gun_adi")["gunluk_hacim"].mean()
ort_tahmin = gunluk[test_set]["gun_adi"].map(gun_ort)
mae_ort = mean_absolute_error(gunluk[test_set]["gunluk_hacim"], ort_tahmin)

# Karşılaştırma tablosu
print("\n===== MODEL KARŞILAŞTIRMASI (2025 test, MAE) =====")
print(f"Naive (geçen haftanın aynı günü) : {mae_naive:6.0f}")
print(f"Gün ortalaması (basit)           : {mae_ort:6.0f}")
print(f"Oran bazlı RandomForest (bizim)  : {mae:6.0f}")
print(f"\nModelimiz naive'den %{(1-mae/mae_naive)*100:.0f} daha iyi")
print(f"Modelimiz ortalamadan %{(1-mae/mae_ort)*100:.0f} daha iyi")

# ========== HATA ANALİZİ — MODEL NEREDE YANILIYOR? ==========
# Tahmin hatasını gün tipine göre kır, modelin güçlü/zayıf olduğu yerleri gör

analiz = gunluk[test_set].copy()
analiz["tahmin"] = hacim_tahmin
analiz["hata"] = analiz["tahmin"] - analiz["gunluk_hacim"]       # +: fazla tahmin, -: eksik
analiz["mutlak_hata"] = analiz["hata"].abs()
analiz["yuzde_hata"] = (analiz["mutlak_hata"] / analiz["gunluk_hacim"] * 100)

# 1) Gün adına göre hata
print("\n===== GÜN ADINA GÖRE ORTALAMA HATA (%) =====")
print(analiz.groupby("gun_adi")["yuzde_hata"].mean().round(1).sort_values())

# 2) Özel gün tipine göre hata
print("\n===== GÜN TİPİNE GÖRE ORTALAMA HATA (%) =====")
for kolon, etiket in [("tatil_oncesi_mi","Tatil öncesi"), ("ay_sonu_mu","Ay sonu"), ("arife_mi","Arife")]:
    normal = analiz[analiz[kolon]==0]["yuzde_hata"].mean()
    ozel   = analiz[analiz[kolon]==1]["yuzde_hata"].mean()
    print(f"{etiket:15s} | Normal: %{normal:.1f}  |  Özel gün: %{ozel:.1f}")

# 3) Yön (bias) kontrolü — sistematik eksik/fazla var mı?
print("\n===== SAPMA (BIAS) =====")
print(f"Ortalama hata (işaretli): {analiz['hata'].mean():+.0f} işlem")
print(f"(0'a yakın = sistematik sapma yok, dengeli tahmin)")

# 4) En çok yanıldığı 5 gün
print("\n===== MODELİN EN ÇOK YANILDIĞI 5 GÜN =====")
en_kotu = analiz.nlargest(5, "mutlak_hata")[["baslama_tarihi","gun_adi","gunluk_hacim","tahmin","hata"]]
print(en_kotu.to_string(index=False))


# Sapma (bias) kontrol -> ~0 olmali
print("Ort gercek:", round(gercek_hacim.mean()))
print("Ort tahmin:", round(hacim_tahmin.mean()))

test_tarih = gunluk[test_set]["baslama_tarihi"]
plt.figure(figsize=(14,4))
plt.plot(test_tarih, gercek_hacim, label="Gerçek", alpha=0.7)
plt.plot(test_tarih, hacim_tahmin, label="Tahmin", alpha=0.7)
plt.legend(); plt.title("2025 Gerçek vs Tahmin")
plt.show(block=True)


gunluk["yuk_grup"], sinirlar = pd.qcut(
    gunluk["kisi_basi_yuk"], 4,
    labels=["Düşük","Orta","Yüksek","Çok Yüksek"],
    retbins=True
)
print("Sınırlar:", sinirlar)
print(gunluk.groupby("yuk_grup", observed=True)["sla_oran"].mean())



def hacim_tahmin_fonk(ozellik_satiri, guncel_seviye):
    oran = rf.predict(ozellik_satiri)[0]
    return oran * guncel_seviye

# X_test'in ilk satırıyla test et
ornek = X_test.iloc[[0]]
ornek_seviye = gunluk[test_set]["ma_14"].iloc[0]
print("Tahmin:", hacim_tahmin_fonk(ornek, ornek_seviye))
print("Gerçek:", gercek_hacim[0])



from sklearn.linear_model import LinearRegression

# Yük -> SLA dogrusal iliski (gunluk veriden ogren)
yuk_X = gunluk[["kisi_basi_yuk"]]      # girdi: yük
sla_y = gunluk["sla_oran"]              # çıktı: SLA

sla_model = LinearRegression()
sla_model.fit(yuk_X, sla_y)

print("Eğim (yük arttıkça SLA değişimi):", sla_model.coef_[0])
print("Sabit:", sla_model.intercept_)


# ========== TAHMİN + GÜVEN ARALIĞI ==========
# RandomForest = 300 ağacın ortalaması. Ağaçların dağılımı = belirsizlik.

def tahmin_araligi(ozellik_satiri, guncel_seviye):
    X_np = ozellik_satiri.values   # DataFrame -> numpy (isim uyarısını keser)
    agac_tahminleri = np.array([t.predict(X_np)[0] for t in rf.estimators_])
    hacimler = agac_tahminleri * guncel_seviye
    ortalama = hacimler.mean()
    std = hacimler.std()
    alt = ortalama - 1.645 * std
    ust = ortalama + 1.645 * std
    return ortalama, alt, ust

# Test: birkaç gün için aralık göster
print("\n===== TAHMİN GÜVEN ARALIĞI (örnek günler) =====")
for i in [0, 50, 100]:
    ornek = X_test.iloc[[i]]
    seviye_i = gunluk[test_set]["ma_14"].iloc[i]
    tarih_i = gunluk[test_set]["baslama_tarihi"].iloc[i].date()
    ort, alt, ust = tahmin_araligi(ornek, seviye_i)
    gercek_i = gunluk[test_set]["gunluk_hacim"].iloc[i]
    print(f"{tarih_i} | Tahmin: {ort:.0f}  Aralık: [{alt:.0f} - {ust:.0f}]  | Gerçek: {gercek_i}")


# ====== FAZ 4 - ÜRÜN 1 ======
gunler_5 = []
gun = dt.date(2025, 1, 1)
while len(gunler_5) < 5:
    if gun not in tam_tatiller:
        gunler_5.append(gun)
    gun = gun + dt.timedelta(days=1)

print(gunler_5)

panel = gunluk[test_set].copy()
panel["tahmini_hacim"] = hacim_tahmin
panel["tahmini_yuk"] = panel["tahmini_hacim"] / panel["isbasi_sayi"]

ilk5 = panel.head(5).copy()

ilk5["tahmini_sla"] = ilk5.apply(
    lambda r: sla_tahmin(r["tahmini_hacim"], r["isbasi_sayi"]), axis=1
)
ilk5["uyari"] = ilk5["tahmini_yuk"].apply(uyari_rengi)
print(ilk5[["baslama_tarihi","gun_adi","tahmini_hacim","isbasi_sayi","tahmini_yuk","tahmini_sla","uyari"]])


en_yogun5 = panel.sort_values("tahmini_yuk", ascending=False).head(5).copy()
en_yogun5["tahmini_sla"] = en_yogun5.apply(
    lambda r: sla_tahmin(r["tahmini_hacim"], r["isbasi_sayi"]), axis=1
)
en_yogun5["uyari"] = en_yogun5["tahmini_yuk"].apply(uyari_rengi)
print(en_yogun5[["baslama_tarihi","gun_adi","tahmini_hacim","isbasi_sayi","tahmini_yuk","tahmini_sla","uyari"]])


panel["yonlendirilebilir"] = gunluk[test_set]["yonlendirilebilir"].values
yogun = panel.sort_values("tahmini_yuk", ascending=False).iloc[0]
print("Yoğun gün:", yogun["baslama_tarihi"], "Yük:", round(yogun["tahmini_yuk"],1))


YONLENDIRME_ORANI = 0.20
kaydirilacak = int(yogun["yonlendirilebilir"] * YONLENDIRME_ORANI)
print("Kaydırılacak işlem:", kaydirilacak)

H_once  = yogun["tahmini_hacim"]
P       = yogun["isbasi_sayi"]
H_sonra = H_once - kaydirilacak

sla_once  = sla_tahmin(H_once,  P)
sla_sonra = sla_tahmin(H_sonra, P)

print(f"Hacim: {H_once:.0f} -> {H_sonra:.0f}")
print(f"SLA:   {sla_once:.3f} -> {sla_sonra:.3f}")


orta_yogun = panel[(panel["tahmini_yuk"] > 35) & (panel["tahmini_yuk"] < 42)].iloc[0]
kaydirilacak = int(orta_yogun["yonlendirilebilir"] * 0.20)
H_once = orta_yogun["tahmini_hacim"]
P = orta_yogun["isbasi_sayi"]
H_sonra = H_once - kaydirilacak
print(f"Hacim: {H_once:.0f} -> {H_sonra:.0f}")
print(f"SLA:   {sla_tahmin(H_once,P):.4f} -> {sla_tahmin(H_sonra,P):.4f}")

def simule(tahmini_hacim, baz_ekip, yeni_ekip, yonlendirme_orani,
           yonlendirilebilir_islem,
           komisyon=50, ihlal_maliyeti=200, gunluk_maas=1500):

    # --- BAZ DURUM (mevcut ekip, yönlendirme yok) ---
    baz_yuk = tahmini_hacim / baz_ekip
    baz_sla = sla_tahmin(tahmini_hacim, baz_ekip)

    # --- SENARYO (yönlendirme + yeni ekip) ---
    kaydirilan = int(yonlendirilebilir_islem * yonlendirme_orani)
    senaryo_hacim = tahmini_hacim - kaydirilan
    senaryo_yuk = senaryo_hacim / yeni_ekip
    senaryo_sla = sla_tahmin(senaryo_hacim, yeni_ekip)

    # --- FİNANSAL: SLA iyileşme kazancı ---
    kurtarilan_islem = (senaryo_sla - baz_sla) * tahmini_hacim
    sla_kazanci = kurtarilan_islem * ihlal_maliyeti

    # --- FİNANSAL: maliyetler ---
    promosyon_maliyeti = kaydirilan * komisyon
    personel_maliyeti  = (yeni_ekip - baz_ekip) * gunluk_maas

    # --- NET ETKİ ---
    net = sla_kazanci - promosyon_maliyeti - personel_maliyeti

    return {
        "baz_yuk": round(baz_yuk,1), "senaryo_yuk": round(senaryo_yuk,1),
        "baz_sla": round(baz_sla,3), "senaryo_sla": round(senaryo_sla,3),
        "kaydirilan": kaydirilan,
        "sla_kazanci": round(sla_kazanci),
        "promosyon_maliyeti": round(promosyon_maliyeti),
        "personel_maliyeti": round(personel_maliyeti),
        "net_etki": round(net)
    }


sonuc = simule(
    tahmini_hacim=2176, baz_ekip=59, yeni_ekip=64,
    yonlendirme_orani=0.20, yonlendirilebilir_islem=440
)
for k, v in sonuc.items():
    print(k, ":", v)


# Sadece yönlendirme, ekip eklemeden (yeni_ekip = baz_ekip)
print(simule(2176, 59, 59, 0.20, 440)["net_etki"])
# Sadece ekip ekleme, yönlendirme yok
print(simule(2176, 59, 64, 0.0, 440)["net_etki"])
# İkisi birden
print(simule(2176, 59, 64, 0.20, 440)["net_etki"])





































