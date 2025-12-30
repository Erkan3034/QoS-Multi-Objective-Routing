# Toplu Deney (25 Test) Çalışma Prensipleri Raporu

Bu rapor, QoS Çok Amaçlı Yönlendirme uygulamasındaki "Toplu Deney" özelliğinin teknik işleyişini ve arka planda koşan süreçleri detaylandırmaktadır.

## 1. Genel Bakış
Toplu Deney, sistemdeki tüm yönlendirme algoritmalarının (GA, ACO, PSO, SA, QL, SARSA) standartlaştırılmış bir test seti üzerinde performansını ölçmek ve birbirleriyle kıyaslamak için tasarlanmıştır. Tek bir rota bulma işleminden farklı olarak, istatistiksel anlamlılık sağlamak için çoklu senaryolar ve tekrarlar kullanır.

## 2. Test Senaryolarının Oluşturulması
Deney başlatıldığında, `TestCaseGenerator` sınıfı otomatik olarak 25 adet test senaryosu üretir:
- **Düğümler**: Her senaryo için mevcut graf üzerinden rastgele bir kaynak ve hedef düğüm seçilir.
- **Bant Genişliği (QoS)**: Her test için 100 Mbps ile 1000 Mbps arasında (100'lük adımlarla) rastgele bir bant genişliği gereksinimi atanır.
- **Ağırlıklar**: Tüm testlerde algoritmaların odak noktası sabit tutulur (Gecikme: %33, Güvenilirlik: %33, Kaynak Kullanımı: %34).

## 3. Yürütme Süreci (Execution Flow)
Deney süreci, kullanıcı arayüzünün donmasını engellemek için ayrı bir iş parçacığında (`ExperimentsWorker`) yürütülür:

### A. Tekrarlı Çalıştırma (Stochastic Nature)
Meta-sezgisel algoritmalar (Karınca Kolonisi, Genetik Algoritma vb.) doğası gereği her çalışmada farklı sonuçlar üretebilir. Bu yüzden:
- Her algoritma, her bir test senaryosu için kullanıcı tarafından belirlenen **tekrar sayısı** kadar (varsayılan x5) çalıştırılır.
- Toplamda 25 (senaryo) × 6 (algoritma) × 5 (tekrar) = **750 bireysel optimizasyon** işlemi gerçekleştirilir.

### B. Kısıt Kontrolleri
Her rota bulma denemesinden sonra `BandwidthConstraintChecker` devreye girer:
- Bulunan yolun tüm bağlantılarındaki bant genişliği kontrol edilir.
- Eğer yol gereksinimi karşılamıyorsa veya yol bulunamadıysa, o deneme "Başarısız" olarak işaretlenir ve hata nedenleri (Yetersiz Bant Genişliği vb.) kaydedilir.

## 4. Veri toplama ve Analiz
Tüm işlemler tamamlandığında `ExperimentRunner` verileri şu şekilde agregat eder:

- **Başarı Oranı (Success Rate)**: Bant genişliği kısıtını sağlayan ve hedefe ulaşan denemelerin toplam denemelere oranı.
- **Ortalama Maliyet (Overall Avg Cost)**: Sadece başarılı denemelerin ağırlıklı maliyetlerinin ortalaması.
- **Hesaplama Süresi (Avg Time)**: Algoritmanın bir rotayı bulması için geçen ortalama milisaniye (ms).
- **En İyi Tohum (Best Seed)**: O algoritmanın en iyi sonucu bulduğu "Rastgelelik Tohumu" kaydedilir, böylece o başarılı sonuç tekrar üretilebilir.

## 5. Raporlama ve Görselleştirme
Sonuçlar toplandıktan sonra sistem:
1. Algoritmaları **ortalama maliyete göre** (en düşük maliyetli en üstte olacak şekilde) sıralar.
2. Bir özet tablo (`comparison_table`) oluşturur.
3. Varsa tüm başarısızlık detaylarını içeren bir "Hata Raporu" hazırlar.
4. Bu verileri kullanıcıya sunmak üzere `TestResultsDialog` penceresini açar.

---
*Bu sistem, ağ planlamacılarının kendi ağ yapıları için en verimli ve hızlı algoritmayı bilimsel verilerle seçmesine olanak tanır.*
