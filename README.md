# Operasyonel Yoğunluk Tahmin ve Verimlilik Simülatörü

🔴 **Canlı Demo:** [operasyon-simulatoru.streamlit.app](https://operasyon-simulatoru.streamlit.app)

Operasyon merkezlerinde günlük iş yoğunluğunu önceden tahmin eden ve "ya şöyle yapsaydık?" sorusunu veriyle yanıtlayan bir karar destek aracı.

> **Not:** Bu bir portföy projesidir. Gerçek kurumsal veri gizlilik nedeniyle kullanılamayacağı için, gerçek operasyonel paternleri taklit eden **sentetik bir veri seti** üretilmiştir. Finansal parametreler varsayımdır; amaç yöntemi ve yaklaşımı göstermektir.

---

## Problem

Operasyon ekiplerinde kararlar çoğu zaman tepkisel ve sezgiseldir: "Yarın yoğun olur herhalde", "bugün izin versek olur mu?". Oysa operasyonel yoğunluk büyük ölçüde **öngörülebilir** bir şeydir — haftanın günü, ay sonu, resmi tatil öncesi gibi paternler tekrar eder. Sorun belirsizlik değil, bu paterni sistematik kullanan bir aracın olmamasıdır.

Bu proje şu soruyu test eder: **Operasyonel yoğunluk veriyle tahmin edilip proaktif yönetilebilir mi?**

---

## Veri

7/24 çalışan bir operasyon merkezini temsil eden, yaklaşık **1.4 milyon işlemlik** sentetik bir veri seti üretildi. Veri, gerçek hayattaki davranışları içerecek şekilde tasarlandı:

- **Haftalık ritim:** Belirli günler yoğun, Pazar sakin
- **Ay sonu yığılması:** Ay kapanışına doğru artan hacim
- **Tatil öncesi patlamalar:** Resmi tatillerden önce işlerin yetiştirilmesi
- **Müşteri çeşitliliği:** Kurumsal, KOBİ ve bireysel müşterilerin farklı davranışları
- **Personel devamsızlığı:** İzin ve raporların günlük kapasiteye etkisi
- **Gerçekçi gürültü:** Her güne öngörülemez bir dalgalanma

---

## Çözüm — Üç Katman

### 1. Tahmin Motoru
Hangi gün ne kadar iş geleceğini öngören bir makine öğrenmesi modeli (RandomForest).

Geliştirme sırasında öğretici bir engelle karşılaşıldı: işlem hacmi yıldan yıla büyüyordu ve standart model bu büyümeyi yakalayamıyor, sürekli eksik tahmin ediyordu. Çözüm, soruyu değiştirmek oldu: modele "kaç işlem gelecek?" yerine **"normale göre kaç kat iş gelecek?"** diye soruldu. Bu oran yıldan bağımsız olduğu için model artık durağan bir şey öğreniyor; güncel seviyeyle çarpılınca doğru hacme ulaşılıyor.

Bu değişiklikle tahmin hatası **yarıya indi** ve sistematik sapma ortadan kalktı.

### 2. What-If Simülatörü
Bir yönetici panosu (Streamlit). Kullanıcı bir gün seçer, ekip sayısı ve iş yönlendirme oranıyla oynar; sistem anında gösterir:
- Kişi başına yük ne olur
- SLA (işlerin zamanında bitme oranı) nasıl değişir
- Kaç iş daha zamanında biter

### 3. Optimum ve Yıllık Planlama
- **Günlük optimum:** Hedeflenen hizmet seviyesini tutturan en uygun ayarı sistem kendisi bulur
- **Yıllık planlama:** Bir yıl için gereken sabit kadroyu hesaplar; "SLA hedefini tutturmak için kaç kişi gerekir?" sorusunu yanıtlar

---

## Modelin Doğrulanması

Bir modelin "iyi" olduğunu söylemek yetmez; kanıtlamak gerekir. Üç yöntemle test edildi:

- **Baseline karşılaştırması:** Model, basit tahmin yöntemlerinden (geçen haftanın aynı günü, gün ortalaması) **yaklaşık %50 daha isabetli** çıktı. Yani gerçekten patern öğreniyor, ezbere tahmin yapmıyor.
- **Hata analizi:** Modelin nerede güçlü, nerede zayıf olduğu incelendi. Normal günlerde hata düşük; nadir uç günlerde (tatil öncesi) artıyor — çünkü bu günler hem az sayıda hem aşırı oynak. Bu bilinen ve kabul edilen bir sınır.
- **Güven aralığı:** Model sadece tek bir sayı değil, bir tahmin aralığı da veriyor. Normal günlerde aralık dar (model emin), oynak günlerde geniş (model belirsizliğini biliyor).

---

## En İlginç Bulgu

"Daha çok önlem her zaman daha iyidir" varsayımı yanlış çıktı.

Bazı günlerde iş yönlendirmesi fayda yerine zarar veriyor. Bazı günlerde ise hiçbir önlem yetmiyor ve kapasite artışı şart oluyor. Simülatör, sezgiye aykırı olsa bile en mantıklı kararı veriyle gösteriyor — yöneticinin tek başına göremeyeceği dengeyi ortaya koyuyor.

---

## Nerede Kullanılabilir?

Talebin dalgalandığı ve insan kapasitesinin planlandığı her alan:
- Bankacılık operasyonları
- Çağrı merkezleri
- Lojistik ve kargo
- E-ticaret müşteri destek
- Sağlık (poliklinik/acil yoğunluğu)

---

## Kullanılan Teknolojiler

`Python` · `pandas` · `scikit-learn` · `Streamlit`

---

## Çalıştırma

```bash
pip install -r requirements.txt
streamlit run app.py
```

> Uygulama veri dosyalarını okuyarak çalışır. Veri üretim ve hazırlık adımları proje dosyalarında yer almaktadır.

---

## Dürüst Sınırlar

Bu projenin neyi yapıp neyi yapmadığı konusunda net olmak önemli:

- **Veri sentetiktir.** Gerçek dünyada paternler daha gürültülü olabilir; buradaki başarı oranları gerçek veride farklılık gösterebilir.
- **Finansal parametreler varsayımdır.** Optimizasyon, parasal getiri yerine operasyonel hedefe (hizmet seviyesi + minimum kaynak) dayandırılmıştır.
- **Uzak gelecek tahmini sabit bir seviye kullanır.** Canlı bir sistemde bu seviye her gün güncellenir ve büyüme trendi otomatik yakalanır.

**Sonraki adımlar:** Gerçek veriyle kalibrasyon, canlı tahmin entegrasyonu, finansal getiri katmanı.

---

## Kapanış

Bu proje şunu gösterdi: Operasyonu "öngörülemez" yapan şey çoğu zaman verinin yokluğu değil, kullanılmamasıdır. Doğru soru sorulduğunda, yoğunluk hem tahmin edilebilir hem de yönetilebilir hale geliyor.
