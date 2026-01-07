# 🌱 Seed Yönetimi ve Tekrarlanabilirlik (Reproducibility)

Bu dokümantasyon, projede kullanılan seed mekanizmasını ve tekrarlanabilirlik özelliklerini açıklar.

---

## 📌 Seed Nedir?

**Seed (Tohum)**, rastgele sayı üretecinin (Random Number Generator - RNG) başlangıç durumunu belirleyen bir tam sayıdır. Aynı seed ile başlatılan RNG, her zaman aynı rastgele sayı dizisini üretir.

### Neden Önemli?

| Avantaj | Açıklama |
|---------|----------|
| **Tekrarlanabilirlik** | Aynı sonuçları tekrar elde edebilme |
| **Hata Ayıklama** | Sorunlu bir çalışmayı tekrar edebilme |
| **Karşılaştırma** | Farklı parametreleri adil şekilde karşılaştırabilme |
| **Akademik Gereklilik** | Bilimsel çalışmalarda doğrulanabilirlik |

---

## 🔧 Projede Seed Kullanımı

### Desteklenen Algoritmalar

Tüm stokastik algoritmalar seed desteğine sahiptir:

| Algoritma | Dosya | Seed Kullanımı |
|-----------|-------|----------------|
| **Genetic Algorithm (GA)** | `genetic_algorithm.py` | ✅ Tam destek |
| **Ant Colony (ACO)** | `aco.py` | ✅ Tam destek |
| **Particle Swarm (PSO)** | `pso.py` | ✅ Tam destek |
| **Simulated Annealing (SA)** | `simulated_annealing.py` | ✅ Tam destek |
| **Q-Learning** | `q_learning.py` | ✅ Tam destek |
| **SARSA** | `sarsa.py` | ✅ Tam destek |

---

## 📊 Seed Çalışma Modları

### 1. Stokastik Mod (seed=None)

Seed belirtilmediğinde, sistem otomatik olarak benzersiz bir seed üretir:

```python
# Otomatik seed üretimi formülü
seed_val = time.time_ns() % (2**31) + os.getpid() + call_counter
random.seed(seed_val)
```

**Özellikler:**
- Her çalışmada farklı sonuç
- Multi-Start için ideal
- Otomatik üretilen seed sonuçta kaydedilir

### 2. Deterministik Mod (seed=42)

Belirli bir seed verildiğinde, RNG bu değerle başlatılır:

```python
random.seed(42)  # Her zaman aynı sonuç
```

**Özellikler:**
- Her çalışmada birebir aynı sonuç
- Hata ayıklama için ideal
- Sonuçların doğrulanabilirliği

---

## 💻 Kod Örnekleri

### Algoritma Oluşturma

```python
from src.algorithms.genetic_algorithm import GeneticAlgorithm

# Stokastik mod - her seferinde farklı sonuç
ga = GeneticAlgorithm(graph, seed=None)
result1 = ga.optimize(source=1, destination=20, weights=weights)

# Deterministik mod - her seferinde aynı sonuç  
ga = GeneticAlgorithm(graph, seed=42)
result2 = ga.optimize(source=1, destination=20, weights=weights)
```

### Sonuçtan Seed Alma

Her optimizasyon sonucu, kullanılan seed değerini içerir:

```python
result = ga.optimize(source=1, destination=20, weights=weights)

# Kullanılan seed'i görüntüle
print(f"Kullanılan Seed: {result.seed_used}")

# Aynı sonucu tekrar almak için:
ga_repeat = GeneticAlgorithm(graph, seed=result.seed_used)
result_repeat = ga_repeat.optimize(source=1, destination=20, weights=weights)

# result.path == result_repeat.path (Eşit olmalı!)
```

### Multi-Start ile Kullanım

```python
# N farklı seed ile çalıştır, en iyi sonucu seç
best_result = None
for run in range(10):
    ga = GeneticAlgorithm(graph, seed=None)  # Her run farklı seed
    result = ga.optimize(source, destination, weights)
    
    if best_result is None or result.fitness < best_result.fitness:
        best_result = result

print(f"En iyi sonuç - Seed: {best_result.seed_used}")
```

---

## 🖥️ UI'da Seed Gösterimi

### Sonuç Paneli

Optimizasyon tamamlandığında, kullanılan seed değeri sonuç panelinde gösterilir:

```
┌─────────────────────────────────────┐
│  🎯 Optimizasyon Sonucu             │
├─────────────────────────────────────┤
│  Algoritma: Genetic Algorithm       │
│  Toplam Maliyet: 0.4523             │
│  Seed: 1704567890123                │  ← Tekrarlanabilirlik için
│  Hesaplama Süresi: 1.23s            │
└─────────────────────────────────────┘
```

### Deney Sonuçları

Toplu deney sonuçlarında her algoritma için kullanılan seed bilgisi kaydedilir:

| Sütun | Açıklama |
|-------|----------|
| `best_seed` | En iyi sonucu veren çalışmanın seed değeri |
| `seed_used` | (Failure raporlarında) Başarısız çalışmanın seed değeri |

---

## 📁 Export'larda Seed Bilgisi

### JSON Export

```json
{
  "algorithm": "GeneticAlgorithm",
  "path": [1, 5, 12, 18, 20],
  "fitness": 0.4523,
  "seed_used": 1704567890123,
  "computation_time_ms": 1234.5
}
```

### CSV Export

```csv
algorithm,fitness,path,seed_used,computation_time_ms
GeneticAlgorithm,0.4523,"[1, 5, 12, 18, 20]",1704567890123,1234.5
```

### PDF Rapor

PDF raporlarında "Tekrarlanabilirlik Bilgisi" bölümünde seed değeri yer alır.

---

## 🧪 Test Case Generator

Test senaryoları oluşturulurken tutarlılık için seed kullanılır:

```python
from src.experiments.test_case_generator import TestCaseGenerator

# seed=42 ile oluşturulan test senaryoları her zaman aynı
generator = TestCaseGenerator(graph, seed=42)
scenarios = generator.generate_scenarios(n=10)
```

> **Not:** Test senaryoları deterministic (seed=42), algoritmalar stochastic (seed=None) çalışır.

---

## ⚙️ Uygulama İçi Ayarlar

### Graf Oluşturma

Rastgele graf oluşturulurken seed belirtilebilir:

```python
from src.services.graph_service import GraphService

# Aynı seed = aynı topoloji
service = GraphService(seed=42)
graph = service.generate_erdos_renyi(n_nodes=100, probability=0.15)
```

### Proje Verisi Yükleme

CSV dosyasından proje verisi yüklendiğinde, topoloji deterministiktir (seed gerekli değil).

---

## 📋 Özet Tablo

| Senaryo | Seed Değeri | Davranış |
|---------|-------------|----------|
| Normal optimizasyon | `None` | Her seferinde farklı sonuç |
| Sonuç tekrarlama | `result.seed_used` | Birebir aynı sonuç |
| Deney karşılaştırması | `42` (sabit) | Adil karşılaştırma |
| Multi-Start | `None` (her run) | Çeşitli çözümler üretir |
| Graf oluşturma | İsteğe bağlı | Aynı topoloji garanti |

---

## 🔗 İlgili Dosyalar

- [Geliştirici Rehberi](./Gelistirici_Rehberi.md) - Algoritma kullanım örnekleri
- [Genetik Algoritma](./Genetik_Algoritma.md) - GA detaylı dokümantasyonu
- [Test Senaryoları](./Test_Senaryoları_Deney_Duzenegi.md) - Deney düzeneği açıklaması

---

> **⚠️ Önemli:** Seed değeri 32-bit integer aralığında olmalıdır (0 - 2,147,483,647).

---

*Son güncelleme: Ocak 2025*
