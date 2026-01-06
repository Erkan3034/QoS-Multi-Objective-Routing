# QoS Odaklı Rotalama Projesi
## Proje Özeti

---

## 1. Proje Kimliği ve Hedefler

| Özellik | Değer |
|---------|-------|
| **Proje** | QoS Odaklı Çok Amaçlı Rotalama (Meta-Sezgisel ve RL Yaklaşımları) |
| **Süre** | 5 Hafta |
| **Teslimat Türü** | Masaüstü uygulaması (PyQt5) + Rapor |

### Amaçlar

| # | Amaç | Açıklama |
|---|------|----------|
| 1 | **Simülasyon Ortamı** | 250 düğümlü, %40 yoğunluklu (Erdős-Rényi) gerçekçi bir ağ topolojisi oluşturmak |
| 2 | **Algoritma Çeşitliliği** | GA, ACO, PSO, SA ve Q-Learning algoritmalarını entegre etmek |
| 3 | **Çok Amaçlı Optimizasyon** | Gecikme, Güvenilirlik ve Kaynak metriklerini aynı anda optimize etmek |
| 4 | **Performans** | Algoritmaların makul sürede sonuç vermesi |

### Başarı Kriterleri

| KPI | Kriter |
|-----|--------|
| **KPI 1** | 250 düğümlü grafiği görselleştirebilme (2D/3D) |
| **KPI 2** | En az 5 farklı algoritmanın çalışması |
| **KPI 3** | Dinamik ağırlık ayarlama (Wd, Wr, Wc) |
| **KPI 4** | Toplu deney ve karşılaştırma raporu oluşturabilme |

---

## 2. Kapsam

| Tür | Açıklama |
|-----|----------|
| ✅ **Dahil** | Python, PyQt5, NetworkX, Matplotlib, PDF/CSV export |
| ❌ **Hariç** | Gerçek donanım entegrasyonu, Web/Mobil uygulama |

---

## 3. Tamamlanan Özellikler

### Algoritmalar
- [x] Genetik Algoritma (GA) - Paralel işleme destekli
- [x] Karınca Kolonisi (ACO) - Feromon takibi
- [x] Parçacık Sürüsü (PSO)
- [x] Benzetilmiş Tavlama (SA)
- [x] Q-Learning (RL)
- [x] SARSA (RL)

### Arayüz
- [x] Graf görselleştirme (2D/3D geçişli)
- [x] Optimizasyon kontrol paneli
- [x] Sonuç paneli (metrikler, yol detayı)
- [x] Deney düzeneği paneli
- [x] PDF/CSV/JSON export

### Deney Özellikleri
- [x] 25 farklı test senaryosu (4 ağırlık profili)
- [x] Senaryo bazlı algoritma karşılaştırması
- [x] Algoritma ranking tablosu
- [x] Karşılaştırma grafikleri (bar chart)
- [x] Ölçeklenebilirlik analizi
- [x] Başarısızlık raporlama

### Teknik
- [x] Multi-start optimizasyon
- [x] Seed ile tekrarlanabilirlik
- [x] Bant genişliği kısıt kontrolü
- [x] Edge break (Chaos Monkey) özelliği

---

## 4. Proje Yapısı

```
📁 QoS-Multi-Objective-Routing/
├── 📁 app/
│   ├── main.py
│   └── 📁 src/
│       ├── 📁 algorithms/      # GA, ACO, PSO, SA, QL, SARSA
│       ├── 📁 services/        # graph, metrics, report
│       ├── 📁 experiments/     # test_cases, experiment_runner
│       ├── 📁 workers/         # optimization_worker
│       └── 📁 ui/              # main_window, components
├── 📁 graph_data/              # CSV veri dosyaları
└── 📁 Documents/               # Dokümantasyon
```

---

## 5. Çalıştırma

```bash
cd app
pip install -r requirements.txt
python main.py
```

---

> Son güncelleme: 2025-12-31