# 🖥️ QoS Multi-Objective Routing - Desktop Application

> **PyQt5 tabanlı yüksek performanslı masaüstü uygulaması**

Bu uygulama, web versiyonunun PyQt5 ile yeniden yazılmış halidir.
250+ düğümlü grafları kasma olmadan görselleştirir.

---

## 🚀 Kurulum

### 1. Virtual Environment Oluştur

```powershell
cd pyqt5-desktop
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
.\venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

### 2. Bağımlılıkları Yükle

```powershell
pip install -r requirements.txt
```

### 3. Uygulamayı Çalıştır

```powershell
python main.py
```

---

## 🎮 Kullanım

### Graf Oluşturma
1. Sol panelden düğüm sayısını (n) ayarlayın (varsayılan: 250)
2. Bağlantı olasılığını (p) ayarlayın (varsayılan: 0.4)
3. **"Graf Oluştur"** butonuna tıklayın

### Kaynak/Hedef Seçimi
- **Sol tıklama**: Kaynak düğümü seç
- **Shift + Sol tıklama**: Hedef düğümü seç
- Veya panelden manuel olarak girin

### Optimizasyon
1. Kaynak ve hedef düğümleri seçin
2. QoS ağırlıklarını ayarlayın (Gecikme, Güvenilirlik, Kaynak)
3. Algoritma seçin
4. **"Optimize Et"** veya **"Tümünü Karşılaştır"** butonuna tıklayın

---

## 📊 Algoritmalar

| Algoritma | Tür | Açıklama |
|-----------|-----|----------|
| Genetic Algorithm | Meta-Sezgisel | Evrimsel optimizasyon |
| Ant Colony (ACO) | Meta-Sezgisel | Feromon tabanlı |
| Particle Swarm (PSO) | Meta-Sezgisel | Sürü zekası |
| Simulated Annealing | Meta-Sezgisel | Sıcaklık bazlı |
| Q-Learning | RL | Off-policy öğrenme |
| SARSA | RL | On-policy öğrenme |

---

## ⌨️ Klavye Kısayolları

| Kısayol | İşlev |
|---------|-------|
| Tıklama | Kaynak seç |
| Shift+Tıklama | Hedef seç |
| Mouse tekerleği | Yakınlaştır/Uzaklaştır |
| Sürükle | Pan (kaydır) |

---

## 🏗️ Proje Yapısı

```
pyqt5-desktop/
├── main.py                 # Ana giriş noktası
├── requirements.txt        # Python bağımlılıkları
├── README.md              # Bu dosya
└── src/
    ├── core/
    │   └── config.py      # Konfigürasyon
    ├── services/
    │   ├── graph_service.py    # Graf oluşturma
    │   └── metrics_service.py  # Metrik hesaplama
    ├── algorithms/
    │   ├── genetic_algorithm.py
    │   ├── aco.py
    │   ├── pso.py
    │   ├── simulated_annealing.py
    │   ├── q_learning.py
    │   └── sarsa.py
    └── ui/
        ├── main_window.py     # Ana pencere
        └── components/
            ├── graph_widget.py    # Graf görselleştirme
            ├── control_panel.py   # Kontrol paneli
            └── results_panel.py   # Sonuç paneli
```

---

## 🔧 Sorun Giderme

### PyQt5 yüklenmiyor
```powershell
pip install --upgrade pip
pip install PyQt5 PyQt5-Qt5 PyQt5-sip
```

### pyqtgraph hatası
```powershell
pip install pyqtgraph numpy
```

### Graf çok yavaş render ediliyor
- Düğüm sayısını 200'ün altında tutun
- Veya `graph_widget.py` içinde `size` parametrelerini küçültün

---

## 📝 Notlar

- Bu uygulama web versiyonundan bağımsızdır
- Graf görselleştirme için PyQtGraph kullanılır (web'deki react-force-graph yerine)

---

*Created by [developer](https://github.com/Erkan3034)*

