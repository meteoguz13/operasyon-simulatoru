# Operasyonel Yoğunluk Tahmin ve Verimlilik Simülatörü

Operasyon merkezleri için günlük işlem yoğunluğunu tahmin eden ve 
ekip/yönlendirme senaryolarını test eden bir karar destek aracı.

Veriye dayalı, proaktif operasyon yönetimini göstermek için geliştirilmiş 
bir portföy projesidir. Sentetik veri kullanır (gerçek veri gizlilik nedeniyle paylaşılamaz).

## Ne yapar?

- **Tahmin:** Hangi gün ne kadar işlem geleceğini öngörür (oran bazlı RandomForest, MAE ~174, basit yöntemlerden %50 daha isabetli)
- **Simülatör:** Ekip sayısı ve iş yönlendirmesiyle oynayıp yük ve SLA etkisini anında gösterir
- **Optimum:** SLA hedefini tutturan en uygun ayarı bulur
- **Yıllık planlama:** Bir yıl için gereken kadroyu hesaplar

## Teknolojiler

Python, pandas, scikit-learn, Streamlit

## Çalıştırma

## Not

Veri seti sentetiktir; finansal parametreler varsayımdır. Detaylı 
dokümantasyon ve teknik açıklamalar yakında eklenecektir.
