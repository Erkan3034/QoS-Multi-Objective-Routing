┌─────────────────────────────────────────────────────┐
│                    BAŞLANGIÇ                        │
│  • Graf yükle                                       │
│  • Feromon matrisi başlat (hepsi 1.0)               │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│              İTERASYON DÖNGÜSÜ                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ 1. α ve β parametrelerini adapte et            │ │
│  │ 2. Her karınca için:                           │ │
│  │    • Kaynak → Hedef yol inşa et                │ │
│  │    • Fitness hesapla                           │ │
│  │ 3. Global en iyiyi güncelle                    │ │
│  │ 4. Feromon güncelle (buharlaşma + deposit)     │ │
│  │ 5. Yakınsama/stagnasyon kontrolü               │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│                    SONUÇ                            │
│  • En iyi yol                                       │
│  • En iyi fitness                                   │
│  • Hesaplama süresi                                 │
└─────────────────────────────────────────────────────┘


>Erkan Turgut (26.12.2025)