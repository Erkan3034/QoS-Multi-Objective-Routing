# Teknik Gereksinimler ve Mimari

> Bu belge, projenin matematiksel altyapısını, veri modellerini ve mimari kararlarını içerir.

---

## 1. Matematiksel Modeller ve Metrikler

Projede **3 temel Kalite Servisi (QoS)** metriği optimize edilecektir.

### 1.1. Ağ Modeli

Ağ, $G(V, E)$ şeklinde bir grafiktir.

| Sembol | Açıklama |
|--------|----------|
| $V$ | Düğümler kümesi (Routerlar). $\|V\| = 250$ |
| $E$ | Kenarlar kümesi (Linkler) |

### 1.2. Metrik Formülleri

#### 1. Toplam Gecikme (Total Delay - $D_{total}$)
> **Minimize edilmeli**

Bir yolun ($P$) toplam gecikmesi, üzerindeki linklerin gecikmesi ve düğümlerin işlem süresinin toplamıdır.

$$D_{total}(P) = \sum_{(i,j) \in P} d_{link}(i,j) + \sum_{n \in P} d_{proc}(n)$$

| Terim | Açıklama |
|-------|----------|
| $d_{link}$ | İletim gecikmesi (Transmission + Propagation) |
| $d_{proc}$ | Düğüm işlem gecikmesi |

---

#### 2. Toplam Güvenilirlik (Total Reliability - $R_{total}$)
> **Maksimize edilmeli**

Güvenilirlik olasılıksaldır ($0 < r < 1$). Çarpım işlemi toplama dönüştürülerek maliyet hesabına katılır.

$$R_{total}(P) = \prod_{(i,j) \in P} r_{link}(i,j) \times \prod_{n \in P} r_{node}(n)$$

**Optimizasyon için dönüştürme (Logaritmik Maliyet):**

$$Cost_{rel}(P) = \sum_{(i,j) \in P} -\ln(r_{link}(i,j))$$

> 💡 Bu sayede "En Yüksek Güvenilirlik" problemi "En Düşük Logaritmik Maliyet" problemine dönüşür.

---

#### 3. Kaynak Kullanımı / Maliyet ($C_{total}$)
> **Minimize edilmeli**

Bant genişliği kullanımı veya parasal maliyet.

$$C_{total}(P) = \sum_{(i,j) \in P} \frac{1}{Bandwidth(i,j)}$$

---

### 1.3. Amaç Fonksiyonu (Fitness Function)

Çok amaçlı optimizasyonu tek bir skora indirgemek için **Ağırlıklı Toplam (Weighted Sum)** yöntemi kullanılır. Değerler normalize edilmelidir.

$$F(P) = W_d \cdot \frac{D(P)}{D_{max}} + W_r \cdot \frac{Cost_{rel}(P)}{C_{rel\_max}} + W_c \cdot \frac{C(P)}{C_{max}}$$

> ⚠️ $W_d + W_r + W_c = 1$ (Kullanıcı arayüzden belirler)

---

## 2. Algoritma Tasarımları

### 2.1. Genetik Algoritma (GA)

| Bileşen | Açıklama |
|---------|----------|
| **Kromozom** | Bir rota (Düğüm ID listesi). Örn: `[1, 5, 12, 55, 250]` |
| **Başlangıç Popülasyonu** | Rastgele geçerli yollardan (Random Walk) oluşturulmuş 50-100 birey |
| **Fitness** | Yukarıdaki $F(P)$ fonksiyonu (küçük olan iyidir) |
| **Seçilim (Selection)** | Turnuva seçimi (Tournament Selection) |
| **Çaprazlama (Crossover)** | Tek noktalı kesim (Common Node Crossover). İki rotanın ortak bir düğümü bulunup oradan parçalar değiştirilir |
| **Mutasyon** | Rotanın içinden rastgele bir alt parça silinip yeniden rastgele oluşturulur |

---

### 2.2. Pekiştirmeli Öğrenme (RL - Q-Learning)

| Bileşen | Açıklama |
|---------|----------|
| **Durum (State)** | Mevcut düğüm (Current Node) |
| **Aksiyon (Action)** | Komşu düğüme gitmek (Next Node) |

**Ödül (Reward) Fonksiyonu:**

| Durum | Ödül |
|-------|------|
| Hedefe ulaştı | $+100$ |
| Çıkmaz sokak / Döngü | $-50$ |
| Her adım (Hop) | $-(W_d \cdot d_{link} + W_r \cdot cost_{rel})$ (Anlık maliyet cezası) |

**Q-Table:** $250 \times 250$ boyutunda matris.

> 💡 Büyük olduğu için Deep Q-Learning düşünülebilir ama proje süresi için Q-Table yeterlidir.

---

## 3. Sistem Mimarisi

Uygulama **MVC (Model-View-Controller)** desenine uygun geliştirilecektir.

```
┌─────────────────────────────────────────────────────────────┐
│                         VIEW (UI)                           │
│                       src/ui/                               │
│              Kullanıcı etkileşimi                           │
└─────────────────────────┬───────────────────────────────────┘
                          │ Signal/Slot
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      CONTROLLER                             │
│                    src/algorithms/                          │
│    Algoritmalar (UI'dan bağımsız)                           │
│    Girdi: Topology, Source, Target                          │
│    Çıktı: Path listesi                                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        MODEL                                │
│                      src/core/                              │
│    • Topology sınıfı: NetworkX grafını tutar                │
│    • Node ve Link sınıfları: Özellikleri tutar              │
└─────────────────────────────────────────────────────────────┘
```

> **Observer Pattern:** Controller bir adım ilerlediğinde View'a "sinyal" gönderir (PyQt Signal/Slot), View grafiği günceller.

---

## 4. API Sözleşmeleri (Internal Interface)

Tüm algoritmalar aşağıdaki şablon sınıftan türetilmelidir:

```python
class RoutingAlgorithm:
    def __init__(self, graph, weights):
        self.graph = graph
        self.weights = weights  # {'wd': 0.5, ...}

    def solve(self, source_id, target_id):
        """
        Returns:
            dict: {
                'path': [1, 5, 8, 20],
                'metrics': {'delay': 12, 'reliability': 0.99, 'cost': 50},
                'execution_time': 0.45
            }
        """
        raise NotImplementedError
```
