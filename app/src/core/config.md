# config.py - Application Configuration

Uygulama genelinde kullanılan konfigürasyon ayarları. `pydantic-settings` kullanarak ortam değişkenleri ve `.env` dosyası desteği sağlar.

## Ana Bileşen

### Settings Class
Tüm uygulama ayarlarını içeren Pydantic Settings sınıfı.

## Ayar Kategorileri

### 1. Genel Ayarlar
- `APP_NAME`: Uygulama adı
- `DEBUG`: Hata ayıklama modu
- `RANDOM_SEED`: Rastgele sayı üreteci seed değeri

### 2. Graf Ayarları
Erdős–Rényi modeli için varsayılan değerler:
- `DEFAULT_NODE_COUNT`: Varsayılan düğüm sayısı (250)
- `DEFAULT_CONNECTION_PROB`: Bağlantı olasılığı (0.4)

**Düğüm Özellikleri:**
- `PROCESSING_DELAY_MIN/MAX`: İşleme gecikmesi aralığı (0.5-2.0 ms)
- `NODE_RELIABILITY_MIN/MAX`: Düğüm güvenilirliği aralığı (0.95-0.999)

**Bağlantı Özellikleri:**
- `BANDWIDTH_MIN/MAX`: Bant genişliği aralığı (100-1000 Mbps)
- `LINK_DELAY_MIN/MAX`: Bağlantı gecikmesi aralığı (3-15 ms)
- `LINK_RELIABILITY_MIN/MAX`: Bağlantı güvenilirliği aralığı (0.95-0.999)

### 3. Genetic Algorithm (GA)
- `GA_POPULATION_SIZE`: Popülasyon boyutu (100)
- `GA_GENERATIONS`: Nesil sayısı (500)
- `GA_MUTATION_RATE`: Mutasyon oranı (0.1)
- `GA_CROSSOVER_RATE`: Çaprazlama oranı (0.8)
- `GA_ELITISM`: Elitizm oranı (0.1)

### 4. Ant Colony Optimization (ACO)
- `ACO_N_ANTS`: Karınca sayısı (50)
- `ACO_N_ITERATIONS`: İterasyon sayısı (100)
- `ACO_ALPHA`: Feromon önemi (1.0)
- `ACO_BETA`: Heuristik önemi (2.0)
- `ACO_EVAPORATION_RATE`: Buharlaşma oranı (0.5)
- `ACO_Q`: Feromon miktarı (100.0)

### 5. Particle Swarm Optimization (PSO)
- `PSO_N_PARTICLES`: Parçacık sayısı (30)
- `PSO_N_ITERATIONS`: İterasyon sayısı (100)
- `PSO_W`: Atalet ağırlığı (0.7)
- `PSO_C1`: Kişisel en iyi ağırlığı (1.5)
- `PSO_C2`: Global en iyi ağırlığı (1.5)

### 6. Simulated Annealing (SA)
- `SA_INITIAL_TEMPERATURE`: Başlangıç sıcaklığı (1000.0)
- `SA_FINAL_TEMPERATURE`: Bitiş sıcaklığı (0.01)
- `SA_COOLING_RATE`: Soğutma oranı (0.995)
- `SA_ITERATIONS_PER_TEMP`: Sıcaklık başına iterasyon (10)

### 7. Q-Learning
- `QL_EPISODES`: Bölüm sayısı (5000)
- `QL_LEARNING_RATE`: Öğrenme oranı (0.1)
- `QL_DISCOUNT_FACTOR`: İndirim faktörü (0.95)
- `QL_EPSILON_START`: Başlangıç epsilon (1.0)
- `QL_EPSILON_END`: Bitiş epsilon (0.01)
- `QL_EPSILON_DECAY`: Epsilon azalma oranı (0.995)

### 8. SARSA
- `SARSA_EPISODES`: Bölüm sayısı (5000)
- `SARSA_LEARNING_RATE`: Öğrenme oranı (0.1)
- `SARSA_DISCOUNT_FACTOR`: İndirim faktörü (0.95)
- `SARSA_EPSILON_START`: Başlangıç epsilon (1.0)
- `SARSA_EPSILON_END`: Bitiş epsilon (0.01)
- `SARSA_EPSILON_DECAY`: Epsilon azalma oranı (0.995)

## Kullanım

```python
from src.core.config import settings

# Ayarlara erişim
print(settings.DEFAULT_NODE_COUNT)  # 250
print(settings.GA_POPULATION_SIZE)  # 100

# Ortam değişkenleri ile override
# .env dosyası veya environment variable:
# DEFAULT_NODE_COUNT=300
# GA_POPULATION_SIZE=150
```

## Ortam Değişkenleri

Ayarlar `.env` dosyası veya ortam değişkenleri ile override edilebilir:

```bash
# .env dosyası örneği
DEFAULT_NODE_COUNT=300
GA_POPULATION_SIZE=150
ACO_N_ANTS=100
DEBUG=False
```

## Notlar

- Tüm ayarlar tip kontrolü ile korunur (Pydantic)
- `.env` dosyası otomatik olarak yüklenir
- Büyük/küçük harf duyarlıdır (`case_sensitive=True`)
- Varsayılan değerler kod içinde tanımlıdır

