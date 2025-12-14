# experiment_runner.py - Experiment Runner

Toplu deney çalıştırıcı. Tüm algoritmaları test case'ler üzerinde çalıştırır ve sonuçları toplar.

## Ana Bileşenler

### 1. ExperimentRunner
Ana deney çalıştırıcı sınıfı.

**Özellikler:**
- En az 20 farklı test case üzerinde çalışır
- En az 2 farklı algoritmayı karşılaştırır
- Her test için en az 5 tekrar yapar
- Başarısız testleri gerekçeleriyle raporlar
- Çalışma süresini ölçer

**Desteklenen Algoritmalar:**
- GeneticAlgorithm
- AntColonyOptimization
- ParticleSwarmOptimization
- SimulatedAnnealing
- QLearning
- SARSA

**Metodlar:**
- `run_experiments(test_cases)`: Tüm deneyleri çalıştırır
- `_run_repeated_test()`: Tek test için tekrarlı deney
- `_run_single_test()`: Tek bir test çalıştırır

### 2. ExperimentResult
Deney sonuçlarını tutar.

**İçerik:**
- `test_cases`: Test case listesi
- `algorithm_results`: Algoritma bazında sonuçlar
- `total_time_sec`: Toplam çalışma süresi
- `failure_report`: Başarısızlık raporu
- `comparison_table`: Karşılaştırma tablosu

**Metodlar:**
- `get_comparison_table()`: Algoritmaları karşılaştıran tablo
- `to_dict()`: JSON'a dönüştürülebilir format

### 3. RepeatResult
Tekrarlı deney sonucu (5+ tekrar).

**İstatistikler:**
- `avg_cost`: Ortalama maliyet
- `std_cost`: Standart sapma
- `min_cost`, `max_cost`: Min/Max maliyet
- `avg_time_ms`: Ortalama çalışma süresi
- `success_rate`: Başarı oranı
- `bandwidth_satisfaction_rate`: Bant genişliği karşılama oranı
- `failures`: Başarısız testler listesi

### 4. AlgorithmResult
Tek bir algoritma çalıştırma sonucu.

**İçerik:**
- `path`: Bulunan yol
- `weighted_cost`: Ağırlıklı maliyet
- `total_delay`, `total_reliability`, `resource_cost`: Metrikler
- `computation_time_ms`: Çalışma süresi
- `success`: Başarı durumu
- `bandwidth_satisfied`: Bant genişliği kısıtı karşılandı mı?
- `failure_reason`: Başarısızlık nedeni

### 5. FailureReport
Başarısız testlerin raporu.

**Özellikler:**
- Nedene göre gruplama
- Algoritmaya göre gruplama
- Detaylı açıklamalar

## Kullanım

```python
from src.experiments.experiment_runner import ExperimentRunner
from src.experiments.test_cases import TestCaseGenerator

# Test case'leri üret
generator = TestCaseGenerator(graph)
test_cases = generator.generate_test_cases(n_cases=25)

# Deney çalıştırıcı oluştur
runner = ExperimentRunner(
    graph=graph,
    n_repeats=5,  # PDF gereksinimi: en az 5
    algorithms=["GeneticAlgorithm", "AntColonyOptimization"]  # En az 2
)

# Deneyleri çalıştır
result = runner.run_experiments(test_cases)

# Sonuçları incele
print(f"Toplam süre: {result.total_time_sec} saniye")
print(f"Başarısız test: {len(result.failure_report.failed_cases)}")
comparison = result.get_comparison_table()
```

## Başarısızlık Nedenleri

- `NO_PATH`: Kaynak ve hedef arasında yol yok
- `BANDWIDTH_INSUFFICIENT`: Bant genişliği yetersiz
- `TIMEOUT`: Algoritma zaman aşımı
- `INVALID_SOURCE/DESTINATION`: Geçersiz düğüm
- `SAME_NODE`: Kaynak ve hedef aynı
- `ALGORITHM_ERROR`: Algoritma hatası

## İstatistikler

Her test için hesaplanan metrikler:
- Ortalama, standart sapma, min, max maliyet
- Ortalama çalışma süresi
- Başarı oranı
- Bant genişliği karşılama oranı

## Notlar

- Bant genişliği kısıtı her testte kontrol edilir
- Başarısız testler detaylı gerekçelerle raporlanır
- Sonuçlar JSON formatına dönüştürülebilir
- Progress callback ile ilerleme takibi yapılabilir

