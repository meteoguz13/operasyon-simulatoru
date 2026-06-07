import datetime as dt
import calendar

# --- Tatil setleri ---
tam_tatiller = {
    "2024-01-01","2024-04-10","2024-04-11","2024-04-12","2024-04-23",
    "2024-05-01","2024-05-19","2024-06-16","2024-06-17","2024-06-18",
    "2024-06-19","2024-07-15","2024-08-30","2024-10-29",
    "2025-01-01","2025-03-30","2025-03-31","2025-04-01","2025-04-23",
    "2025-05-01","2025-05-19","2025-06-06","2025-06-07","2025-06-08",
    "2025-06-09","2025-07-15","2025-08-30","2025-10-29",
}
arifeler = {
    "2024-04-09","2024-06-15","2024-10-28","2024-12-31",
    "2025-03-29","2025-06-05","2025-10-28",
}
tam_tatiller = {dt.date.fromisoformat(x) for x in tam_tatiller}
arifeler = {dt.date.fromisoformat(x) for x in arifeler}

# --- SLA tahmin fonksiyonu ---
def sla_tahmin(hacim, havuz):
    yuk = hacim / havuz
    sla = 1.1296 - 0.006522 * yuk
    # SLA 0-1 arasinda kalmali (uc degerlerde tasmasin)
    return max(0.0, min(1.0, sla))

# --- Uyari rengi ---
def uyari_rengi(yuk):
    if   yuk < 34.5:  return "🟢 Normal"
    elif yuk < 41.4:  return "🟡 Dikkat"
    else:             return "🔴 Kritik"