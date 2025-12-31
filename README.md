# QoS Multi-Objective Routing Optimizer

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?logo=qt&logoColor=white)
![NetworkX](https://img.shields.io/badge/NetworkX-3.1+-orange)
![License](https://img.shields.io/badge/License-Educational-blue)

**Çok Amaçlı QoS Rotalama Optimizasyonu** — NP-Hard Multi-Constraint QoS Routing problemini **6 farklı algoritma** ile çözen, gerçek zamanlı görselleştirme ve karşılaştırmalı deney yapabilme özelliklerine sahip masaüstü uygulaması.

> Üç çelişen metriği (Gecikme, Güvenilirlik, Kaynak Kullanımı) aynı anda optimize eder.

---

## 📋 İçindekiler

- [Temel Özellikler](#-temel-özellikler)
- [Desteklenen Algoritmalar](#-desteklenen-algoritmalar)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Proje Yapısı](#-proje-yapısı)
- [Dokümantasyon](#-dokümantasyon)
- [QoS Metrikleri](#-qos-metrikleri)
- [Konfigürasyon](#-konfigürasyon)

---

## 🎯 Temel Özellikler

### Multi-Start Optimization
Stokastik algoritmalar farklı seed'lerle N kez çalıştırılıp en iyi sonuç seçilir.

### Real-Time Visualization
| Özellik | Açıklama |
|---------|----------|
| **2D/3D Toggle** | OpenGL destekli 3D görünüm |
| **Packet Animation** | Yol üzerinde animasyon |
| **Interactive Graph** | Hover ile detay görüntüleme |

### Chaos Monkey (Self-Healing)
Orta tık ile kenar kırma, otomatik rota yeniden hesaplama.

### Export & Reporting
- PDF rapor export
- PNG graf görüntüsü
- JSON/CSV deney sonuçları

---

## 🧬 Desteklenen Algoritmalar

### Meta-Sezgisel

| Algoritma | Dosya | Açıklama |
|-----------|-------|----------|
| **Genetic Algorithm (GA)** | `genetic_algorithm.py` | Evrimsel seçilim, crossover, mutasyon |
| **Ant Colony (ACO)** | `aco.py` | Karınca feromon takibi |
| **Particle Swarm (PSO)** | `pso.py` | Sürü zekası |
| **Simulated Annealing (SA)** | `simulated_annealing.py` | Tavlama benzetimi |

### Pekiştirmeli Öğrenme

| Algoritma | Dosya | Açıklama |
|-----------|-------|----------|
| **Q-Learning** | `q_learning.py` | Off-policy değer öğrenme |
| **SARSA** | `sarsa.py` | On-policy TD learning |

> 📖 **Detaylı açıklama:** [GA Akış Şeması](./Documents/GA_akis_semasi.md) | [ACO Akış Şeması](./Documents/Aco_akis_semasi.md)

---

## 🔧 Kurulum

### Gereksinimler
- Python 3.9+
- Windows / Linux / macOS

### Adımlar

```bash
# 1. Repoyu klonlayın
git clone https://github.com/Erkan3034/QoS-Multi-Objective-Routing.git
cd QoS-Multi-Objective-Routing

# 2. Sanal ortam oluşturun
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 3. Bağımlılıkları yükleyin
cd app
pip install -r requirements.txt
```

### Bağımlılıklar

```txt
PyQt5>=5.15
PyQtGraph>=0.12
networkx>=3.1
numpy>=1.24
matplotlib>=3.7
reportlab>=4.0
Pillow>=10.0
```

---

## 🚀 Kullanım

### Uygulamayı Başlatma

```bash
cd app
python main.py
```

### Temel İş Akışı

1. **Graf Yükleme**
   - "Proje Verisini Yükle" → CSV dosyasından
   - "Graf Oluştur" → Rastgele Erdős–Rényi topolojisi

2. **Kaynak/Hedef Seçimi**
   - Sol tık = Kaynak (S) - Yeşil
   - Sağ tık = Hedef (D) - Kırmızı

3. **Ağırlık Ayarları**
   - Gecikme / Güvenilirlik / Kaynak slider'ları
   - Toplam otomatik 100%'e normalize edilir

4. **Optimizasyon**
   - Algoritma seç → "Optimize Et"
   

5. **Sonuç**
   - Bulunan yol sarı renkte
   - Metrikler sağ panelde

---

## 📁 Proje Yapısı

```
QoS-Multi-Objective-Routing/
├── app/
│   ├── main.py                    # Giriş noktası
│   ├── requirements.txt
│   └── src/
│       ├── algorithms/            # 5 optimizasyon algoritması
│       │   ├── genetic_algorithm.py
│       │   ├── aco.py
│       │   ├── pso.py
│       │   ├── simulated_annealing.py
│       │   ├── q_learning.py
│       │   
│       │
│       ├── core/
│       │   └── config.py          # Konfigürasyon
│       │
│       ├── services/
│       │   ├── graph_service.py   # Graf oluşturma
│       │   ├── metrics_service.py # QoS metrik hesaplama
│       │   └── report_service.py  # PDF/PNG export
│       │
│       ├── experiments/
│       │   └── experiment_runner.py
│       │
│       └── ui/
│           ├── main_window.py
│           ├── components/
│           │   ├── graph_widget.py
│           │   ├── control_panel.py
│           │   └── results_panel.py
│           └── dialogs/
│               └── experiment_dialog.py
│
├── graph_data/                    # CSV veri dosyaları
│   ├── *_NodeData.csv
│   ├── *_EdgeData.csv
│   └── *_DemandData.csv
│
├── Documents/                     # 📖 Dokümantasyon
│
└── README.md
```

---

## � Dokümantasyon

| Dosya | İçerik |
|-------|--------|
| [Geliştirici Rehberi](./Documents/Gelistirici_Rehberi.md) | Kurulum, proje yapısı, kodlama standartları |
| [GA Akış Şeması](./Documents/GA_akis_semasi.md) | Genetik Algoritma görsel açıklaması |
| [ACO Akış Şeması](./Documents/Aco_akis_semasi.md) | Karınca Kolonisi görsel açıklaması |
| [Teknik Gereksinimler](./Documents/Teknik_Gereksinimler.md) | Proje gereksinimleri ve QoS tanımları |
| [Test Senaryoları](./Documents/Test_Senaryoları_Deney_Duzenegi.md) | Deney düzeneği ve test planları |
| [Ölçeklenebilirlik](./Documents/Olceklenebilirlik_Analizi.md) | Büyük graf performans analizi |
| [Proje Yönetimi](./Documents/Proje_Yönetimi.md) | Görev dağılımı ve timeline |

---

## 📊 QoS Metrikleri

### Formüller (Proje Yönergesi)

| Metrik | Formül |
|--------|--------|
| **TotalDelay** | `Σ(LinkDelay) + Σ(ProcessingDelay)` (k ≠ S,D) |
| **ReliabilityCost** | `Σ[-log(LinkReliability)] + Σ[-log(NodeReliability)]` |
| **ResourceCost** | `Σ(1Gbps / Bandwidth)` |
| **TotalCost** | `w₁×Delay + w₂×Reliability + w₃×Resource` |

### Normalizasyon

```
delay_norm = min(total_delay / 200ms, 1.0)
reliability_norm = min(-log(reliability) / 10.0, 1.0)
resource_norm = min(resource_cost / 200.0, 1.0)
```

---

## ⚙️ Konfigürasyon

Parametreler `app/src/core/config.py` dosyasında:

```python
# Genetic Algorithm
GA_POPULATION_SIZE = 200
GA_GENERATIONS = 100
GA_MUTATION_RATE = 0.05
GA_CROSSOVER_RATE = 0.8
GA_ELITISM = 0.1

# Ant Colony Optimization
ACO_N_ANTS = 50
ACO_N_ITERATIONS = 100

# Q-Learning / SARSA
QL_EPISODES = 5000
QL_LEARNING_RATE = 0.1
QL_DISCOUNT_FACTOR = 0.95
```

---

## � Reproducibility (Tekrarlanabilirlik)

Tüm algoritmalar kullanılan seed değerini döndürür:

```python
result = ga.optimize(source=1, destination=20, weights=weights)
print(f"Seed: {result.seed_used}")

# Aynı sonucu tekrar almak için:
ga = GeneticAlgorithm(graph, seed=result.seed_used)
```

---  

<br>



>**BSM307 - Bilgisayar Ağları Dersi | Güz 2025**

>Danışman: Doç. Dr. Evrim GÜLER

---

## 👥 Ekip

| İsim | Görev |
|------|-------|
| Erkan Turgut | Backend & Genetic & ACO algoritmaları. |
| Bilal Alfa Guldi | PSO & SA algoritmaları. |
| Diğer Ekip Üyeleri | UI & Test |
