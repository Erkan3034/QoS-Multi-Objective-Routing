# QoS Routing Optimizer v2.4

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-41CD52?logo=qt&logoColor=white)
![NetworkX](https://img.shields.io/badge/NetworkX-2.6+-orange)
![License](https://img.shields.io/badge/License-Educational-blue)
![Status](https://img.shields.io/badge/Status-Production--Ready-brightgreen)

**Çok Amaçlı QoS Rotalama Optimizasyonu** — NP-Hard sınıfında yer alan Multi-Constraint QoS Routing problemini 6 farklı meta-sezgisel ve pekiştirmeli öğrenme algoritması ile çözen, gerçek zamanlı görselleştirme ve self-healing yeteneklerine sahip masaüstü uygulaması.

> Üç çelişen metriği (Gecikme, Güvenilirlik, Kaynak Kullanımı) aynı anda optimize ederek, ağ mühendislerine **enterprise-grade** rota planlama aracı sunar.

![Screenshot](./Documents/screenshot.png)

---

## 📋 İçindekiler

- [Temel Özellikler](#-temel-özellikler)
- [Teknik Mimari](#-teknik-mimari)
- [Desteklenen Algoritmalar](#-desteklenen-algoritmalar)
- [Kurulum](#-kurulum)
- [Kullanım](#-kullanım)
- [Proje Yapısı](#-proje-yapısı)
- [Gelişmiş Özellikler](#-gelişmiş-özellikler)
- [Konfigürasyon](#-konfigürasyon)

---

## 🎯 Temel Özellikler

### Normalization Engine (Dominant Metric Çözümü)

Farklı birimlerdeki metrikleri (ms, %, hop) aynı denklemde toplayabilmek için **v2.4 Normalization** motoru geliştirilmiştir. Bu sayede kullanıcı ağırlıkları gerçekten etkili olur.

```
Problem: 50ms + 0.01 + 5 hop = Delay her zaman kazanır
Çözüm:   0.25 + 0.10 + 0.25 = Dengeli katkı
```

**Referans Sabitleri:**
| Metrik | Referans Maksimum | Gerçek Dünya Eşdeğeri |
|--------|-------------------|------------------------|
| Delay | 200 ms | Satellite/3G sınırı |
| Hop Count | 20 hop | Pratik maksimum |
| Reliability Penalty | 10x | Güvenilirlik hassasiyeti |

---

### Chaos Monkey (Self-Healing Test)

Graf üzerinde herhangi bir kenarı **orta tık** ile kırarak link arızası simülasyonu yapabilirsiniz. Sistem otomatik olarak:

1. Kenarı graftan kaldırır
2. Görsel güncelleme yapar (kırmızı kesikli çizgi)
3. `edge_broken` sinyali emit eder
4. Yeni rota hesaplar ve görselleştirir

```python
# Event-driven architecture
self.graph_widget.edge_broken.connect(self._on_edge_broken)
```

Bu özellik, **MTTR (Mean Time To Recovery)** testleri için idealdir.

---

### Real-Time Visualization

| Bileşen | Açıklama |
|---------|----------|
| **Live Convergence Plot** | Nesil vs. Fitness grafiği, gerçek zamanlı güncellenir |
| **Packet Animation** | Bulunan yol üzerinde hareket eden parçacıklar |
| **2D/3D Toggle** | OpenGL destekli 3D görünüm |
| **Interactive Tooltips** | Kenar/düğüm üzerinde hover ile detay görüntüleme |

---

### ILP Benchmark

- **ILP Solver:** PuLP kutuphanesi ile optimal cozum hesaplama
- **Optimality Gap:** Meta-sezgisel sonuclari optimal cozumle karsilastirma

---

## 🏗️ Teknik Mimari

### Teknoloji Stack

| Katman | Teknoloji | Amaç |
|--------|-----------|------|
| **Core** | Python 3.8+ | Ana programlama dili |
| **Graph Engine** | NetworkX | Graf veri yapısı ve algoritmalar |
| **UI Framework** | PyQt5 | Masaüstü arayüz |
| **Visualization** | PyQtGraph + OpenGL | Performanslı 2D/3D render |
| **Optimization** | PuLP | ILP çözücü (opsiyonel) |

### Mimari Desenler

- **Event-Driven (Signals/Slots):** PyQt sinyalleri ile loose coupling
- **Worker Threads:** UI donmasını önlemek için QThread kullanımı
- **Multiprocessing:** 500+ düğümlü ağlarda paralel fitness hesaplama
- **Singleton Pool Pattern:** Process pool için bellek optimizasyonu
- **LRU Cache:** Tekrarlanan shortest path hesaplamalarını önbelleğe alma

```
┌─────────────────────────────────────────────────────────────┐
│                      MainWindow                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ControlPanel │  │ GraphWidget │  │ ResultsPanel        │  │
│  │             │  │  (2D/3D)    │  │ ConvergenceWidget   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                    │             │
│         └────────────────┼────────────────────┘             │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │  OptimizationWorker   │  ← QThread           │
│              │  (Background Thread)  │                      │
│              └───────────┬───────────┘                      │
│                          ▼                                  │
│              ┌───────────────────────┐                      │
│              │  Algorithm Engine     │                      │
│              │  (GA/ACO/PSO/SA/RL)   │                      │
│              └───────────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧬 Desteklenen Algoritmalar

### Meta-Sezgisel Algoritmalar

| Algoritma | Kısaltma | Açıklama | Öne Çıkan Özellik |
|-----------|----------|----------|-------------------|
| **Genetic Algorithm** | GA | Evrimsel seçilim, çaprazlama ve mutasyon | Adaptive mutation rate |
| **Ant Colony Optimization** | ACO | Karınca feromon izleme davranışı | Pheromone persistence |
| **Particle Swarm Optimization** | PSO | Sürü zekası ile parçacık hareketi | Global/Local best tracking |
| **Simulated Annealing** | SA | Metalurji tavlama simülasyonu | Temperature scheduling |

### Pekiştirmeli Öğrenme Algoritmaları

| Algoritma | Kısaltma | Açıklama | Öne Çıkan Özellik |
|-----------|----------|----------|-------------------|
| **Q-Learning** | QL | Off-policy değer fonksiyonu öğrenme | Epsilon-greedy exploration |
| **SARSA** | SARSA | On-policy temporal difference | State-Action-Reward learning |

---

## 🔧 Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- Windows / Linux / macOS

### Adımlar

```bash
# 1. Repoyu klonlayın
git clone https://github.com/your-username/QoS-Multi-Objective-Routing.git
cd QoS-Multi-Objective-Routing

# 2. Sanal ortam oluşturun (önerilen)
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 3. Bağımlılıkları yükleyin
cd app
pip install -r requirements.txt
```

### Bağımlılıklar

```
PyQt5>=5.15.0
PyQtGraph>=0.12.0
networkx>=2.6.0
numpy>=1.20.0
pyopengl>=3.1.0
pydantic-settings>=2.0.0
pulp>=2.7.0          # ILP solver (opsiyonel)
matplotlib>=3.5.0    # Convergence plot
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
   - "Proje Verisini Yükle (CSV)" ile hazır veri seti
   - Veya "Graf Oluştur" ile rastgele Erdős–Rényi topolojisi

2. **Kaynak/Hedef Seçimi**
   - Sol tık = Kaynak (S) - Yeşil
   - Sağ tık = Hedef (D) - Kırmızı
   - Veya kontrol panelinden spin box ile

3. **Ağırlık Ayarları**
   - Gecikme / Güvenilirlik / Kaynak slider'ları
   - Otomatik normalizasyon (toplam = 100%)

4. **Optimizasyon**
   - Algoritma seçimi (GA, ACO, PSO, SA, Q-Learning, SARSA)
   - "Optimize Et" butonu
   - Canlı yakınsama grafiğini izleyin

5. **Sonuç İnceleme**
   - Bulunan yol sarı renkte görselleştirilir
   - Metrikler sağ panelde gösterilir

---

## 📁 Proje Yapısı

```
QoS-Multi-Objective-Routing/
├── app/
│   ├── main.py                      # Giriş noktası
│   ├── requirements.txt             # Python bağımlılıkları
│   └── src/
│       ├── algorithms/              # 6 optimizasyon algoritması
│       │   ├── genetic_algorithm.py # GA v2.4 (Normalized)
│       │   ├── aco.py               # Ant Colony Optimization
│       │   ├── pso.py               # Particle Swarm Optimization
│       │   ├── simulated_annealing.py
│       │   ├── q_learning.py        # Reinforcement Learning
│       │   └── sarsa.py
│       │
│       ├── core/                    # Konfigürasyon
│       │   └── config.py            # Tüm parametreler
│       │
│       ├── experiments/             # Deney framework'u
│       │   ├── experiment_runner.py # Toplu deney calistirici
│       │   ├── ilp_solver.py        # ILP optimal cozum
│       │   └── scalability_analyzer.py
│       │
│       ├── services/                # İş mantığı
│       │   ├── graph_service.py     # Graf oluşturma/yükleme
│       │   └── metrics_service.py   # Normalize edilmiş metrik hesaplama
│       │
│       ├── workers/                 # Arka plan thread'leri
│       │   └── optimization_worker.py
│       │
│       └── ui/                      # PyQt5 arayüz
│           ├── main_window.py       # Ana pencere
│           └── components/
│               ├── graph_widget.py  # 2D/3D görselleştirme + Chaos Monkey
│               ├── convergence_widget.py  # Canlı yakınsama grafiği
│               ├── control_panel.py
│               ├── results_panel.py
│               └── ...
│
├── graph_data/                      # CSV veri dosyaları
│   ├── *_NodeData.csv
│   ├── *_EdgeData.csv
│   └── *_DemandData.csv
│
├── Documents/                       # Dokümantasyon
│   └── Technical_Defense_Report.md
│
└── README.md
```

---

## 🔬 Gelişmiş Özellikler

### Multi-Start Optimization

Stokastik algoritmaların güvenilirliğini artırmak için N farklı seed ile N kez çalıştırma:

```
Çoklu Çalıştırma: [1] [5] [10] [30]
```

En iyi sonuç otomatik seçilir, istatistiksel analiz sağlanır.

### ILP Benchmark

Meta-sezgisel sonuclari matematiksel optimal cozumle karsilastirma:
- Optimality Gap (%) hesaplama
- Solver: PuLP (CBC backend)

### Reproducibility (Tekrarlanabilirlik)

Tüm algoritmalar çalışma sırasında kullanılan seed değerini sonuç objesinde döndürür:

```python
result = ga.optimize(source=0, destination=249, weights=weights)
print(f"Kullanılan seed: {result.seed_used}")

# Aynı sonucu tekrar almak için:
ga = GeneticAlgorithm(graph, seed=result.seed_used)
result2 = ga.optimize(source=0, destination=249, weights=weights)
# result.path == result2.path  # ✓ Aynı sonuç
```

**Desteklenen algoritmalar:**
- `GAResult.seed_used` - Genetic Algorithm
- `ACOResult.seed_used` - Ant Colony Optimization
- `PSOResult.seed_used` - Particle Swarm Optimization
- `SAResult.seed_used` - Simulated Annealing

### Ölçeklenebilirlik Analizi

Farklı graf boyutlarında (50-500+ düğüm) algoritma performansını test etme.

---

## ⚙️ Konfigürasyon

Tüm parametreler `app/src/core/config.py` dosyasında tanımlıdır:

```python
# Genetic Algorithm
GA_POPULATION_SIZE = 150
GA_GENERATIONS = 500
GA_MUTATION_RATE = 0.12
GA_CROSSOVER_RATE = 0.8
GA_ELITISM = 0.08

# Ant Colony Optimization
ACO_N_ANTS = 50
ACO_N_ITERATIONS = 100

# Simulated Annealing
SA_INITIAL_TEMPERATURE = 1000.0
SA_COOLING_RATE = 0.995

# Q-Learning / SARSA
QL_EPISODES = 5000
QL_LEARNING_RATE = 0.1
QL_DISCOUNT_FACTOR = 0.95
```

---

## 📊 Örnek Sonuçlar

```
250 düğüm, p=0.40, S=0 → D=200

Algoritma     | Gecikme  | Güvenilirlik | Maliyet | Süre
--------------|----------|--------------|---------|------
Genetic Alg.  | 45.2 ms  | 92.3%        | 0.234   | 150ms
ACO           | 48.1 ms  | 94.1%        | 0.251   | 280ms
PSO           | 46.8 ms  | 93.5%        | 0.245   | 120ms
SA            | 47.5 ms  | 93.8%        | 0.248   | 85ms
Q-Learning    | 52.3 ms  | 91.2%        | 0.289   | 450ms
SARSA         | 51.8 ms  | 91.5%        | 0.285   | 420ms
```

---

## 📝 Lisans

Bu proje eğitim amaçlı geliştirilmiştir.

**BSM307 - Bilgisayar Ağları Dersi | Güz 2025**

---


Doç. Dr. Evrim GÜLER (Danışman)
