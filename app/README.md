# 🖥️ QoS Multi-Objective Routing - Desktop Application

PyQt5 tabanlı masaüstü uygulaması. 250+ düğümlü grafları optimize eder ve görselleştirir.

## 🚀 Kurulum

```bash
# Virtual environment oluştur
python -m venv venv

# Aktif et (Windows)
.\venv\Scripts\Activate.ps1

# Bağımlılıkları yükle
pip install -r requirements.txt

# Çalıştır
python main.py
```

## 🎮 Kullanım

### Graf Yükleme
- **CSV'den Yükle**: "Proje Verisini Yükle (CSV)" butonuna tıklayın (graph_data klasöründen otomatik yükler)
- **Rastgele Oluştur**: Düğüm sayısı ve bağlantı olasılığını ayarlayıp "Graf Oluştur" butonuna tıklayın

### Optimizasyon
1. Kaynak ve hedef düğümleri seçin (graf üzerinde tıklayarak veya panelden)
2. QoS ağırlıklarını ayarlayın (Gecikme, Güvenilirlik, Kaynak)
3. Algoritma seçin
4. "Optimize Et" veya "Tüm Algoritmaları Karşılaştır" butonuna tıklayın

### Talep Çiftleri
CSV yüklendiğinde, talep çiftleri otomatik olarak ComboBox'ta görünür. Seçtiğinizde kaynak/hedef otomatik ayarlanır.

## 📊 Algoritmalar

| Algoritma | Tür |
|-----------|-----|
| Genetic Algorithm | Meta-Sezgisel |
| Ant Colony (ACO) | Meta-Sezgisel |
| Particle Swarm (PSO) | Meta-Sezgisel |
| Simulated Annealing | Meta-Sezgisel |
| Q-Learning | Reinforcement Learning |
| SARSA | Reinforcement Learning |

## 🏗️ Proje Yapısı

```
app/
├── main.py                 # Ana giriş noktası
├── requirements.txt        # Bağımlılıklar
└── src/
    ├── core/
    │   └── config.py      # Konfigürasyon (pydantic-settings)
    ├── services/
    │   ├── graph_service.py    # Graf oluşturma ve CSV yükleme
    │   └── metrics_service.py  # Metrik hesaplama
    ├── algorithms/         # 6 optimizasyon algoritması
    ├── experiments/        # Deney framework'ü
    └── ui/
        ├── main_window.py
        └── components/     # UI bileşenleri
```

## 🔧 Sorun Giderme

**PyQt5 yüklenmiyor:**
```bash
pip install --upgrade pip
pip install PyQt5 PyQt5-Qt5 PyQt5-sip
```

**CSV dosyaları bulunamıyor:**
- `graph_data` klasörünün proje kökünde (QoS-guncel ile aynı dizinde) olduğundan emin olun
- Veya manuel olarak klasör seçin

## 📝 Notlar

- Graf görselleştirme için PyQtGraph kullanılır
- CSV dosyaları Türkçe format (virgül) destekler
- Tüm algoritma parametreleri `src/core/config.py` dosyasından ayarlanabilir
