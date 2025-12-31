# Toplu Deney Çalışma Prensipleri

Bu rapor, QoS Çok Amaçlı Yönlendirme uygulamasındaki "Toplu Deney" özelliğinin teknik işleyişini açıklar.

---

## 1. Genel Bakış

Toplu Deney, tüm yönlendirme algoritmalarının (GA, ACO, PSO, SA, QL) standartlaştırılmış test senaryoları üzerinde performansını ölçer ve karşılaştırır.

**Temel Özellikler:**
- 25 farklı test senaryosu
- 4 farklı ağırlık profili
- Her senaryo için 5 tekrar
- Senaryo bazlı detaylı istatistikler
- Algoritma ranking tablosu
- Karşılaştırma grafikleri

---

## 2. Test Senaryoları

`TestCaseGenerator` sınıfı 25 adet test senaryosu üretir:

### Senaryo Parametreleri

| Parametre | Değer |
|-----------|-------|
| **Kaynak/Hedef** | Graf düğümlerinden rastgele |
| **Bant Genişliği** | 100-1000 Mbps (100 adımlarla) |

### 4 Farklı Ağırlık Profili

| Profil | Delay | Reliability | Resource |
|--------|-------|-------------|----------|
| Gecikme Odaklı | 0.7 | 0.2 | 0.1 |
| Güvenilirlik Odaklı | 0.2 | 0.7 | 0.1 |
| Kaynak Odaklı | 0.2 | 0.1 | 0.7 |
| Dengeli | 0.33 | 0.33 | 0.34 |

> Senaryolar döngüsel olarak farklı profiller alır: #1=Gecikme, #2=Güvenilirlik, #3=Kaynak, #4=Dengeli, #5=Gecikme...

---

## 3. Yürütme Süreci

### İş Parçacığı Yapısı

```
UI Thread                    Worker Thread (ExperimentsWorker)
    │                                │
    │─── Başlat ──────────────────>  │
    │                                ├─ TestCaseGenerator()
    │                                ├─ ExperimentRunner.run_experiments()
    │  <─── Progress sinyal ────────┤   ├─ GA, ACO, PSO, SA, QL çalıştır
    │  <─── Progress sinyal ────────┤   ├─ Her senaryo × 5 tekrar
    │                                │   └─ Ranking hesapla
    │  <─── Finished sinyal ────────┤
    │                                │
    └── TestResultsDialog aç ───────┘
```

### Toplam İşlem Sayısı

```
25 senaryo × 5 algoritma × 5 tekrar = 625 bireysel optimizasyon
```

---

## 4. Veri Toplama

Her senaryo için her algoritmadan şu veriler toplanır:

| Metrik | Açıklama |
|--------|----------|
| `all_costs` | Tüm tekrarların maliyet değerleri |
| `avg_cost` | Ortalama maliyet |
| `std_cost` | Standart sapma |
| `min_cost` | En iyi (minimum) maliyet |
| `max_cost` | En kötü (maksimum) maliyet |
| `avg_time_ms` | Ortalama çalışma süresi |
| `success_rate` | Başarı oranı (0-1) |
| `best_seed` | En iyi sonucu veren seed |

---

## 5. Ranking Sistemi

Her senaryo için algoritmalar ortalama maliyete göre sıralanır:

```python
# Örnek: Senaryo #1
1. GA   → 0.0249 (🥇)
2. ACO  → 0.0251 (🥈)
3. PSO  → 0.0265 (🥉)
4. SA   → 0.0278
5. QL   → 0.0312
```

Tüm senaryolardaki sıralamalar toplanarak genel ranking özeti oluşturulur:

| Algoritma | 🥇 1. | 🥈 2. | 🥉 3. | Toplam Kazanma |
|-----------|-------|-------|-------|----------------|
| GA | 15 | 6 | 3 | 15 |
| ACO | 8 | 10 | 5 | 8 |
| ... | | | | |

---

## 6. Sonuç Penceresi Sekmeleri

| Sekme | İçerik |
|-------|--------|
| 📊 Özet | Test sayısı, toplam süre, başarısız test |
| 📈 Algoritma Karşılaştırması | Genel ortalama tablo |
| 📋 Senaryo Detayları | Seçilen senaryo için tüm algoritmalar |
| 🏆 Ranking | Algoritma sıralama performansı |
| 📊 Grafikler | Bar chart (maliyet, süre) |
| ⚠️ Başarısızlıklar | Hata detayları ve sebepleri |

---

## 7. Export

| Format | İçerik |
|--------|--------|
| **JSON** | Tüm veriler (comparison_table, scenario_results, ranking_summary) |
| **CSV** | Algoritma özeti + senaryo bazlı detaylar |

---

> Son güncelleme: 2025-12-31
