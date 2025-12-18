```bash
# 📚 PyQt5 Desktop - Geliştirici Rehberi
# Proje: BSM307 - QoS Multi-Objective Routing Desktop Application
# Amaç: Ekibin projeyi aynı düzenle geliştirmesi için rehber

────────────────────────────────────────────────────────
## 📁 PROJE YAPISI
────────────────────────────────────────────────────────
app
├── main.py
├── requirements.txt
├── README.md
├── DEVELOPMENT_GUIDE.md
├── PERFORMANCE_OPTIMIZATION.md
├── UI_TODO.md
└── src/
    ├── core/
    │   └── config.py
    ├── services/
    │   ├── graph_service.py
    │   └── metrics_service.py
    ├── algorithms/
    │   ├── genetic_algorithm.py
    │   ├── aco.py
    │   ├── pso.py
    │   ├── simulated_annealing.py
    │   ├── q_learning.py
    │   └── sarsa.py
    ├── experiments/
    │   ├── test_cases.py
    │   └── experiment_runner.py
    └── ui/
        ├── main_window.py
        └── components/
            ├── graph_widget.py
            ├── control_panel.py
            └── results_panel.py

────────────────────────────────────────────────────────
## 🔄 GELİŞTİRME AŞAMALARI
────────────────────────────────────────────────────────

AŞAMA 1: CORE
- config.py oluştur
- requirements.txt ekle
Commit:
feat: temel core yapısı oluşturuldu

AŞAMA 2: SERVICES
- graph_service.py
- metrics_service.py
Commit:
feat: servis modülleri tamamlandı

AŞAMA 3: META-OPTİMİZASYON ALGORİTMALARI
- genetic_algorithm.py
- aco.py
- pso.py
- simulated_annealing.py
Commit:
feat: meta-heuristic algoritmalar eklendi

AŞAMA 4: RL ALGORİTMALARI
- q_learning.py
- sarsa.py
Commit:
feat: RL modülleri eklendi

AŞAMA 5: EXPERIMENTS MODÜLÜ
- test_cases.py
- experiment_runner.py
Commit:
feat: deney modülü eklendi

AŞAMA 6: UI GELİŞTİRME
- main_window.py + components/
Commit:
feat: UI bileşenleri eklendi

AŞAMA 7: ENTEGRASYON
- main.py
Commit:
feat: UI + backend entegre edildi

────────────────────────────────────────────────────────
## 🔀 GIT WORKFLOW
────────────────────────────────────────────────────────

BRANCH MODELİ:
main
└── develop
    ├── feature/core
    ├── feature/services
    ├── feature/algorithms-meta
    ├── feature/algorithms-rl
    ├── feature/experiments
    ├── feature/ui
    └── feature/integration

BRANCH KURALLARI:
branch ismi → feature/isim

COMMIT FORMAT:
<tip>: <açıklama>

tipler:
feat = özellik
fix = hata düzeltme
docs = dokümantasyon
refactor = yeniden yapı
test = test modülü

ÖRNEK:
git commit -m "feat: q-learning eklendi"


────────────────────────────────────────────────────────
## 🧪 TEST STRATEJİSİ
────────────────────────────────────────────────────────

Birinci katman → Unit Test
İkinci katman → Integration Test

Test Dosya Yapısı:
tests/
├── test_config.py
├── test_graph_service.py
├── test_metrics_service.py
├── test_genetic_algorithm.py
├── test_aco.py
├── test_pso.py
├── test_q_learning.py
└── test_sarsa.py

────────────────────────────────────────────────────────
## ✨ YENİ ÖZELLİK EKLEME
────────────────────────────────────────────────────────
1) feature branch aç:
``bash
git checkout -b feature/<ozellik>
``
2) kodu yaz:
src/... içinde doğru klasöre

3) test yaz:
tests/... içine test ekle

4) commit:
git add .
git commit -m "feat: <özellik> eklendi"

5) push:
git push origin feature/<ozellik>

6) PR aç:
base: develop → compare: feature branch

────────────────────────────────────────────────────────
## 🔧 PROJEYİ KURMA
────────────────────────────────────────────────────────
git clone https://github.com/Erkan3034/QoS-Multi-Objective-Routing.git
cd app
pip install -r requirements.txt
python main.py

────────────────────────────────────────────────────────
## 📌 KOD STANDARTLARI
────────────────────────────────────────────────────────
- Fonksiyonlar kısa olmalı
- Global state kullanılmayacak
- magic number yok
- import sırası:
  standard → third party → local
- UI logic backend içinde olmayacak

────────────────────────────────────────────────────────
## 🧱 DOSYA LAW & ORDER
────────────────────────────────────────────────────────
src/core → ayarlar + konfigürasyon
src/services → graf + metrik işleme
src/algorithms → tüm algoritmalar
src/experiments → toplu testler
src/ui → arayüz

────────────────────────────────────────────────────────
## ✔ GÜVENLİK NOTLARI
────────────────────────────────────────────────────────
- main branch’a push yasak
- PR review zorunlu
- kod test edilmeden PR yok
- dokümantasyonsuz kod yok

────────────────────────────────────────────────────────
## 📌 FINAL TALİMATLAR
────────────────────────────────────────────────────────
- commitler küçük parçalı yapılacak
- branch isimleri açıklayıcı olacak
- repository içi dosya yapısı korunacak
- PR açıklaması detaylı olacak

```
