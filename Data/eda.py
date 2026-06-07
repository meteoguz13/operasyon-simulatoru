import sys
sys.path.append(r"C:\Users\meteoguz\PycharmProjects\Operation\Data")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from yardimci import tam_tatiller, arifeler, sla_tahmin, uyari_rengi


pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 500)

gunluk = pd.read_csv("gunluk_ozet.csv", encoding="utf-8-sig")
gunluk["baslama_tarihi"] = pd.to_datetime(gunluk["baslama_tarihi"])
df_islem = pd.read_csv(r"C:\Users\meteoguz\PycharmProjects\Operation\Data\islem_detay (1).csv", encoding="utf-8-sig")


#####################  FAZ 2 — KEŞİFSEL ANALİZ (EDA)


gunluk.head()

print(gunluk["gun_adi"].unique())


gun_sira = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

gun_ort = gunluk.groupby("gun_adi")["gunluk_hacim"].mean()
gun_ort = gun_ort.reindex(gun_sira)

print(gun_ort)


plt.figure(figsize=(8,4))
gun_ort.plot(kind="bar")
plt.title("Gün Bazında Ortalama Hacim")
plt.ylabel("İşlem")
plt.show(block=True)

aylik = gunluk.groupby(["yil", "ay_no"])["gunluk_hacim"].mean().reset_index()
plt.figure(figsize=(10,4))
for y in [2024, 2025]:
    alt = aylik[aylik["yil"]==y]
    plt.plot(alt["ay_no"], alt["gunluk_hacim"], marker = "o", label=str(y))
plt.legend(); plt.title("Aylık Ortalama Hacim"); plt.xlabel("Ay")
plt.show(block=True)


gunluk.groupby("tatil_oncesi_mi")["gunluk_hacim"].mean()
gunluk.groupby("ay_sonu_mu")["gunluk_hacim"].mean()

plt.figure(figsize=(8,5))
plt.scatter(gunluk["kisi_basi_yuk"], gunluk["sla_oran"], alpha=0.3)
plt.xlabel("Kişi Başına Yük"); plt.ylabel("SLA Oranı")
plt.title("Yük Arttıkça SLA Düşüyor mu?")
plt.show(block=True)


kor = gunluk["kisi_basi_yuk"].corr(gunluk["sla_oran"])
print("Korelasyon", kor)

gunluk["yuk_grup"] = pd.qcut(
    gunluk["kisi_basi_yuk"], 4,
    labels=["Düşük","Orta","Yüksek","Çok Yüksek"]
)
print(gunluk.groupby("yuk_grup", observed=True)["sla_oran"].mean())

seg_gun = gunluk.groupby("gun_adi")[["seg_kurumsal","seg_kobi","seg_bireysel"]].mean()
seg_gun = seg_gun.reindex(gun_sira)
seg_gun.plot(kind= "bar", figsize=(10,5))
plt.title("Gün Bazında Segment Ortalaması")
plt.show(block=True)

gunluk["esnek_islem"] = gunluk["seg_bireysel"] + gunluk["seg_kobi"]
gunluk["esnek_oran"] = gunluk["esnek_islem"] / gunluk["gunluk_hacim"]
print("Ortalama esnek oran:", gunluk["esnek_oran"].mean())


musteri = df_islem.groupby("musteri_id").agg(
    islem_sayisi = ("islem_id", "count"),
    tip          = ("musteri_tipi","first"),
    farkli_gun   = ("baslama_tarihi", "nunique"),
).reset_index()

musteri.head()

musteri["yayilim"] = musteri["farkli_gun"] / musteri["islem_sayisi"]

aciliyet = df_islem.groupby("musteri_id")["gercek_sure_dk"].mean()
musteri = musteri.merge(aciliyet.rename("ort_sure"), on="musteri_id")

musteri.head()

print(musteri.groupby("tip")["yayilim"].mean())
gun_dagilim = df_islem.groupby(["musteri_tipi","baslama_gun"]).size().unstack(fill_value=0)
gun_oran = gun_dagilim.div(gun_dagilim.sum(axis=1), axis=0)
print(gun_oran.round(2))

def esneklik_skoru(row):
    if   row["yayilim"] > 0.70:  return 2
    elif row["yayilim"] > 0.40:  return 1
    else:                        return 0
musteri["esneklik"] = musteri.apply(esneklik_skoru, axis=1)


def segment(skor):
    if   skor == 2:  return "Esnek"
    elif skor == 1:  return "Orta"
    else:            return "Esnek Değil"
musteri["segment"] = musteri["esneklik"].apply(segment)


print(musteri["segment"].value_counts())
print(musteri.groupby("segment")["islem_sayisi"].sum())
musteri.to_csv("musteri_segment.csv", index=False, encoding="utf-8-sig")

musteri.head()

df_islem = df_islem.merge(musteri[["musteri_id", "segment"]], on="musteri_id", how="left")
print(df_islem[["islem_id","musteri_id","segment"]].head())

gun_segment =(
    df_islem.groupby(["baslama_tarihi", "segment"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
print(gun_segment.head())


gun_segment["baslama_tarihi"] = pd.to_datetime(gun_segment["baslama_tarihi"])
gunluk["baslama_tarihi"] = pd.to_datetime(gunluk["baslama_tarihi"])
gunluk = gunluk.merge(
    gun_segment[["baslama_tarihi","Esnek","Orta","Esnek Değil"]],
    on="baslama_tarihi",
    how="left"
)
gunluk.head()


ORTA_ESNEKLIK = 0.5        # orta segmentin %50'si yönlendirilebilir
KURUMSAL_ESNEKLIK = 0.10   # kurumsalın %10'u (müşteri ilişkileri/teşvikle), temkinli varsayım

gunluk["yonlendirilebilir"] = (
    gunluk["Esnek"]
    + gunluk["Orta"] * ORTA_ESNEKLIK
    + gunluk["Esnek Değil"] * KURUMSAL_ESNEKLIK
)
print(gunluk[["baslama_tarihi","gunluk_hacim","Esnek","Orta","Esnek Değil","yonlendirilebilir"]].head())
gunluk.to_csv("gunluk_ozet.csv", index=False, encoding="utf-8-sig")
















