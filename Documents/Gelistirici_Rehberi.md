# Geliştirici Rehberi (Developer Guide)

> Bu doküman, QoS Rotalama projesine kod yazacak tüm ekip üyeleri için standartları ve prosedürleri belirler.

---

## 1. Kurulum (Setup)

Proje **Python 3.9+** gerektirir. Tüm geliştiriciler aşağıdaki adımları uygulamalıdır.

### Ortamın Hazırlanması

```bash
# 1. Repoyu klonlayın
git clone <repo_url>
cd qos-routing-project

# 2. Sanal ortam oluşturun (ÖNEMLİ: Kütüphane çakışmalarını önler)
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

```bash
# 3. Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### Örnek `requirements.txt`

```txt
networkx>=3.1
matplotlib>=3.7
PyQt5>=5.15
numpy>=1.24
pandas>=2.0
scipy>=1.10
gym>=0.26  # RL için (opsiyonel, custom env yazılacaksa gerekmeyebilir)
```

---

## 🏗️ 2 Proje Yapısı

```
📁pyqt5-desktop/
├── main.py                 # Ana giriş noktası
├── requirements.txt        # Python bağımlılıkları
├── README.md              # Bu dosya
└── 📁src/
    ├──📁 core/
    │   └── config.py      # Konfigürasyon
    ├──📁 services/
    │   ├── graph_service.py    # Graf oluşturma
    │   └── metrics_service.py  # Metrik hesaplama
    ├──📁 algorithms/
    │   ├── genetic_algorithm.py
    │   ├── aco.py
    │   ├── pso.py
    │   ├── simulated_annealing.py
    │   ├── q_learning.py
    │   └── sarsa.py
    └──📁 ui/
        ├── main_window.py     # Ana pencere
        └──📁 components/
            ├── graph_widget.py    # Graf görselleştirme
            ├── control_panel.py   # Kontrol paneli
            └── results_panel.py   # Sonuç paneli
```
---

## 3. Git Stratejisi (Branching Model)

Ekip çalışmasında kodun karışmaması için **katı kurallar** uygulanacaktır.

### Branch Yapısı

| Branch | Açıklama |
|--------|----------|
| `main` | Sadece "Production Ready" (sunuma hazır) kod bulunur. **ASLA direkt push yapılmaz.** |
| `dev` | Geliştirme dalıdır. Tüm feature'lar burada birleşir. |
| `feat/*` | Feature branch'ler: Herkes kendi işini `dev`'den dal alarak yapar. |

### İsimlendirme Kuralları

| Tür | Format | Örnek |
|-----|--------|-------|
| Yeni özellik | `feat/isim-ozellik` | `feat/ahmet-genetic-crossover` |
| Hata düzeltme | `fix/isim-bug` | `fix/mehmet-ui-freeze` |

### İş Akışı

```bash
# 1. Dev dalına geç
git checkout dev

# 2. Güncel kodu al
git pull

# 3. Yeni feature dalı oluştur
git checkout -b feat/yeni-ozellik

# 4. Kodla -> Commit et -> Pushla
git add .
git commit -m "feat: açıklayıcı mesaj"
git push origin feat/yeni-ozellik
```

5. GitHub/GitLab üzerinden `dev` dalına **Pull Request (PR)** aç.
6. Backend Lead veya Algo Lead onaylayınca merge edilir.

---

## 4. Kodlama Standartları (Coding Guidelines)

| Kural | Standart | Örnek |
|-------|----------|-------|
| **Dil** | Python (PEP8 standartları) | - |
| **Değişken İsimleri** | `snake_case` | `best_route`, `calculate_delay` |
| **Class İsimleri** | `PascalCase` | `GeneticSolver`, `NetworkTopology` |

### Yorum Kuralları

- ✅ Her fonksiyonun başında ne işe yaradığı, parametreleri ve dönüş değeri yazılmalıdır (Docstring).
- ✅ Karmaşık matematiksel işlemlerin yanına formül referansı eklenmelidir.

### Örnek Fonksiyon

```python
def calculate_fitness(route, weights):
    """
    Bir rotanın uygunluk değerini hesaplar.
    
    Args:
        route (list): Düğüm ID'lerinden oluşan liste.
        weights (dict): {'wd': 0.5, 'wr': 0.3, 'wc': 0.2}
    
    Returns:
        float: Fitness skoru (Düşük olması daha iyi).
    """
    # Kod buraya...
    pass
```

---

## 5. Test Çalıştırma

> ⚠️ Kodunuzu göndermeden önce **mutlaka** test edin.

```bash
# Tüm testleri çalıştır
python -m unittest discover tests
```
