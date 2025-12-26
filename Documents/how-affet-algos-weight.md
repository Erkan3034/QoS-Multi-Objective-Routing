# Ağırlıkların Algoritmalar ve Sonuçlar Üzerindeki Etkisi

Bu belge, Arayüzdeki **Gecikme (Delay)**, **Güvenilirlik (Reliability)** ve **Kaynak (Resource)** ağırlıklarının arka planda algoritmaları nasıl yönlendirdiğini ve sonuçları nasıl değiştirdiğini (veya neden bazen değiştirmediğini) açıklar.

## 1. Amaç Fonksiyonu (Objective Function)

Tüm algoritmalar (Genetic, ACO, PSO vb.), matematiksel olarak "Maliyet" (Cost) adını verdiğimiz tek bir sayıyı **minimize** etmeye çalışır. Bu sayı ne kadar küçükse, yol o kadar iyidir.

Formülümüz şu şekildedir:

```
Toplam Maliyet = (W_gecikme × Norm_Gecikme) + (W_güven × Norm_Güvenilirlik) + (W_kaynak × Norm_Kaynak)
```

Burada:
- **W (Weight):** Sizin arayüzden belirlediğiniz yüzdelik ağırlıklardır (Örn: %50 = 0.5).
- **Norm (Normalized):** Farklı birimlerin (ms, %, hop sayısı) matematiksel olarak toplanabilmesi için 0 ile 1 arasına sıkıştırılmış değerleridir.

## 2. Ağırlıklar Nasıl Etki Eder?

### Senaryo A: Dengeli Ağırlıklar (%33, %33, %33)
Algoritma; gecikmesi düşük, güvenilirliği yüksek ve hop sayısı az olan "dengeli" yolları arar.

### Senaryo B: Gecikme Odaklı (%80 Gecikme, %10 Güvenilirlik, %10 Kaynak)
Bu durumda algoritma için "Toplam Maliyet"in büyük bir kısmını **Gecikme** oluşturur.
- Algoritma, 10 hoplu ama çok hızlı (fiber optik gibi düşünün) bir yolu, 2 hoplu ama yavaş (eski bakır kablo gibi) bir yola tercih edebilir.
- Çünkü 10 hopun getirdiği "Kaynak Maliyeti" cezası (%10 etkili), hızdan kazandığı "Gecikme Ödülü"nün (%80 etkili) yanında önemsiz kalır.

### Senaryo C: Güvenilirlik Odaklı (%10 Gecikme, %80 Güvenilirlik, %10 Kaynak)
Algoritma, yolun ne kadar uzadığına veya ne kadar sürdüğüne bakmaksızın, en güvenli (kopma ihtimali en düşük) yolu seçmeye zorlanır.

## 3. Neden Bazen Sonuç Değişmiyor? (Pareto Optimality)

Ağırlıkları değiştirmenize rağmen sonucun (bulunan yolun) değişmemesinin iki temel nedeni vardır:

### A. "Tartışmasız En İyi" (Dominant) Yolun Varlığı
Bir yol düşünün ki:
1.  En kısa (1 hop)
2.  En düşük gecikmeli
3.  En yüksek güvenilirlikli

Bu yol, tüm kriterlerde rakiplerinden daha iyidir.
- Gecikmeye odaklansanız da bu yolu seçer.
- Güvenilirliğe odaklansanız da bu yolu seçer.
- Kaynağa odaklansanız da bu yolu seçer.

Matematiksel olarak bu yola **Dominant Çözüm** denir. Eğer grafiğinizde böyle bir "süper yol" varsa (ki doğrudan bağlantılar genelde böyledir), ağırlıkların bir etkisi olmaz.

### B. Alternatiflerin Yetersizliği
Bazen alternatif yollar o kadar kötüdür ki, ağırlıkları ne kadar değiştirirseniz değiştirin, algoritma onları seçmeye değer bulmaz.

**Örnek:**
- Yol 1: 10ms gecikme, %99 güvenilirlik (Maliyet: Düşük)
- Yol 2: 100ms gecikme, %50 güvenilirlik (Maliyet: Çok Yüksek)

Burada Gecikme ağırlığını %0 yapıp sadece Güvenilirlik (%100) yapsanız bile, Yol 1'in güvenilirliği (%99) Yol 2'den (%50) daha iyi olduğu için **yine Yol 1 seçilir.**

## 4. Geliştirici Notu: Nasıl Test Edilmeli?

Farklılıkları görmek için **birbirine zıt (trade-off) özelliklere sahip** yolların olduğu senaryolar gerekir.

Örneğin, graf üzerinde şöyle bir durum kurgularsanız (veya denk gelirse) farkı görebilirsiniz:
- **Yol A:** Çok Hızlı ama Güvensiz (Düşük Gecikme, Düşük Güvenilirlik)
- **Yol B:** Yavaş ama Çok Sağlam (Yüksek Gecikme, Yüksek Güvenilirlik)

Bu durumda:
- Ağırlıkları **Gecikme** lehine çekerseniz -> **Yol A** seçilir.
- Ağırlıkları **Güvenilirlik** lehine çekerseniz -> **Yol B** seçilir.

Eğer grafiğiniz çok yoğunsa (250 düğüm, 12.000 kenar), genellikle "Hem hızlı hem güvenli" yollar bulunabildiğinden (Dominant Yol), ağırlıkların etkisi azalır. Daha seyrek (sparse) graflarda ağırlıkların etkisi çok daha belirgindir.
