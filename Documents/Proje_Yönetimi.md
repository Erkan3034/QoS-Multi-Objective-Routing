# QoS Odaklı Rotalama Projesi
## İş Analizi ve Yönetim Planı

---

## 1. Proje Kimliği ve Hedefler

| Özellik | Değer |
|---------|-------|
| **Proje** | QoS Odaklı Çok Amaçlı Rotalama (Meta-Sezgisel ve RL Yaklaşımları) |
| **Ekip Büyüklüğü** | 9 Kişi |
| **Süre** | 5 Hafta |
| **Teslimat Türü** | Web arayüzü yazılımı + Rapor |

### Amaçlar (Goals)

| # | Amaç | Açıklama |
|---|------|----------|
| 1 | **Simülasyon Ortamı** | 250 düğümlü, %40 yoğunluklu (Erdős-Rényi) gerçekçi bir ağ topolojisi oluşturmak |
| 2 | **Algoritma Çeşitliliği** | Dijkstra (Referans), Genetik Algoritma (GA), Karınca Kolonisi (ACO) ve Q-Learning (RL) algoritmalarını entegre etmek |
| 3 | **Çok Amaçlı Optimizasyon** | Gecikme (Delay), Güvenilirlik (Reliability) ve Maliyet/Kullanım metriklerini aynı anda optimize eden Pareto-Optimal rotalar bulmak |
| 4 | **Performans** | Algoritmaların makul sürede (örn. <10sn) sonuç vermesini sağlamak |

### Başarı Kriterleri (Success Metrics)

| KPI | Kriter |
|-----|--------|
| **KPI 1** | Sistemin çökmeden 250 düğümlü grafiği görselleştirebilmesi |
| **KPI 2** | GA ve RL algoritmalarının, klasik Dijkstra'ya kıyasla %95+ doğrulukla (veya daha iyi çoklu kriter skoruyla) rota bulması |
| **KPI 3** | UI üzerinden tüm ağırlıkların (Wd, Wr, Wc) dinamik olarak değiştirilebilmesi |

---

## 2. Kapsam (Scope)

| Tür | Açıklama |
|-----|----------|
| ✅ **Dahil (In-Scope)** | Python tabanlı geliştirme, PyQt5 arayüzü, NetworkX kütüphanesi, Sentetik veri üretimi, Dokümantasyon |
| ❌ **Hariç (Out-Scope)** | Gerçek donanım router entegrasyonu, Web tabanlı arayüz (performans riski nedeniyle), Mobil uygulama |

---

## 3. 9 Kişilik Ekip Rol Dağılımı (Squad Yapısı)

Ekip **3 ana "Squad"a** bölünmüştür.

### Squad A: Core & Infrastructure (2 Kişi)

> **Sorumluluk:** Ağ topolojisi, veri yapıları, dosya okuma/yazma, ana mimari

| Rol | Görev |
|-----|-------|
| **Backend Lead** | Mimariden sorumlu, kod review yapar |
| **Data Engineer** | Topoloji üretimi ve metrik hesaplama motorunu yazar |

---

### Squad B: Algorithm & AI (4 Kişi - En Ağır Yük)

> **Sorumluluk:** GA, ACO ve RL algoritmalarının kodlanması

| Rol | Görev |
|-----|-------|
| **Algo Lead (GA Uzmanı)** | Genetik Algoritma implementasyonu |
| **AI Engineer (RL)** | Q-Learning ajanı ve ortam (env) tasarımı |
| **Optimization Eng (ACO)** | Karınca Kolonisi algoritması |
| **Math/Logic Dev** | Algoritmaların hiperparametre optimizasyonu ve Dijkstra entegrasyonu |

---

### Squad C: UI & Integration (3 Kişi)

> **Sorumluluk:** Arayüz, görselleştirme, test ve dokümantasyon

| Rol | Görev |
|-----|-------|
| **Frontend Lead (PyQt)** | GUI tasarımı ve thread yönetimi |
| **Vis Engineer** | Matplotlib/Graph görselleştirme entegrasyonu |
| **QA & Doc Specialist** | Test planları, hata raporlama ve proje raporu yazımı |

---

## 4. Haftalık İlerleme Planı (Timeline)

### 📅 Hafta 1: Altyapı ve Veri Modeli

> **Hedef:** Çalışan, görselleştirilebilir bir "boş" ağ yapısı

| Squad | Görevler |
|-------|----------|
| **Squad A** | GitHub reposunu kur. Erdős-Rényi (250 node) grafiğini NetworkX ile oluştur. JSON formatında kaydet/yükle yapısını yaz |
| **Squad B** | Literatür taraması yap. Q-Table yapısını ve GA kromozom yapısını kağıt üzerinde tasarla. Dijkstra'yı yaz |
| **Squad C** | PyQt5 ile boş bir pencere aç, Matplotlib canvas'ı içine göm ve statik bir grafiği ekrana çiz |

---

### 📅 Hafta 2: Meta-Sezgisel Algoritmalar (GA & ACO)

> **Hedef:** GA ve ACO'nun konsol üzerinde rota bulması

| Squad | Görevler |
|-------|----------|
| **Squad A** | Fitness (Uygunluk) fonksiyonunu kodla (Gecikme, Güvenilirlik formülleri) |
| **Squad B (GA)** | Başlangıç popülasyonu, Çaprazlama (Crossover), Mutasyon fonksiyonlarını yaz |
| **Squad B (ACO)** | Feromon matrisini oluştur, karınca gezinti mantığını kodla |
| **Squad C** | Arayüze "Kaynak", "Hedef" seçimi ve "Algoritma Seç" dropdown'larını ekle |

---

### 📅 Hafta 3: Pekiştirmeli Öğrenme (RL) ve Arayüz Bağlantısı

> **Hedef:** ⚠️ En zorlu hafta. RL ajanının eğitilmesi ve UI'ın donmadan çalışması

| Squad | Görevler |
|-------|----------|
| **Squad B (RL)** | OpenAI Gym mantığında `step()`, `reset()`, `reward()` fonksiyonlarını yaz. Eğitimi başlat |
| **Squad A** | Algoritmaların UI'ı dondurmaması için "Thread" (QThread) yapısını kur |
| **Squad C** | Algoritmadan gelen "yol" verisini (node listesi) grafikte farklı renkte (kırmızı) çizdirmeyi başar |

---

### 📅 Hafta 4: Entegrasyon ve Optimizasyon

> **Hedef:** Tüm algoritmaların UI üzerinden çalıştırılabilir olması

| Squad | Görevler |
|-------|----------|
| **Squad B** | Hiperparametre ayarı (Learning rate, Popülasyon sayısı vb.). Algoritmalar çok yavaşsa optimize et |
| **Squad C** | Ağırlık slider'larını (Gecikme vs. önemi) sisteme bağla. Anlık log ekranı ekle |
| **Squad A & QA** | Uç durumları dene (Bağlantısız node, Source=Target durumu). Hataları gider |

---

### 📅 Hafta 5: Test, Analiz ve Raporlama

> **Hedef:** Teslim edilebilir ürün ve rapor

| Sorumlu | Görevler |
|---------|----------|
| **QA & Squad C** | 20 farklı senaryo çalıştır. Sonuçları Excel/CSV'ye aktar |
| **Squad B** | Karşılaştırma tablolarını (Süre, Maliyet, Başarım) oluştur |
| **Tüm Ekip** | Kod temizliği (Refactoring), yorum satırları |
| **QA & Doc** | Final raporunu PDF yap, sunum dosyasını hazırla |

---