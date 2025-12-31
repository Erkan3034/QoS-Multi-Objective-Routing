# 🧬 Genetik Algoritma (GA) - Teknik Dokümantasyon

Projemizde kullanılan Genetik Algoritma, **Darwin'in doğal seçilim teorisini** ağ yönlendirme problemine uygular. "Kötü yollar elenir, iyi yollar çoğalır, mutasyonlar yeni keşifler sağlar."

---

## 📋 Varsayılan Parametreler

| Parametre | Değer | Açıklama |
|-----------|-------|----------|
| `POPULATION_SIZE` | 200 | Popülasyondaki birey sayısı (ağ büyüklüğüne göre otomatik ölçeklenir) |
| `GENERATIONS` | 100 | Maksimum nesil sayısı |
| `MUTATION_RATE` | 0.05 (5%) | Mutasyon oranı |
| `CROSSOVER_RATE` | 0.8 (80%) | Çaprazlama oranı |
| `ELITISM` | 0.1 (10%) | Direkt aktarılan en iyi bireyler |

---

## 🔄 Evrim Döngüsü (Ana Algoritma)

```
1. Başlangıç Popülasyonu Oluştur
   ├── Shortest paths (hop, delay, reliability bazlı)
   ├── Guided paths (hub düğümlere yönelir)
   └── Random paths (keşif için)

2. Her Nesil İçin:
   ├── Fitness Hesapla → Delay + Reliability + Resource
   ├── Elitizm → En iyi %10 direkt aktar
   ├── Tournament Selection → Ebeveyn seç
   ├── Crossover → İki ebeveynden çocuk oluştur
   ├── Mutasyon → Rastgele değişiklik
   └── Yakınsama Kontrolü → Erken durdurma

3. En İyi Yolu Döndür
```

---

## 🎯 Fitness Fonksiyonu (Yol Kalitesi)

**Proje Yönergesine 100% Uyumlu:**

```
TotalCost = W1 × delay_normalized + W2 × reliability_normalized + W3 × resource_normalized
```

### Metrik Hesaplamaları

| Metrik | Formül | Açıklama |
|--------|--------|----------|
| **TotalDelay** | `Σ(LinkDelay) + Σ(ProcessingDelay)` | Ara düğümler hariç S ve D |
| **ReliabilityCost** | `Σ[-log(LinkReliability)] + Σ[-log(NodeReliability)]` | Logaritmik ceza |
| **ResourceCost** | `Σ(1Gbps / Bandwidth)` | Düşük BW = yüksek maliyet |

### Normalizasyon (0-1 aralığı)

```python
delay_normalized = min(total_delay / 200ms, 1.0)
reliability_normalized = min(-log(reliability) / 10.0, 1.0)
resource_normalized = min(resource_cost / 200.0, 1.0)
```

---

## 🧬 Genetik Operatörler

### 1. Selection (Seçilim) - Tournament
- K birey rastgele seçilir (varsayılan K=5)
- En iyi fitness'a sahip olan ebeveyn olur
- Bu, kötü bireylerin de şansı olması için kullanılır

### 2. Crossover (Çaprazlama) - Edge-Based

```
Ebeveyn 1: [1, 5, 8, 12, 20]
Ebeveyn 2: [1, 3, 8, 15, 20]
         ───────↑ ortak düğüm

Çocuk 1: [1, 5, 8, 15, 20]  (P1'in başı + P2'nin sonu)
Çocuk 2: [1, 3, 8, 12, 20]  (P2'nin başı + P1'nin sonu)
```

### 3. Mutasyon - Diversity'e Göre Adaptif

| Diversity | Strateji | Açıklama |
|-----------|----------|----------|
| < 0.05 | **Segment Replacement** | Yolun bir kesitini tamamen değiştir (agresif) |
| < 0.15 | **Node Insertion** | Mevcut yola detour ekle |
| ≥ 0.15 | **Node Replacement** | Tek bir ara düğümü değiştir |

---

## ⚡ Performans Optimizasyonları

1. **Paralel İşleme**: 500+ düğümlü ağlarda otomatik aktif (multiprocessing pool)
2. **LRU Cache**: Shortest path hesaplamaları önbelleklenir
3. **Neighbor Cache**: Graf komşuluk bilgisi ön yüklenir
4. **Erken Durdurma**: 20 nesil boyunca iyileşme yoksa durur

---

## 🎛️ Adaptif Davranışlar

### Popülasyon Ölçekleme (Ağ Büyüklüğüne Göre)

| Düğüm Sayısı | Popülasyon |
|--------------|------------|
| < 100 | 200 birey |
| < 500 | 260 birey |
| ≥ 500 | 500 birey |

### Mutation Rate Artışı (Düşük Diversity'de)

```python
if diversity < 0.1:
    mutation_rate = base_rate × 2.5  # Lokal optimumdan kaçış
```

---

## 📊 Çıktılar (GAResult)

| Alan | Tip | Açıklama |
|------|-----|----------|
| `path` | List[int] | Bulunan en iyi yol |
| `fitness` | float | Ağırlıklı toplam maliyet |
| `generation` | int | En iyi yolun bulunduğu nesil |
| `computation_time_ms` | float | Hesaplama süresi |
| `convergence_history` | List[float] | Nesil bazlı en iyi fitness (grafik için) |
| `diversity_history` | List[float] | Popülasyon çeşitliliği takibi |
| `seed_used` | int | Kullanılan random seed (reproducibility) |

---

## 🔑 Önemli Notlar

1. **Stokastik Algoritma**: Her çalışmada farklı sonuç verebilir (seed verilmezse)
2. **Bandwidth Kısıtı**: Yetersiz BW'ye sahip edge'ler otomatik filtrelenir
3. **Multi-Start Desteği**: UI'dan N kez çalıştırıp en iyi sonucu alabilirsiniz
4. **Experiment Mode**: `use_standard_metrics=True` ile diğer algoritmalarla adil karşılaştırma

---

## 🐵 Chaos Monkey Entegrasyonu

GA, Chaos Monkey özelliği ile entegre çalışır:

1. Edge kırıldığında `edge_broken` signal'i tetiklenir
2. `_on_edge_broken()` mevcut kaynak/hedef için yol kontrolü yapar
3. Yol varsa, **mevcut GA parametreleri ve ağırlıklarla** otomatik yeniden optimize eder
4. Graf güncel haliyle (kırık edge olmadan) yeni en iyi yolu bulur

Bu sayede ağda bir link arızalandığında sistem **otomatik olarak alternatif yol** bulur (Self-Healing Routing).
