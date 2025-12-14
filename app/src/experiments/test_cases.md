# test_cases.py - Test Case Generator

Test case üreteci ve bant genişliği kısıt kontrolü modülü.

## Ana Bileşenler

### 1. TestCase
Tek bir test senaryosu. (S, D, B) üçlüsünü içerir:
- `source` (S): Kaynak düğüm
- `destination` (D): Hedef düğüm
- `bandwidth_requirement` (B): Talep edilen bant genişliği (Mbps)
- `weights`: QoS ağırlıkları (delay, reliability, resource)

### 2. TestResult
Test sonucu - başarılı veya başarısız:
- `success`: Başarı durumu
- `path`: Bulunan yol
- `path_min_bandwidth`: Yolun minimum bant genişliği
- `failure_reason`: Başarısızlık nedeni (varsa)

### 3. TestCaseGenerator
Test case'leri otomatik üretir.

**Özellikler:**
- En az 20 farklı (S, D, B) kombinasyonu üretir
- Farklı mesafelerde S-D çiftleri seçer (kısa, orta, uzun)
- 10 farklı ağırlık senaryosu kullanır
- 10 farklı bant genişliği gereksinimi (100-1000 Mbps)

**Ağırlık Senaryoları:**
- Sadece Gecikme (delay=1.0)
- Sadece Güvenilirlik (reliability=1.0)
- Sadece Kaynak (resource=1.0)
- İkili kombinasyonlar
- Eşit ağırlık (0.33, 0.33, 0.34)
- Öncelikli senaryolar

**Metodlar:**
- `generate_test_cases(n_cases)`: Rastgele test case'leri üretir
- `get_predefined_test_cases()`: Önceden tanımlanmış 25 test senaryosu
- `check_bandwidth_constraint(path, bandwidth_requirement)`: Bant genişliği kontrolü

### 4. BandwidthConstraintChecker
Yolun bant genişliği kısıtını kontrol eder.

**Metodlar:**
- `get_path_min_bandwidth(path)`: Yoldaki minimum bant genişliğini bulur
- `check_constraint(path, bandwidth_requirement)`: Kısıtı kontrol eder
- `find_bottleneck(path)`: Darboğaz bağlantıyı bulur

**Kontrol Mantığı:**
```
Yol geçerli mi? → Her kenarın bandwidth'si >= B mi?
```

## Kullanım

```python
from src.experiments.test_cases import TestCaseGenerator, BandwidthConstraintChecker

# Generator oluştur
generator = TestCaseGenerator(graph, seed=42)

# Test case'leri üret
test_cases = generator.generate_test_cases(n_cases=25)

# Bant genişliği kontrolü
checker = BandwidthConstraintChecker(graph)
is_valid, min_bw, reason = generator.check_bandwidth_constraint(
    path=[0, 5, 10, 15],
    bandwidth_requirement=500.0
)
```

## Bant Genişliği Gereksinimleri

10 farklı seviye:
- 100-200 Mbps: Düşük (çoğu yol karşılar)
- 300-500 Mbps: Orta
- 600-800 Mbps: Yüksek (bazı yollar başarısız olabilir)
- 900-1000 Mbps: Çok yüksek (çoğu yol başarısız olabilir)

