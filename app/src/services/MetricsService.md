# MetricsService - Metrik Motoru

Metrik servisi, bir yol (path) için QoS metriklerini hesaplar ve ağırlıklı maliyeti döndürür.

## Hesaplanan Metrikler

### 1. Total Delay (Toplam Gecikme)

**Hesaplama:**
- Yol üzerindeki tüm düğümlerin `processing_delay` değerleri toplanır
- Yol üzerindeki tüm kenarların `delay` değerleri toplanır

**Formül:**
```
total_delay = Σ(node.processing_delay) + Σ(edge.delay)
```

### 2. Total Reliability (Toplam Güvenilirlik)

**Hesaplama:**
- Yol üzerindeki tüm düğümlerin `reliability` değerleri çarpılır
- Yol üzerindeki tüm kenarların `reliability` değerleri çarpılır

**Formül:**
```
total_reliability = Π(node.reliability) × Π(edge.reliability)
```

### 3. Resource Cost (Kaynak Maliyeti)

**Hesaplama:**
- Her kenar için: `1 / bandwidth`
- Düşük bandwidth = yüksek maliyet

**Formül:**
```
resource_cost = Σ(1 / edge.bandwidth)
```

### 4. Weighted Cost (Ağırlıklı Maliyet)

**Hesaplama:**
Üç metriğin ağırlıklı toplamı:

```
weighted_cost = delay_w × total_delay 
              + reliability_w × (1 - total_reliability)
              + resource_w × resource_cost
```

**Ağırlıklar:**
- `delay_w`: Gecikme ağırlığı (0-1 arası)
- `reliability_w`: Güvenilirlik ağırlığı (0-1 arası)
- `resource_w`: Kaynak ağırlığı (0-1 arası)

## Kullanım

```python
from src.services.metrics_service import MetricsService

# Servis oluştur
metrics = MetricsService(graph)

# Tüm metrikleri hesapla
result = metrics.calculate_all(
    path=[0, 5, 10, 15],
    delay_w=0.33,
    reliability_w=0.33,
    resource_w=0.34
)

# Sadece ağırlıklı maliyeti al (algoritmalar için)
cost = metrics.calculate_weighted_cost(
    path=[0, 5, 10, 15],
    delay_w=0.33,
    reliability_w=0.33,
    resource_w=0.34
)
```

## Dönen Değerler

`PathMetrics` dataclass:
- `total_delay`: Toplam gecikme (ms)
- `total_reliability`: Toplam güvenilirlik (0-1 arası)
- `resource_cost`: Kaynak maliyeti
- `weighted_cost`: Ağırlıklı toplam maliyet

## Notlar

- Geçersiz kenarlar için çok yüksek maliyet döndürülür (1e6)
- Tüm algoritmalar bu servisi kullanır
- UI'de sonuçlar gösterilirken de kullanılır

