# 🔧 Backend TODO - Yapılması Gereken Değişiklikler

> Son Güncelleme: 07-12-2025

---

## 🔴 KRİTİK (Mutlaka Yapılmalı)

### 1. Bandwidth (B) Kısıtının Algoritmalara Entegrasyonu

**Problem:** Şu an algoritmalar yol ararken bandwidth'i kontrol etmiyor. Yol bulunduktan SONRA `experiment_runner.py`'de kontrol yapılıyor ve yetersizse "FAILED" işaretleniyor.

**Yapılması Gereken:**
- [ ] Her algoritmada `optimize()` metoduna `bandwidth_requirement` parametresi ekle
- [ ] Yol arama sırasında `edge['bandwidth'] >= bandwidth_requirement` kontrolü yap
- [ ] Yetersiz bandwidth'li kenarları komşu listesinden çıkar

**Etkilenen Dosyalar:**
- `src/algorithms/genetic_algorithm.py`
  - `_generate_random_path()` metodunda komşu filtreleme
  - `_mutate()` metodunda yeni düğüm seçerken bandwidth kontrolü
  
- `src/algorithms/aco.py`
  - `_construct_solution()` metodunda komşu filtreleme
  - `_calculate_visibility()` metodunda bandwidth'i dikkate al
  
- `src/algorithms/pso.py`
  - Path construction'da bandwidth kontrolü
  
- `src/algorithms/simulated_annealing.py`
  - `_get_neighbor_solution()` metodunda bandwidth kontrolü
  
- `src/algorithms/q_learning.py`
  - `_get_valid_actions()` metodunda bandwidth filtresi
  
- `src/algorithms/sarsa.py`
  - `_get_valid_actions()` metodunda bandwidth filtresi

**Örnek Değişiklik (GA için):**
```
# _generate_random_path metodunda:
# ESKİ:
neighbors = [n for n in self.graph.neighbors(current) if n not in visited]

# YENİ:
neighbors = [
    n for n in self.graph.neighbors(current) 
    if n not in visited 
    and self.graph.edges[current, n]['bandwidth'] >= self.bandwidth_requirement
]
```

---

### 2. DemandData Entegrasyonu

**Problem:** DemandData.csv'deki 30 test case UI'dan deney çalıştırırken otomatik kullanılmıyor.

**Yapılması Gereken:**
- [ ] `test_cases.py`'de `load_from_demand_csv()` fonksiyonu var mı kontrol et
- [ ] `experiment_runner.py`'de DemandData'dan otomatik test case üretimi
- [ ] Her demand için: `source`, `destination`, `demand_mbps` → TestCase

---

## 🟡 ORTA ÖNCELİK

### 3. Deney Sonuçlarının Export'u

**Problem:** Deney sonuçları sadece konsola yazdırılıyor, dosyaya kaydedilmiyor.

**Yapılması Gereken:**
- [ ] `ExperimentResult.to_json()` metodu ekle
- [ ] `ExperimentResult.to_csv()` metodu ekle
- [ ] Sonuçları `results/` klasörüne timestamp ile kaydet

**Çıktı Formatı:**
```
results/
├── experiment_2025-12-07_14-30-00.json
├── comparison_table.csv
└── failure_report.csv
```

---

### 4. Konfigürasyon Eksikleri

**Problem:** `config.py`'de bazı deney parametreleri eksik.

**Yapılması Gereken:**
- [ ] `EXPERIMENT_N_REPEATS: int = 5` ekle
- [ ] `EXPERIMENT_TIMEOUT_SEC: int = 60` ekle
- [ ] `EXPERIMENT_N_TEST_CASES: int = 20` ekle

---

## 🟢 DÜŞÜK ÖNCELİK

### 5. Algoritma Performans İyileştirmeleri

**Yapılması Gereken:**
- [ ] Q-Learning ve SARSA için episode sayısını azalt (5000 → 1000)
- [ ] ACO'da `nx.shortest_path_length` cache'leme
- [ ] GA'da paralel fitness hesaplama

---

### 6. Logging ve Debug

**Yapılması Gereken:**
- [ ] Her algoritmaya verbose mode ekle
- [ ] Deney sırasında progress bar
- [ ] Hata durumlarında detaylı log

---

## 📝 NOTLAR

- B kısıtı olmadan bulunan yollar geçersiz sayılmalı
- PDF'de "B kısıtını karşılamayan yollar başarısız olarak raporlanmalı" yazıyor
- Şu an post-check var ama pre-check (algoritma içi) yok

