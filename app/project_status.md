# 📊 Proje Durum Raporu

> BSM307/317 QoS Multi-Objective Routing Project
> Son Güncelleme: 2025-12-07

---

## 🎯 Proje Özeti

**Amaç:** Çok amaçlı rotalama problemi için 6 farklı optimizasyon algoritması geliştirmek ve karşılaştırmak.

**Amaç Fonksiyonu:**
```
minimize F(P) = W_delay × Delay(P) + W_reliability × ReliabilityCost(P) + W_resource × ResourceCost(P)
```

---

## ✅ TAMAMLANAN BÖLÜMLER

### 1. Graf Altyapısı (100%)

| Özellik | Durum | Dosya |
|---------|-------|-------|
| CSV'den graf yükleme | ✅ | `graph_service.py` |
| NodeData parsing | ✅ | 250 düğüm, processing_delay, reliability |
| EdgeData parsing | ✅ | 12,452 kenar, bandwidth, delay, reliability |
| DemandData parsing | ✅ | 30 talep çifti (source, dest, demand_mbps) |
| Rastgele graf oluşturma | ✅ | Erdős–Rényi G(n,p) modeli |
| Graf bağlantılılık kontrolü | ✅ | `nx.is_connected()` |

### 2. Metrik Hesaplama (100%)

| Metrik | Formül | Durum |
|--------|--------|-------|
| Total Delay | Σ LinkDelay + Σ ProcessingDelay | ✅ |
| Total Reliability | Π LinkReliability × Π NodeReliability | ✅ |
| Reliability Cost | -Σ log(reliability) | ✅ |
| Resource Cost | Σ (1Gbps / bandwidth) | ✅ |
| Weighted Cost | W₁×Delay + W₂×RelCost + W₃×ResCost | ✅ |

### 3. Optimizasyon Algoritmaları (100%)

| Algoritma | Dosya | Özellikler |
|-----------|-------|------------|
| **Genetic Algorithm** | `genetic_algorithm.py` | Path encoding, tournament selection, single-point crossover, random mutation, elitism |
| **Ant Colony (ACO)** | `aco.py` | Feromon tabanlı seçim, visibility heuristic, evaporation, elitist ant |
| **Particle Swarm (PSO)** | `pso.py` | Particle representation, velocity update, global/local best |
| **Simulated Annealing** | `simulated_annealing.py` | Temperature cooling, neighbor solution, Metropolis criterion |
| **Q-Learning** | `q_learning.py` | ε-greedy exploration, Q-table update, off-policy TD |
| **SARSA** | `sarsa.py` | On-policy TD, ε-greedy, action-value update |

### 4. Deney Altyapısı (100%)

| Özellik | Durum | Açıklama |
|---------|-------|----------|
| TestCase yapısı | ✅ | source, destination, bandwidth_requirement, weights |
| RepeatResult | ✅ | Tekrarlı deney sonuçları, istatistikler |
| FailureReport | ✅ | Başarısız testlerin gerekçeli raporu |
| ExperimentRunner | ✅ | Tüm deneyleri çalıştıran ana sınıf |
| Ölçeklenebilirlik Analizi | ✅ | Farklı düğüm sayılarıyla test |
| Bandwidth Kontrolü (post) | ✅ | Yol bulunduktan sonra B kontrolü |

### 5. UI Bileşenleri (90%)

| Bileşen | Durum | Açıklama |
|---------|-------|----------|
| Ana pencere | ✅ | Dark theme, 3 panel layout |
| Graf görselleştirme | ✅ | PyQtGraph, 250+ düğüm render |
| Kontrol paneli | ✅ | Parametre ayarları, algoritma seçimi |
| CSV yükleme butonu | ✅ | Hocanın verisini yükle |
| Demand seçici | ✅ | 30 talep çiftinden seçim |
| Sonuç paneli | ✅ | Tek sonuç ve karşılaştırma tablosu |
| Deney çalıştırma | ⏳ | UI'dan tam deney henüz yok |

---

## ⚠️ EKSİK BÖLÜMLER

### 1. Bandwidth Kısıtı - Algoritma İçi (0%)

**Mevcut Durum:**
- Algoritmalar bandwidth'i göz ardı ederek yol buluyor
- Yol bulunduktan SONRA bandwidth kontrolü yapılıyor
- Yetersizse "FAILED" olarak işaretleniyor

**Olması Gereken:**
- Algoritmalar yol ararken bandwidth kontrolü yapmalı
- `min(path_bandwidth) >= demand_mbps` sağlanmalı

### 2. Sonuç Export (0%)

**Eksik:**
- JSON/CSV dosyasına kaydetme
- Rapor oluşturma

---

## 📁 Dosya Yapısı

```
pyqt5-desktop/
├── main.py                 # Ana giriş noktası
├── requirements.txt        # Bağımlılıklar
├── src/
│   ├── core/
│   │   └── config.py       # Konfigürasyon
│   ├── services/
│   │   ├── graph_service.py    # Graf yükleme/oluşturma
│   │   └── metrics_service.py  # Metrik hesaplama
│   ├── algorithms/
│   │   ├── __init__.py
│   │   ├── genetic_algorithm.py
│   │   ├── aco.py
│   │   ├── pso.py
│   │   ├── simulated_annealing.py
│   │   ├── q_learning.py
│   │   └── sarsa.py
│   ├── experiments/
│   │   ├── experiment_runner.py  # Deney çalıştırıcı
│   │   └── test_cases.py         # Test case tanımları
│   └── ui/
│       ├── main_window.py
│       └── components/
│           ├── control_panel.py
│           ├── graph_widget.py
│           └── results_panel.py
└── graph_data/             # Hocanın verileri
    ├── BSM307_317_Guz2025_TermProject_NodeData.csv
    ├── BSM307_317_Guz2025_TermProject_EdgeData.csv
    └── BSM307_317_Guz2025_TermProject_DemandData.csv
```

---

## 📈 Veri İstatistikleri

| Veri | Değer |
|------|-------|
| Düğüm Sayısı | 250 |
| Kenar Sayısı | 12,452 |
| Talep Çifti Sayısı | 30 |
| Ortalama Derece | 99.62 |
| Graf Bağlantılı mı? | ✅ Evet |
| Processing Delay Aralığı | 0.51 - 1.99 ms |
| Node Reliability Aralığı | 0.950 - 0.999 |
| Link Bandwidth Aralığı | 100 - 1000 Mbps |
| Link Delay Aralığı | 3 - 15 ms |
| Link Reliability Aralığı | 0.950 - 0.999 |
| Demand Aralığı | 18 - 200 Mbps |

---

## 🏁 Sonraki Adımlar

1. **[KRİTİK]** Bandwidth kısıtını algoritmalara entegre et
2. **[ORTA]** Sonuç export fonksiyonları ekle
3. **[DÜŞÜK]** UI'dan tam deney çalıştırma

---

## 📊 Tamamlanma Durumu

```
Graf Altyapısı:        ████████████████████ 100%
Metrik Hesaplama:      ████████████████████ 100%
Algoritmalar:          ████████████████████ 100%
Deney Altyapısı:       ████████████████████ 100%
B Kısıtı (post):       ████████████████████ 100%
B Kısıtı (algoritma):  ░░░░░░░░░░░░░░░░░░░░   0%
UI:                    ██████████████████░░  90%
Export:                ░░░░░░░░░░░░░░░░░░░░   0%

GENEL:                 ████████████████░░░░  85%
```

