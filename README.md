# QoS Multi-Objective Routing

250 düğümlü ağlarda QoS odaklı çok amaçlı rotalama optimizasyonu için PyQt5 masaüstü uygulaması.

## Özellikler

- **6 Optimizasyon Algoritması**: Genetic Algorithm, ACO, PSO, Simulated Annealing, Q-Learning, SARSA
- **CSV Veri Yükleme**: Hocanın verdiği graph_data klasöründen otomatik yükleme
- **Graf Görselleştirme**: 250+ düğümlü grafları sorunsuz görselleştirme
- **Toplu Deneyler**: Experiment runner ile çoklu test senaryoları
- **Karşılaştırmalı Analiz**: Tüm algoritmaları aynı anda karşılaştırma

## Hızlı Başlangıç

```bash
cd app
pip install -r requirements.txt
python main.py
```

## Kullanım

1. **Graf Yükleme**: "Proje Verisini Yükle (CSV)" butonuna tıklayın veya rastgele graf oluşturun
2. **Kaynak/Hedef Seçimi**: Graf üzerinde tıklayarak veya panelden manuel seçin
3. **Optimizasyon**: Algoritma seçip optimize edin veya tüm algoritmaları karşılaştırın

## Proje Yapısı

```
QoS-Multi-Objective-Routing/
├── app/                    # Ana uygulama
│   ├── main.py            # Giriş noktası
│   ├── src/
│   │   ├── algorithms/    # 6 optimizasyon algoritması
│   │   ├── experiments/   # Deney framework'ü
│   │   ├── services/      # Graf ve metrik servisleri
│   │   └── ui/            # PyQt5 arayüz bileşenleri
│   └── requirements.txt
└── graph_data/            # CSV veri dosyaları (proje kökünde)
```

## Gereksinimler

- Python 3.8+
- PyQt5
- NetworkX
- NumPy
- PyQtGraph

Detaylar için `app/README.md` dosyasına bakın.
