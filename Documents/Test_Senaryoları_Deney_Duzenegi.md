# Test Senaryoları ve Deney Çalıştırma Sistemi

## 📋 İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Sistem Mimarisi](#sistem-mimarisi)
3. [Dosya Yapısı](#dosya-yapısı)
4. [Test Senaryoları Sistemi](#test-senaryoları-sistemi)
5. [Deney Çalıştırma Sistemi](#deney-çalıştırma-sistemi)
6. [Çalışma Akışı](#çalışma-akışı)
7. [Kullanım Adımları](#kullanım-adımları)

---

## 🎯 Genel Bakış

QoS Multi-Objective Routing projesinde, algoritmaların performansını test etmek için iki ana sistem bulunmaktadır:

1. **Test Senaryoları Sistemi**: Önceden tanımlanmış test senaryolarını görüntüleme
2. **Deney Çalıştırma Sistemi**: Test senaryolarını gerçekten çalıştırıp algoritmaları karşılaştırma

---

## 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer (PyQt5)                         │
├─────────────────────────────────────────────────────────────┤
│  ExperimentsPanel                                           │
│  ├─ "Test Senaryolarını Yükle" Butonu                       │
│  └─ "Deneyleri Çalıştır" Butonu                             │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Worker Layer (QThread)                         │
├─────────────────────────────────────────────────────────────┤
│  ExperimentsWorker (Background Thread)                      │
│  └─ Progress Signals → UI Updates                           │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│            Business Logic Layer                             │
├─────────────────────────────────────────────────────────────┤
│  TestCaseGenerator                                          │
│  └─ get_predefined_test_cases() → 25 Senaryo                │
│                                                             │
│  ExperimentRunner                                           │
│  ├─ run_experiments()                                       │
│  └─ _execute_single_run() → GA, ACO, PSO                    │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│            Algorithm Layer                                  │
├─────────────────────────────────────────────────────────────┤
│  GeneticAlgorithm, ACO, PSO                                 │
│  └─ optimize() → Path Finding                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Dosya Yapısı

### Ana Dosyalar

#### 1. Test Senaryoları Üretimi
```
app/src/experiments/test_cases.py
├─ TestCase (dataclass)
│   ├─ id: int
│   ├─ source: int
│   ├─ destination: int
│   ├─ bandwidth_requirement: float
│   ├─ weights: Dict[str, float]
│   └─ description: str
│
├─ TestCaseGenerator
│   ├─ __init__(graph, seed=42)
│   ├─ get_predefined_test_cases() → 25 senaryo
│   └─ generate_test_cases(n_cases) → rastgele senaryo
│
└─ BandwidthConstraintChecker
    ├─ check_constraint(path, requirement) → (bool, float, str)
    └─ get_path_min_bandwidth(path) → float
```

#### 2. Deney Çalıştırıcı
```
app/src/experiments/experiment_runner.py
└─ ExperimentRunner
    ├─ __init__(graph, n_repeats=5, iterations=100)
    ├─ run_experiments(test_cases) → Dict[str, Any]
    │   ├─ Her algoritma için (GA, ACO, PSO)
    │   ├─ Her test case için
    │   ├─ n_repeats tekrar
    │   └─ İstatistik toplama
    │
    └─ _execute_single_run(alg_name, case) → Dict
        ├─ Algoritma seçimi (GA/ACO/PSO)
        ├─ optimize() çağrısı
        ├─ Bant genişliği kontrolü
        └─ Maliyet hesaplama
```

#### 3. UI Bileşenleri
```
app/src/ui/components/
├─ experiments_panel.py
│   ├─ ExperimentsPanel
│   ├─ TestScenariosCard → "Test Senaryolarını Yükle"
│   └─ PresetExperimentsCard → "Deneyleri Çalıştır"
│
├─ scenarios_dialog.py
│   └─ ScenariosDialog → Senaryo listesi gösterimi
│
└─ test_results_dialog.py
    └─ TestResultsDialog → Deney sonuçları gösterimi
```

#### 4. Ana Pencere ve Worker
```
app/src/ui/main_window.py
├─ MainWindow
│   ├─ _on_load_test_scenarios() → Senaryo listesi
│   ├─ _on_run_experiments() → Deney başlatma
│   ├─ _on_experiment_progress() → İlerleme güncelleme
│   └─ _on_experiments_finished() → Sonuç gösterimi
│
└─ ExperimentsWorker (QThread)
    ├─ run() → Background execution
    ├─ progress → Signal (current, total, message)
    ├─ finished → Signal (result_dict)
    └─ error → Signal (error_message)
```

---

## 🔍 Test Senaryoları Sistemi

### Amaç
Önceden tanımlanmış test senaryolarını görselleştirmek ve listelemek.

### Çalışma Mantığı

1. **Senaryo Üretimi**
   ```python
   # app/src/experiments/test_cases.py
   generator = TestCaseGenerator(graph, seed=42)
   scenarios = generator.get_predefined_test_cases()  # 25 senaryo
   ```

2. **Senaryo İçeriği**
   - **25 önceden tanımlanmış senaryo**
   - Her senaryo: (Source, Destination, Bandwidth)
   - Bant genişliği seviyeleri: [100, 200, 300, ..., 1000] Mbps
   - Ağırlıklar: `{"delay": 0.33, "reliability": 0.33, "resource": 0.34}`

3. **UI Gösterimi**
   ```python
   # app/src/ui/main_window.py
   def _on_load_test_scenarios(self):
       generator = TestCaseGenerator(self.graph_service.graph)
       scenarios = generator.get_predefined_test_cases()
       dialog = ScenariosDialog(scenarios, self)
       dialog.exec_()  # Modal dialog açılır
   ```

### Özellikler
- ✅ 25 senaryo listesi
- ✅ Filtreleme (ID, Source, Destination, Bandwidth)
- ✅ İstatistik kartları (Toplam, Farklı Kaynak, Farklı Hedef)
- ✅ Tam ekran modu
- ✅ Profesyonel tablo tasarımı

---

## 🚀 Deney Çalıştırma Sistemi

### Amaç
Test senaryolarını gerçekten çalıştırarak algoritmaları (GA, ACO, PSO) karşılaştırmak.

### Çalışma Mantığı

#### 1. Deney Başlatma
```python
# app/src/ui/main_window.py
def _on_run_experiments(self, n_tests, n_repeats):
    self.current_worker = ExperimentsWorker(
        self.graph_service.graph, 
        n_tests,      # 25 (önceden tanımlı) veya rastgele
        n_repeats     # 5 (varsayılan)
    )
    self.current_worker.start()  # QThread başlatılır
```

#### 2. Worker İşlemi
```python
# app/src/ui/main_window.py → ExperimentsWorker.run()
def run(self):
    # 1. Test case'leri üret
    generator = TestCaseGenerator(self.graph)
    if self.n_tests == 25:
        test_cases = generator.get_predefined_test_cases()
    else:
        test_cases = generator.generate_test_cases(n_cases=self.n_tests)
    
    # 2. ExperimentRunner oluştur
    runner = ExperimentRunner(
        graph=self.graph,
        n_repeats=self.n_repeats,  # 5 tekrar
        progress_callback=progress_callback
    )
    
    # 3. Deneyleri çalıştır
    result = runner.run_experiments(test_cases)
    
    # 4. Sonucu emit et
    self.finished.emit(result)
```

#### 3. Deney Çalıştırma Detayları
```python
# app/src/experiments/experiment_runner.py
def run_experiments(self, test_cases):
    algorithms = ["GA", "ACO", "PSO"]
    
    for alg_name in algorithms:
        for case in test_cases:
            for repeat in range(n_repeats):  # 5 tekrar
                result = self._execute_single_run(alg_name, case)
                # İstatistik toplama
```

#### 4. Tek Bir Çalıştırma
```python
# app/src/experiments/experiment_runner.py
def _execute_single_run(self, alg_name, case):
    # 1. Algoritma seçimi ve optimize çağrısı
    if alg_name == "GA":
        alg = GeneticAlgorithm(self.graph)
        result = alg.optimize(
            source=case.source,
            destination=case.destination,
            weights=case.weights,
            bandwidth_demand=case.bandwidth_requirement
        )
    elif alg_name == "ACO":
        alg = AntColonyOptimization(self.graph)
        result = alg.optimize(...)
    else:  # PSO
        alg = ParticleSwarmOptimization(self.graph)
        result = alg.optimize(...)
    
    # 2. Bant genişliği kontrolü
    is_valid, min_bw, reason = self.checker.check_constraint(
        result.path, 
        case.bandwidth_requirement
    )
    
    # 3. Maliyet hesaplama (başarılı ise)
    if is_valid:
        weighted_cost = self.metrics_service.calculate_weighted_cost(
            result.path, 
            case.weights['delay'],
            case.weights['reliability'],
            case.weights['resource']
        )
    
    # 4. Sonuç döndürme
    return {
        "success": is_valid,
        "time": execution_time_ms,
        "weighted_cost": weighted_cost,
        "failure_reason": reason if not is_valid else None
    }
```

### Toplanan İstatistikler

Her algoritma için:
- ✅ **Başarı Oranı** (Success Rate): Başarılı çalıştırma / Toplam çalıştırma
- ✅ **Bant Genişliği Memnuniyeti** (Bandwidth Satisfaction Rate)
- ✅ **Ortalama Maliyet** (Overall Average Cost)
- ✅ **Ortalama Süre** (Overall Average Time) - milisaniye
- ✅ **En İyi Maliyet** (Best Cost)
- ✅ **Başarısızlık Detayları** (Failure Details)

### Sonuç Formatı
```python
{
    "timestamp": "2025-01-XX...",
    "n_test_cases": 25,
    "total_time_sec": 123.45,
    "comparison_table": [
        {
            "algorithm": "GA",
            "success_rate": 0.96,
            "bandwidth_satisfaction_rate": 0.96,
            "overall_avg_cost": 12.34,
            "overall_avg_time_ms": 45.67,
            "best_cost": 10.12
        },
        # ... ACO, PSO
    ],
    "failure_report": {
        "total_failures": 10,
        "details": [...]
    }
}
```

---

## 🔄 Çalışma Akışı

### Senaryo 1: Test Senaryolarını Yükle

```
Kullanıcı "Test Senaryolarını Yükle" Butonuna Tıklar
    ↓
main_window._on_load_test_scenarios() çağrılır
    ↓
TestCaseGenerator.get_predefined_test_cases() → 25 senaryo
    ↓
ScenariosDialog(scenarios) → Modal dialog açılır
    ↓
Kullanıcı senaryoları görüntüler (filtreleme, arama yapabilir)
    ↓
Dialog kapatılır (sadece görüntüleme, çalıştırma yok)
```

### Senaryo 2: Deneyleri Çalıştır

```
Kullanıcı "Deneyleri Çalıştır" Butonuna Tıklar
    ↓
main_window._on_run_experiments(n_tests, n_repeats) çağrılır
    ↓
ExperimentsWorker (QThread) oluşturulur ve başlatılır
    ↓
[BACKGROUND THREAD]
    ├─ TestCaseGenerator → Test case'leri üret
    ├─ ExperimentRunner oluştur
    └─ runner.run_experiments(test_cases) başlat
        │
        ├─ Her algoritma için (GA, ACO, PSO):
        │   ├─ Her test case için:
        │   │   ├─ n_repeats tekrar (varsayılan 5):
        │   │   │   ├─ Algoritma optimize() çağrısı
        │   │   │   ├─ Bant genişliği kontrolü
        │   │   │   ├─ Maliyet hesaplama
        │   │   │   └─ Sonuç kaydetme
        │   │   └─ İstatistik toplama
        │   └─ Algoritma ortalamaları hesapla
        │
        └─ Sonuçları sırala ve döndür
    ↓
[UI THREAD - Signal Handler]
    ├─ progress.emit() → İlerleme güncelleme
    ├─ finished.emit(result) → Deney tamamlandı
    └─ TestResultsDialog(result) → Sonuçları göster
```

---

## 📝 Kullanım Adımları

### Adım 1: Test Senaryolarını Görüntüleme

1. **Graf Yükleme/Oluşturma**
   - Ana pencerede bir graf yükleyin veya oluşturun

2. **Test Senaryoları Butonuna Tıklama**
   - Sol panelde "Test Senaryoları (S, D, B)" kartını genişletin
   - "🕑 Test Senaryolarını Yükle" butonuna tıklayın

3. **Senaryo Listesini İnceleme**
   - `ScenariosDialog` penceresi açılır
   - 25 önceden tanımlanmış senaryo listelenir
   - Filtreleme, arama yapabilirsiniz
   - Tam ekran modu için F11 tuşuna basın

4. **Dialog Kapatma**
   - Pencereyi kapatın (sadece görüntüleme amaçlı)

### Adım 2: Deneyleri Çalıştırma

1. **Graf Yükleme/Oluşturma**
   - Ana pencerede bir graf yükleyin veya oluşturun

2. **Deney Ayarları**
   - Sol panelde "Önceden Tanımlı Deneyler" kartını genişletin
   - Test sayısı: 25 (önceden tanımlı) veya özel sayı
   - Tekrar sayısı: 5 (varsayılan) veya özel sayı

3. **Deneyleri Başlatma**
   - "▷ Deneyleri Çalıştır" butonuna tıklayın
   - İlerleme çubuğu görünür
   - Status bar'da ilerleme mesajları görünür

4. **Deney Süreci**
   - **Background Thread** çalışır (UI donmaz)
   - Her algoritma (GA, ACO, PSO) için:
     - Her test case için n_repeats tekrar
     - Toplam: 5 algoritma × 25 test case × 5 tekrar = **375 çalıştırma**

5. **Sonuçları Görüntüleme**
   - Deney tamamlandığında `TestResultsDialog` otomatik açılır
   - Karşılaştırma tablosu görüntülenir
   - Başarısızlık raporu (varsa) gösterilir
   - İstatistikler: Başarı oranı, Ortalama maliyet, Ortalama süre

---

## 🔧 Teknik Detaylar

### Thread Yönetimi
- `ExperimentsWorker` → `QThread` (UI donmaması için)
- `progress` signal → UI güncellemeleri
- `finished` signal → Sonuç gösterimi
- `error` signal → Hata yönetimi

### İlerleme Takibi
```python
# Progress callback
def progress_callback(current, total, message):
    self.progress.emit(current, total, message)
    # UI: progress_bar.setValue(current/total * 100)
    # UI: status_bar.showMessage(message)
```

### Hata Yönetimi
- Her `_execute_single_run()` try-except ile sarılı
- Başarısız çalıştırmalar `failure_report`'a eklenir
- Exception'lar yakalanır ve loglanır

### Performans
- **Paralel çalıştırma yok** (sıralı)
- Her algoritma sırayla test edilir
- Büyük graflar için süre uzayabilir
- UI donmaması için QThread kullanılır

---

## 📊 Örnek Sonuç

```
Deney Tamamlandı!
─────────────────
Test Case Sayısı: 25
Tekrar Sayısı: 5
Toplam Süre: 123.45 saniye

Karşılaştırma Tablosu:
┌──────────┬──────────────┬──────────────┬──────────────┬───────────────┐
│ Algoritma│ Başarı Oranı │ Ort. Maliyet │ Ort. Süre(ms)│ En İyi Maliyet│
├──────────┼──────────────┼──────────────┼──────────────┼───────────────┤
│ GA       │ 96%          │ 12.34        │ 45.67        │ 10.12         │
│ ACO      │ 92%          │ 13.56        │ 52.34        │ 11.23         │
│ PSO      │ 88%          │ 14.78        │ 48.90        │ 12.45         │
└──────────┴──────────────┴──────────────┴──────────────┴───────────────┘

Başarısızlık Raporu:
- Toplam Başarısızlık: 10
- Detaylar: [test_case_id, algorithm, reason, ...]
```

---

## 📌 Önemli Notlar

1. **Test Senaryoları ≠ Deney Çalıştırma**
   - "Test Senaryolarını Yükle" → Sadece listeleme
   - "Deneyleri Çalıştır" → Gerçek test çalıştırma

2. **Graf Gereksinimi**
   - Her iki işlem için de graf yüklenmiş olmalı

3. **Zamanlama**
   - 25 test case × 3 algoritma × 5 tekrar = 375 çalıştırma
   - Büyük graflar için süre uzayabilir (dakikalar)

4. **Thread Güvenliği**
   - UI güncellemeleri signal-slot mekanizması ile yapılır
   - Worker thread'den direkt UI erişimi yok

5. **Seed Değeri**
   - `TestCaseGenerator` seed=42 kullanır (reproducibility)
   - Algoritmalar seed=None kullanır (stochastic behavior)

---

## 🔗 İlgili Dosyalar

### Core Files
- `app/src/experiments/test_cases.py` - Test case üretimi
- `app/src/experiments/experiment_runner.py` - Deney çalıştırıcı
- `app/src/services/metrics_service.py` - Maliyet hesaplama

### UI Files
- `app/src/ui/main_window.py` - Ana pencere ve worker
- `app/src/ui/components/experiments_panel.py` - Deney paneli
- `app/src/ui/components/scenarios_dialog.py` - Senaryo dialog
- `app/src/ui/components/test_results_dialog.py` - Sonuç dialog

### Algorithm Files
- `app/src/algorithms/genetic_algorithm.py` - GA
- `app/src/algorithms/aco.py` - ACO
- `app/src/algorithms/pso.py` - PSO

---

**Son Güncelleme** 25.12.2025  
**Versiyon:** 1.0  
*Erkan TURGUT*

