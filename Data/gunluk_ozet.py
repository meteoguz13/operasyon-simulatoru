from operator import index

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import datetime as dt
import calendar
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

pd.set_option('display.expand_frame_repr', False)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 500)

df_islem = pd.read_csv(r"C:\Users\meteoguz\PycharmProjects\Operation\Data\islem_detay (1).csv")
df_cal = pd.read_csv(r"C:\Users\meteoguz\PycharmProjects\Operation\Data\calisan_detay (1).csv")

df_islem["baslama_tarihi"] = pd.to_datetime(df_islem["baslama_tarihi"])
df_islem["tamamlama_tarihi"] = pd.to_datetime(df_islem["tamamlama_tarihi"])
df_cal["tarih"] = pd.to_datetime(df_cal["tarih"])


def check_df(df):
    print("##############--Shape--##############")
    print(df.shape)
    print("#############--Head--##############")
    print(df.head())
    print("##############--Tail--##############")
    print(df.tail())
    print("##############--Dtypes--##############")
    print(df.dtypes)
    print("##############--Describe--##############")
    print(df.describe(percentiles=[0.05, 0.10, 0.15, 0.25, 0.40, 0.50, 0.60, 0.75, 0.90, 0.95]))
    print("##############--NA--##############")
    print(df.isnull().sum())

check_df(df_islem)
check_df(df_cal)

#####################  FAZ 1 -- GÜNLÜK ÖZET TABLOSU

gunluk = df_islem.groupby("baslama_tarihi").agg(
    gunluk_hacim = ("islem_id", "count"),
    havuz_kisi = ("havuz_kisi_sayisi", "first"),
    sla_oran = ("hedefte_bitti", "mean"),
    ort_gecikme = ("gecikme_dk", "mean"),
).reset_index()

print(gunluk.head())
print(gunluk.tail())

tip_gunluk = (
    df_islem.groupby(["baslama_tarihi","islem_tipi"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)
print(tip_gunluk.head())

gunluk = pd.merge(gunluk, tip_gunluk, on="baslama_tarihi", how="left")
print(gunluk.head())

seg_gunluk = (
    df_islem.groupby(["baslama_tarihi","musteri_tipi"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

seg_gunluk = seg_gunluk.rename(columns={
    "kurumsal": "seg_kurumsal",
    "KOBİ": "seg_kobi",
    "bireysel": "seg_bireysel"
})

print(seg_gunluk.head())

gunluk = pd.merge(gunluk, seg_gunluk, on="baslama_tarihi", how="left")
print(gunluk.head())



durum_gunluk = (
    df_cal.groupby(["tarih", "durum"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

durum_gunluk = durum_gunluk.rename(columns={
    "işbaşı":  "isbasi_sayi",
    "izinli":  "izinli_sayi",
    "raporlu": "raporlu_sayi"
})
print(durum_gunluk.head())


gunluk = pd.merge(gunluk, durum_gunluk, left_on="baslama_tarihi", right_on="tarih", how="left")
print(gunluk.head())

gunluk["gun_adi"]   = gunluk["baslama_tarihi"].dt.day_name()
gunluk["ay_no"]     = gunluk["baslama_tarihi"].dt.month
gunluk["yil"]       = gunluk["baslama_tarihi"].dt.year
gunluk["ayin_gunu"] = gunluk["baslama_tarihi"].dt.day
gunluk["hafta"]     = gunluk["baslama_tarihi"].dt.isocalendar().week


# Tam tatiller (işlem yok)
tam_tatiller = {
    # 2024
    "2024-01-01",
    "2024-04-10", "2024-04-11", "2024-04-12",
    "2024-04-23", "2024-05-01", "2024-05-19",
    "2024-06-16", "2024-06-17", "2024-06-18", "2024-06-19",
    "2024-07-15", "2024-08-30", "2024-10-29",
    # 2025
    "2025-01-01",
    "2025-03-30", "2025-03-31", "2025-04-01",
    "2025-04-23", "2025-05-01", "2025-05-19",
    "2025-06-06", "2025-06-07", "2025-06-08", "2025-06-09",
    "2025-07-15", "2025-08-30", "2025-10-29",
}

# Arifeler (yarım gün - işlem var ama düşük)
arifeler = {
    "2024-04-09", "2024-06-15", "2024-10-28", "2024-12-31",
    "2025-03-29", "2025-06-05", "2025-10-28",
}

# İkisini de date'e çevir
tam_tatiller = {dt.date.fromisoformat(x) for x in tam_tatiller}
arifeler     = {dt.date.fromisoformat(x) for x in arifeler}

gunluk["arife_mi"] = gunluk["baslama_tarihi"].apply(
    lambda x: 1 if x.date() in arifeler else 0
)
gunluk["tatil_mi"] = gunluk["baslama_tarihi"].apply(
    lambda x: 1 if x.date() in tam_tatiller else 0
)

# tatil_oncesi_mi: ertesi 1 veya 2 gun tatil mi?
def tatil_oncesi(tarih):
    yarin     = tarih.date() + dt.timedelta(days=1)
    obur_gun  = tarih.date() + dt.timedelta(days=2)
    if yarin in tam_tatiller or obur_gun in tam_tatiller:
        return 1
    return 0

gunluk["tatil_oncesi_mi"] = gunluk["baslama_tarihi"].apply(tatil_oncesi)

# ay_sonu_mu: ayin son 3 gunu mu?
def ay_sonu(tarih):
    son_gun = calendar.monthrange(tarih.year, tarih.month)[1]
    return 1 if tarih.day >= son_gun - 2 else 0

gunluk["ay_sonu_mu"] = gunluk["baslama_tarihi"].apply(ay_sonu)

print(gunluk[gunluk["tatil_oncesi_mi"] == 1][["baslama_tarihi", "gunluk_hacim"]].head(10))
print(gunluk[gunluk["arife_mi"] == 1][["baslama_tarihi", "gunluk_hacim"]])

gunluk.head()

gunluk["kisi_basi_yuk"] = gunluk["gunluk_hacim"] / gunluk["havuz_kisi"]
gunluk.head()


gunluk.to_csv("gunluk_ozet.csv", index=False, encoding="utf-8-sig")
print("Kaydedildi:", gunluk.shape)






















