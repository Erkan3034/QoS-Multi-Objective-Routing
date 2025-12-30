
```text
┌─────────────────────────────────────────────────────┐
│                    BAŞLANGIÇ                        │
│  • Graf yükle                                       │
│  • Parametreleri ayarla (population, mutation...)   │
│  • Başlangıç popülasyonu oluştur                    │
│    ├── Shortest paths (hop, delay, reliability)     │
│    ├── Guided paths (hub-yönelimli)                 │
│    └── Random walks (keşif için)                    │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│              EVRİM DÖNGÜSÜ (Nesiller)               │
│  ┌────────────────────────────────────────────────┐ │
│  │ 1. FITNESS HESAPLA                             │ │
│  │    • Her yol için: delay + reliability + BW    │ │
│  │    • Paralel/seri işleme (graf boyutuna göre)  │ │
│  ├────────────────────────────────────────────────┤ │
│  │ 2. SEÇİLİM (Tournament Selection)              │ │
│  │    • K birey seç → En iyi ikisi ebeveyn olur   │ │
│  │    • Elitizm: En iyi %10 direkt aktarılır      │ │
│  ├────────────────────────────────────────────────┤ │
│  │ 3. ÇAPRAZLAMA (Edge-based Crossover)           │ │
│  │    • İki ebeveyn → Ortak düğümde kes           │ │
│  │    • Parçaları değiştir → 2 çocuk üret         │ │
│  ├────────────────────────────────────────────────┤ │
│  │ 4. MUTASYON (Diversity'e göre strateji)        │ │
│  │    • Düşük diversity → Segment replacement     │ │
│  │    • Orta diversity → Node insertion           │ │
│  │    • Yüksek diversity → Node replacement       │ │
│  ├────────────────────────────────────────────────┤ │
│  │ 5. YAKINSAMADI KONTROLÜ                        │ │
│  │    • Stagnasyon > 20 nesil? → DUR              │ │
│  │    • Değişim < 0.001? → DUR                    │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│                    SONUÇ                            │
│  • En iyi yol (path)                                │
│  • En iyi fitness değeri                            │
│  • Hangi nesilde bulundu                            │
│  • Hesaplama süresi (ms)                            │
│  • Yakınsama geçmişi (grafik için)                  │
└─────────────────────────────────────────────────────┘


        ┌─────────────────────────────────────┐
        │       GENETİK OPERATÖRLER           │
        └─────────────────────────────────────┘

  ╔═══════════════════════════════════════════════════╗
  ║ SEÇİLİM (Tournament Selection)                    ║
  ╠═══════════════════════════════════════════════════╣
  ║  Popülasyon: [A, B, C, D, E, F, G, H]             ║
  ║       ↓                                           ║
  ║  Rastgele K=5 seç: [B, D, F, G, H]                ║
  ║       ↓                                           ║
  ║  En iyi fitness'a sahip olan seçilir: [D]         ║
  ╚═══════════════════════════════════════════════════╝

  ╔═══════════════════════════════════════════════════╗
  ║ ÇAPRAZLAMA (Edge-based Crossover)                 ║
  ╠═══════════════════════════════════════════════════╣
  ║  Ebeveyn 1: [1, 3, 5, 7, 9]                       ║
  ║  Ebeveyn 2: [1, 4, 5, 8, 9]                       ║
  ║                  ▲                                ║
  ║            Ortak: 5                               ║
  ║                  ▼                                ║
  ║  Çocuk 1: [1, 3, 5, 8, 9]  (P1 başı + P2 sonu)    ║
  ║  Çocuk 2: [1, 4, 5, 7, 9]  (P2 başı + P1 sonu)    ║
  ╚═══════════════════════════════════════════════════╝

  ╔═══════════════════════════════════════════════════╗
  ║ MUTASYON TİPLERİ                                  ║
  ╠═══════════════════════════════════════════════════╣
  ║ 1. Node Replacement (Düğüm Değiştir)              ║
  ║    [1, 3, 5, 7, 9] → [1, 3, 6, 7, 9]              ║
  ║                  ▲                                ║
  ║                                                   ║
  ║ 2. Node Insertion (Düğüm Ekle)                    ║
  ║    [1, 3, 5, 7, 9] → [1, 3, 4, 5, 7, 9]           ║
  ║               ▲                                   ║
  ║                                                   ║
  ║ 3. Segment Replacement (Kesit Değiştir)           ║
  ║    [1, 3, 5, 7, 9] → [1, 3, 8, 6, 7, 9]           ║
  ║          ▲▲▲▲▲                                    ║
  ╚═══════════════════════════════════════════════════╝

```    
  
<br>

>Erkan Turgut (29.12.2025)