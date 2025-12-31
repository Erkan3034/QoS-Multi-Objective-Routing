# Sunum Hazırlık Rehberi
## Mutlaka Bilinmesi Gerekenler & Olası Sorular

> Bu belge, proje sunumunda karşılaşabileceğiniz kritik soruları ve cevaplarını içerir.

---

## 📚 MUTLAKA BİLMENİZ GEREKENLER

### 1. QoS (Quality of Service) Nedir?
Ağ trafiğinin kalitesini ölçen ve garanti eden metriklerin bütünüdür. Bu projede 3 temel QoS metriği kullanılır:
- **Gecikme (Delay):** Paketin kaynaktan hedefe ulaşma süresi
- **Güvenilirlik (Reliability):** Bağlantının kesintisiz çalışma olasılığı
- **Kaynak Kullanımı (Resource):** Bant genişliği tüketimi

### 2. Çok Amaçlı Optimizasyon
Bu projede tek bir metrik değil, **3 metrik aynı anda** optimize edilir. Bu "Çok Amaçlı Optimizasyon" (Multi-Objective Optimization) problemidir. Çözüm: **Ağırlıklı Toplam (Weighted Sum)** yöntemi.

```
TotalCost = w₁×Delay + w₂×ReliabilityCost + w₃×ResourceCost
```

### 3. Meta-Sezgisel Algoritmalar
Klasik algoritmaların (Dijkstra gibi) yetersiz kaldığı NP-hard problemlerde kullanılan "iyi çözüm" bulan algoritmalar:
- **GA (Genetik Algoritma):** Evrim, seçilim, çaprazlama, mutasyon
- **ACO (Karınca Kolonisi):** Feromon takibi, sürü zekası
- **PSO (Parçacık Sürüsü):** Hız-pozisyon güncelleme
- **SA (Simulated Annealing):** Metalurji ilhamı, sıcaklık-soğutma

### 4. Pekiştirmeli Öğrenme (RL)
Ajan-ortam etkileşimiyle öğrenen sistem:
- **Q-Learning:** Model-free, off-policy, Q-table güncelleme
- **SARSA:** On-policy alternatif

---

## ❓ 10 KRİTİK SORU VE CEVAPLARI

---

### SORU 1: "Dijkstra varken neden meta-sezgisel algoritma kullanıyorsunuz?"

**CEVAP:**
Dijkstra **tek kriterli** (örn. sadece en kısa yol) problemlerde optimaldir. Ancak bu projede:

1. **3 farklı metrik** aynı anda optimize edilmeli (gecikme, güvenilirlik, kaynak)
2. **Bant genişliği kısıtı** var (kısıtlı optimizasyon)
3. Çok kriterli problemlerde **Pareto-optimal** çözümler gerekir

Meta-sezgisel algoritmalar bu karmaşık arama uzayında "yeterince iyi" çözümleri makul sürede bulabilir.

---

### SORU 2: "Fitness (Uygunluk) fonksiyonunuz nasıl çalışıyor?"

**CEVAP:**
```
Fitness = w_delay × (TotalDelay / MaxDelay) 
        + w_reliability × (ReliabilityCost / MaxReliabilityCost)
        + w_resource × (ResourceCost / MaxResourceCost)
```

- **Normalizasyon:** Her metrik 0-1 arasına normalize edilir (adil karşılaştırma için)
- **Ağırlıklar:** Kullanıcı belirler (w₁ + w₂ + w₃ = 1)
- **Hedef:** Fitness değeri **düşük** olan yol daha iyidir

---

### SORU 3: "Güvenilirlik logaritmik maliyet olarak nasıl hesaplanıyor?"

**CEVAP:**
Güvenilirlik olasılıksal (0 < r < 1) ve **çarpımsal**:
```
R_total = r₁ × r₂ × r₃ × ... (yoldaki tüm güvenilirlikler)
```

Maximizasyon problemini minimizasyona çevirmek için **negatif logaritma** kullanılır:
```
ReliabilityCost = -log(r₁) - log(r₂) - log(r₃) - ...
```

**Örnek:** r = 0.99 → -log(0.99) ≈ 0.0044 (düşük maliyet = iyi)
**Örnek:** r = 0.50 → -log(0.50) ≈ 0.693 (yüksek maliyet = kötü)

---

### SORU 4: "Genetik Algoritmanızda crossover nasıl yapılıyor?"

**CEVAP:**
**Common Node Crossover (Ortak Düğüm Çaprazlama):**

1. İki ebeveyn yolu al: `[1, 5, 8, 12, 20]` ve `[1, 3, 8, 15, 20]`
2. Ortak düğümü bul: `8` (kaynak/hedef hariç)
3. Bu noktadan kes ve birleştir:
   - Çocuk 1: `[1, 5, 8, 15, 20]`
   - Çocuk 2: `[1, 3, 8, 12, 20]`

**Neden bu yöntem?** Graf tabanlı problemlerde rastgele kesim geçersiz yol üretebilir. Ortak düğüm kenarların korunmasını sağlar.

---

### SORU 5: "Q-Learning'deki Q-Table boyutu ne kadar?"

**CEVAP:**
```
Q-Table boyutu = |Nodes| × |Nodes| = 250 × 250 = 62,500 hücre
```

- **Satır:** Mevcut düğüm (state)
- **Sütun:** Hedef düğüm (action = komşuya git)
- **Değer:** Q(s,a) = Bu durumda bu aksiyonun beklenen ödülü

**Alternatif neden yok?** 62,500 hücre bellek açısından çok küçük. 10,000+ düğümlü ağlarda Deep Q-Learning (DQN) gerekir.

---

### SORU 6: "Neden 5 tekrar yapıyorsunuz?"

**CEVAP:**
Meta-sezgisel algoritmalar **stokastik** (rastgele) çalışır:
- Her çalışmada farklı başlangıç noktası
- Farklı rastgele kararlar

**5 tekrar ile:**
1. **Ortalama (Mean):** Tipik performansı gösterir
2. **Standart Sapma (Std):** Tutarlılığı ölçer
3. **Min/Max:** En iyi ve en kötü durumu gösterir

Bu istatistiksel olarak **güvenilir** sonuçlar sağlar.

---

### SORU 7: "4 farklı ağırlık profili ne işe yarıyor?"

**CEVAP:**
Gerçek dünyada farklı uygulamalar farklı önceliklere sahiptir:

| Profil | Kullanım Senaryosu |
|--------|-------------------|
| **Gecikme Odaklı (0.7/0.2/0.1)** | Video konferans, gaming |
| **Güvenilirlik Odaklı (0.2/0.7/0.1)** | Finansal işlemler, sağlık |
| **Kaynak Odaklı (0.2/0.1/0.7)** | Büyük dosya transferi |
| **Dengeli (0.33/0.33/0.34)** | Genel amaçlı trafik |

Bu profiller algoritmaların **farklı koşullara adaptasyonunu** test eder.

---

### SORU 8: "Bant genişliği kısıtı nasıl kontrol ediliyor?"

**CEVAP:**
**Post-Processing (Sonradan Kontrol):**

1. Algoritma bir yol bulur: `[5, 8, 12, 20]`
2. `BandwidthConstraintChecker` yoldaki her kenarın BW'sini kontrol eder
3. **Darboğaz** (minimum BW) bulunur: min(500, 400, 600) = 400 Mbps
4. Gereksinim (örn. 500 Mbps) ile karşılaştırılır
5. 400 < 500 → **BAŞARISIZ** (Yetersiz Bant Genişliği)

**Neden algoritma içinde değil?** Esneklik. Aynı algoritma farklı BW gereksinimleriyle çalıştırılabilir.

---

### SORU 9: "Hangi algoritma en iyi?"

**CEVAP:**
**Duruma bağlı!** (Bu kritik bir cevap)

| Kriter | En İyi Algoritma |
|--------|-----------------|
| **En düşük maliyet** | Genellikle GA veya ACO |
| **En hızlı hesaplama** | SA veya Q-Learning |
| **En tutarlı sonuç (düşük std)** | ACO |
| **Küçük graf (<50 düğüm)** | Hepsi benzer |
| **Büyük graf (>200 düğüm)** | GA (paralel işlem) |

**Önemli:** "X her zaman en iyidir" demek yerine "X, Y koşulunda en iyidir" deyin.

---

### SORU 10: "Projenizin sınırlamaları (limitations) neler?"

**CEVAP:**
(Bu soru genellikle sorulur - dürüst cevap puan kazandırır)

1. **Statik Graf:** Gerçek zamanlı trafik değişikliği yok
2. **Tek Talep:** Aynı anda birden fazla akış yok (Multi-commodity flow)
3. **Merkezi Çözüm:** SDN gibi dağıtık mimari yok
4. **Simülasyon Verisi:** Gerçek router'dan alınan veri yok
5. **Q-Table Boyutu:** 250+ düğümde DQN gerekebilir

---

## 🧬 GENETİK ALGORİTMA (GA) SORULARI

---

### GA-1: "Genetik Algoritmada popülasyon büyüklüğü neden 50?"

**CEVAP:**
Popülasyon büyüklüğü (population_size = 50) bir **trade-off**:

| Küçük Popülasyon (<30) | Büyük Popülasyon (>100) |
|------------------------|-------------------------|
| Hızlı iterasyon | Yavaş iterasyon |
| Çeşitlilik eksikliği | Daha iyi keşif |
| Erken yakınsama riski | Daha fazla bellek |

**50** dengeli bir değer:
- 250 düğümlü grafta yeterli çeşitlilik
- Her iterasyon ~50-100ms
- Bellek: ~50 yol × ortalama 10 düğüm = 500 integer ≈ 4KB

---

### GA-2: "Elitizm nedir ve neden kullanıyorsunuz?"

**CEVAP:**
**Elitizm:** Her nesilde en iyi bireylerin doğrudan sonraki nesle aktarılması.

```python
elite_count = int(population_size * elite_rate)  # örn: 50 * 0.1 = 5 birey
```

**Neden gerekli?**
1. **En iyi çözüm korunur** - Crossover/mutasyon onu bozamaz
2. **Monoton iyileşme** - Fitness asla kötüleşmez
3. **Yakınsama hızlanır** - İyi genler kaybolmaz

**Dikkat:** Çok yüksek elite_rate (>0.3) → Çeşitlilik kaybı → Yerel minimuma takılma

---

### GA-3: "Turnuva seçimi (Tournament Selection) nasıl çalışıyor?"

**CEVAP:**
```python
def tournament_selection(population, tournament_size=3):
    # 1. Rastgele 3 birey seç
    candidates = random.sample(population, tournament_size)
    # 2. En iyi fitness'a sahip olanı döndür
    return min(candidates, key=lambda x: x.fitness)
```

**Neden Rulet Tekerleği değil?**
- Rulet: Fitness'a orantılı olasılık (büyük farklar dominant olur)
- Turnuva: Daha dengeli seçim baskısı
- **tournament_size** ile baskı ayarlanabilir (büyük = daha seçici)

---

### GA-4: "Mutasyon oranı (mutation_rate) neden 0.1?"

**CEVAP:**
**Mutasyon = Rastgele değişiklik = Keşif (Exploration)**

| Düşük (<0.05) | Yüksek (>0.3) |
|---------------|---------------|
| Yetersiz keşif | Rastgele aramaya dönüşür |
| Yerel optimuma takılır | İyi çözümler bozulur |

**0.1 (10%)** ideal çünkü:
- Her 10 genin 1'i değişir
- Yeni bölgeler keşfedilir
- Ama iyi çözümler çoğunlukla korunur

**Projede mutasyon:** Yolun ortasından rastgele bir segment yeniden oluşturulur.

---

### GA-5: "Geçersiz yollar (Invalid paths) nasıl engelleniyor?"

**CEVAP:**
Graf tabanlı problemlerde temel zorluk: **Crossover/Mutasyon geçersiz yol üretebilir**

**Çözümler:**

1. **Başlangıç popülasyonu:** Random Walk ile sadece geçerli yollar
2. **Crossover:** Ortak düğüm noktasından kesim (kenar bağlantısı korunur)
3. **Mutasyon:** Segment yeniden oluşturulurken BFS/DFS kullanılır
4. **Repair (Onarım):** Geçersiz yol tespit edilirse → rastgele geçerli yolla değiştir

```python
if not self._is_valid_path(child):
    child = self._random_walk(source, destination)
```

---

## 🐜 KARINCA KOLONİSİ (ACO) SORULARI

---

### ACO-1: "Feromon nedir ve nasıl çalışıyor?"

**CEVAP:**
**Feromon:** Karıncaların yol üzerine bıraktığı kimyasal iz. İlham: Gerçek karıncalar!

**Başlangıç:**
```python
pheromone[i][j] = 1.0  # Tüm kenarlar eşit feromon
```

**Güncelleme (her iterasyon sonunda):**
```python
# 1. Buharlaşma
pheromone[i][j] *= (1 - evaporation_rate)  # örn: 0.9 çarpanı

# 2. Biriktirme (iyi yollar için)
for edge in best_path:
    pheromone[edge] += Q / best_cost  # Q = sabit, best_cost = düşükse daha fazla
```

**Sonuç:** İyi yollarda feromon birikir → Daha fazla karınca o yolu seçer → Pozitif geri besleme

---

### ACO-2: "Evaporation rate (Buharlaşma oranı) neden önemli?"

**CEVAP:**
**evaporation_rate = 0.1** demek her iterasyonda feromon %10 azalır.

| Düşük (<0.05) | Yüksek (>0.3) |
|---------------|---------------|
| Eski yollar dominant | Feromon çok hızlı silinir |
| Yeni keşif zorlaşır | Öğrenme zayıflar |
| Yerel optimum riski | Yakınsama yavaşlar |

**0.1 ideal değer:**
- Eski bilgi yavaşça unutulur
- Yeni iyi yollar hâlâ öğrenilebilir
- Dinamik dengeleme sağlar

---

### ACO-3: "Karınca bir sonraki düğümü nasıl seçiyor?"

**CEVAP:**
**Olasılıksal Seçim Kuralı:**

```
P(i → j) = [τ(i,j)]^α × [η(i,j)]^β / Σ[...tüm komşular...]
```

| Parametre | Açıklama |
|-----------|----------|
| τ(i,j) | Kenar (i,j) üzerindeki feromon miktarı |
| η(i,j) | Sezgisel bilgi = 1 / kenar_maliyeti |
| α (alpha) | Feromon ağırlığı (sürü bilgisinin önemi) |
| β (beta) | Sezgisel ağırlık (açgözlü seçimin önemi) |

**Örnek (α=1, β=2):**
- Hem feromon hem sezgisel önemli
- Ama sezgisel (düşük maliyetli kenarlar) biraz daha baskın

---

### ACO-4: "Alpha ve Beta parametreleri ne anlama geliyor?"

**CEVAP:**

| α (alpha) | Etki |
|-----------|------|
| α = 0 | Feromon yok sayılır → Açgözlü (greedy) seçim |
| α = 1 | Feromon normal etkili |
| α > 2 | Feromon çok dominant → Erken yakınsama |

| β (beta) | Etki |
|----------|------|
| β = 0 | Sezgisel yok sayılır → Sadece feromona bak |
| β = 2 | Sezgisel güçlü → Düşük maliyetli kenarlar tercih |
| β > 3 | Çok açgözlü → Keşif azalır |

**Projede: α=1, β=2** → Dengeli ama sezgisele biraz ağırlık

---

### ACO-5: "ACO ile GA arasındaki temel fark nedir?"

**CEVAP:**

| Özellik | Genetik Algoritma (GA) | Karınca Kolonisi (ACO) |
|---------|------------------------|------------------------|
| **İlham** | Evrim teorisi | Karınca kolonisi davranışı |
| **Çözüm temsili** | Kromozom (yol listesi) | Feromon matrisi |
| **Öğrenme** | Nesiller arası | Feromon birikimi |
| **Keşif mekanizması** | Mutasyon, crossover | Olasılıksal seçim |
| **Bellek** | Popülasyon tutulur | Feromon matrisi tutulur |
| **Paralellik** | Bireyler bağımsız | Karıncalar bağımsız |
| **Yakınsama** | Genellikle daha hızlı | Daha tutarlı (düşük std) |

**Hangisi ne zaman?**
- **GA:** Çok modlu arama uzayı, paralel hesaplama imkanı
- **ACO:** Graf/rota problemleri, tutarlılık önemli

---

## 🎯 SUNUM İPUÇLARI

1. **Demo sırası:** Graf oluştur → Optimize Et → Toplu Deney → Sonuçları göster
2. **Karşılaştırma vurgula:** "X algoritması Y'den %Z daha iyi" gibi somut rakamlar
3. **Görselleştirme:** 3D graf geçişini göster
4. **Ranking:** "25 senaryonun 15'inde GA kazandı" gibi istatistik
5. **Kod değil sonuç:** Kod satırlarını okumak yerine çıktıları göster

---

> Hazırlayan: QoS Routing Proje Ekibi | 2025-12-31
