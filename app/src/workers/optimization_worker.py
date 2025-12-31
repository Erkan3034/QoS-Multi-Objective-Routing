"""
Optimizasyon Worker - Arka Plan İş Parçacığı
=============================================
Bu modül, UI'nin donmasını önlemek için optimizasyon algoritmalarını
ayrı bir thread'de (iş parçacığı) çalıştırır.

NEDEN QThread KULLANIYORUZ?
---------------------------
PyQt5 uygulamalarında ana thread (Main Thread) UI güncellemelerinden sorumludur.
Eğer uzun süren bir hesaplama (örn. GA 500 nesil) ana thread'de çalışırsa,
UI "Not Responding" durumuna geçer ve kullanıcı arayüzle etkileşemez.

QThread sayesinde:
1. Hesaplama arka planda çalışır
2. UI yanıt vermeye devam eder
3. İlerleme güncellemeleri (progress_data) gerçek zamanlı gösterilir
4. Yakınsama grafiği canlı çizilir

SİNYAL-SLOT MEKANİZMASI:
------------------------
- finished: Optimizasyon tamamlandığında sonucu iletir
- progress_data: Her iterasyonda (iteration, fitness) verisini iletir
- error: Hata durumunda hata mesajını iletir
"""

from PyQt5.QtCore import QThread, pyqtSignal
from typing import Dict, Any, Optional
import networkx as nx

from src.services.metrics_service import MetricsService
from src.ui.components.results_panel import OptimizationResult


class OptimizationWorker(QThread):
    """
    Genel Amaçlı Optimizasyon Worker'ı
    ===================================
    
    Bu sınıf, HERHANGİ bir optimizasyon algoritmasını arka planda çalıştırabilir.
    Algoritma türünden bağımsız çalışır (GA, ACO, PSO, SA, Q-Learning).
    
    KULLANIM:
    ---------
    ```python
    # 1. Algoritma örneğini oluştur
    ga = GeneticAlgorithm(graph)
    
    # 2. Worker'ı başlat
    worker = OptimizationWorker(ga, "Genetic Algorithm", graph, src, dst, weights)
    worker.finished.connect(self._on_result)      # Sonuç geldiğinde
    worker.progress_data.connect(self._on_progress)  # Her iterasyonda
    worker.error.connect(self._on_error)          # Hata durumunda
    worker.start()  # Arka plan thread'ini başlat
    ```
    
    SİNYALLER (Signals):
    --------------------
    finished(OptimizationResult): Optimizasyon tamamlandığında emit edilir
    progress_data(int, float): Her iterasyonda (iterasyon_no, fitness) emit edilir
    error(str): Hata durumunda hata mesajı emit edilir
    """
    
    # ==================== SINYAL TANIMLARI ====================
    # PyQt sinyalleri: Thread'ler arası güvenli iletişim sağlar
    
    finished = pyqtSignal(object)      # Optimizasyon sonucu (OptimizationResult)
    progress_data = pyqtSignal(int, float)  # (iterasyon, fitness) - canlı grafik için
    error = pyqtSignal(str)            # Hata mesajı
    
    def __init__(
        self,
        algorithm_instance: Any,    # Örn: GeneticAlgorithm(graph)
        algorithm_name: str,        # Örn: "Genetic Algorithm"
        graph: nx.Graph,            # NetworkX graf nesnesi
        source: int,                # Kaynak düğüm ID'si
        dest: int,                  # Hedef düğüm ID'si
        weights: Dict,              # {'delay': 0.33, 'reliability': 0.33, 'resource': 0.34}
        bandwidth_demand: float = 0.0  # Minimum bandwidth gereksinimi (Mbps)
    ):
        """
        Worker'ı Başlat
        ---------------
        
        Args:
            algorithm_instance: Hazır algoritma nesnesi (optimize() metodu olmalı)
            algorithm_name: UI'da gösterilecek algoritma adı
            graph: Üzerinde optimizasyon yapılacak graf
            source: Başlangıç düğümü
            dest: Hedef düğümü
            weights: QoS metrik ağırlıkları (toplam = 1.0)
            bandwidth_demand: Sert bandwidth kısıtı (0 = kısıt yok)
        """
        super().__init__()  # QThread.__init__() çağır
        
        # Parametreleri sakla (run() metodunda kullanılacak)
        self.algorithm_instance = algorithm_instance
        self.algorithm_name = algorithm_name
        self.graph = graph
        self.source = source
        self.dest = dest
        self.weights = weights
        self.bandwidth_demand = bandwidth_demand
    
    def run(self):
        """
        Arka Plan Optimizasyonu - Ana Çalışma Metodu
        ============================================
        
        Bu metod worker.start() çağrıldığında AYRI BİR THREAD'DE çalışır.
        Ana thread'i bloklamaz, bu sayede UI yanıt vermeye devam eder.
        
        ÇALIŞMA AKIŞI:
        1. İlerleme callback fonksiyonunu tanımla
        2. Algoritmayı çalıştır (optimize)
        3. Sonuç metriklerini hesapla
        4. OptimizationResult oluştur
        5. finished sinyali emit et
        
        HATA YÖNETİMİ:
        Herhangi bir hata oluşursa, error sinyali emit edilir
        ve UI uygun bir şekilde kullanıcıya bildirir.
        """
        try:
            # ==============================================================
            # ADIM 1: İlerleme Callback Fonksiyonu
            # ==============================================================
            # Bu fonksiyon algoritma tarafından her iterasyonda çağrılır.
            # Amacı: Canlı yakınsama grafiği güncellemesi için veri iletmek.
            #
            # Örnek: GA her nesilde, ACO her iterasyonda bunu çağırır.
            #
            def on_progress(iteration: int, fitness: float):
                """
                İlerleme verisini UI'a ilet.
                
                Args:
                    iteration: Mevcut iterasyon/nesil numarası
                    fitness: Bu iterasyondaki en iyi fitness değeri
                """
                # progress_data sinyali emit et → ConvergenceWidget güncellenir
                self.progress_data.emit(iteration, fitness)
            
            # ==============================================================
            # ADIM 2: Optimizasyonu Çalıştır
            # ==============================================================
            # Tüm algoritmalar aynı arayüzü kullanır:
            # result = algorithm.optimize(source, destination, weights, ...)
            #
            # progress_callback parametresi sayesinde canlı grafik çizilir.
            #
            result = self.algorithm_instance.optimize(
                source=self.source,
                destination=self.dest,
                weights=self.weights,
                bandwidth_demand=self.bandwidth_demand,
                progress_callback=on_progress  # Canlı grafik için callback
            )
            
            # ==============================================================
            # ADIM 3: Metrikleri Hesapla
            # ==============================================================
            # MetricsService: Bulunan yol için tüm QoS metriklerini hesaplar
            # - total_delay: Toplam gecikme (ms)
            # - total_reliability: Toplam güvenilirlik maliyeti
            # - resource_cost: Kaynak kullanım maliyeti
            # - min_bandwidth: Yoldaki en dar kenarın bandwidth'i
            # - weighted_cost: Ağırlıklı toplam maliyet
            #
            ms = MetricsService(self.graph)
            metrics = ms.calculate_all(
                result.path,
                self.weights['delay'],
                self.weights['reliability'],
                self.weights['resource']
            )
            
            # ==============================================================
            # ADIM 4: Bandwidth Kısıt Kontrolü
            # ==============================================================
            # Eğer kullanıcı bir bandwidth talebi belirttiyse (örn. 500 Mbps)
            # ve bulunan yoldaki minimum bandwidth bu talebi karşılamıyorsa,
            # yolu "geçersiz" olarak işaretle (cost = infinity).
            #
            # Bu SERT KISIT (hard constraint) yaklaşımıdır - ya karşılanır
            # ya da çözüm reddedilir.
            #
            if self.bandwidth_demand > 0 and metrics.min_bandwidth < self.bandwidth_demand:
                metrics.weighted_cost = float('inf')  # Geçersiz çözüm
            
            # ==============================================================
            # ADIM 5: Sonuç Nesnesini Oluştur
            # ==============================================================
            # OptimizationResult: UI'ın beklediği standart sonuç formatı
            # Bu nesne results_panel tarafından gösterilir.
            #
            opt_result = OptimizationResult(
                algorithm=self.algorithm_name,       # "Genetic Algorithm"
                path=result.path,                    # [1, 5, 8, 12, 20]
                total_delay=metrics.total_delay,     # 45.2 ms
                total_reliability=metrics.total_reliability,  # 0.0823 (log-cost)
                resource_cost=metrics.resource_cost,  # 2.34
                weighted_cost=metrics.weighted_cost,  # 0.234 (final score)
                computation_time_ms=result.computation_time_ms,  # 150.5 ms
                min_bandwidth=metrics.min_bandwidth,  # 450 Mbps
                seed_used=getattr(result, 'seed_used', None)  # Tekrarlanabilirlik için
            )
            
            # ==============================================================
            # ADIM 6: Sonucu UI'a İlet
            # ==============================================================
            # finished sinyali emit edildiğinde, main_window'daki
            # _on_optimization_finished() metodu tetiklenir ve
            # sonuç results_panel'de gösterilir.
            #
            self.finished.emit(opt_result)
            
        except Exception as e:
            # ==============================================================
            # HATA YÖNETİMİ
            # ==============================================================
            # Herhangi bir hata oluşursa (örn. yol bulunamadı, graf bağlantısız)
            # error sinyali emit edilir ve UI kullanıcıya uyarı gösterir.
            #
            self.error.emit(str(e))
