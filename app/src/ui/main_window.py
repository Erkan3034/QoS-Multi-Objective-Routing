"""
Ana Pencere - QoS Routing Desktop Application
"""
import sys
import os
import random
import statistics
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QStatusBar, QApplication, QTabWidget, QSplitter,
    QScrollArea, QFrame, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from typing import Dict, List, Optional

# __file__ = app/src/ui/main_window.py
# app klasörünü bul (3 seviye yukarı: ui -> src -> app)
APP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# app ile aynı dizindeki graph_data klasörünü bul
PROJECT_ROOT = os.path.dirname(APP_DIR)
GRAPH_DATA_DIR = os.path.join(PROJECT_ROOT, "graph_data")

from src.ui.components.graph_widget import GraphWidget
from src.ui.components.control_panel import ControlPanel
from src.ui.components.results_panel import ResultsPanel, OptimizationResult
from src.ui.components.header_widget import HeaderWidget
from src.ui.components.footer_widget import FooterWidget
from src.ui.components.experiments_panel import ExperimentsPanel
from src.ui.components.legend_widget import LegendWidget
from src.ui.components.path_info_widget import PathInfoWidget
from src.ui.components.test_results_dialog import TestResultsDialog
from src.ui.components.scalability_dialog import ScalabilityDialog
from src.ui.components.scenarios_dialog import ScenariosDialog

from src.services.graph_service import GraphService
from src.services.metrics_service import MetricsService
from src.algorithms import ALGORITHMS
from src.workers.optimization_worker import OptimizationWorker as GenericOptimizationWorker

class GraphGenerationWorker(QThread):
    """Graf oluşturma thread'i."""
    
    finished = pyqtSignal(object, dict, dict) # graph, positions, info
    error = pyqtSignal(str)
    
    def __init__(self, service, n_nodes, prob):
        super().__init__()
        self.service = service
        self.n_nodes = n_nodes
        self.prob = prob
        
    def run(self):
        try:
            graph = self.service.generate_graph(n_nodes=self.n_nodes, p=self.prob)
            positions = self.service.get_node_positions()
            info = self.service.get_graph_info()
            self.finished.emit(graph, positions, info)
        except Exception as e:
            self.error.emit(str(e))

# [DEPRECATED] Old OptimizationWorker - kept for backward compatibility
# New code should use GenericOptimizationWorker from src.workers.optimization_worker
class OptimizationWorker(QThread):
    """Arka plan optimizasyon thread'i (Legacy - for backward compatibility)."""
    
    finished = pyqtSignal(object)  # result
    error = pyqtSignal(str)
    
    def __init__(self, graph, algorithm_key, source, dest, weights):
        super().__init__()
        self.graph = graph
        self.algorithm_key = algorithm_key
        self.source = source
        self.dest = dest
        self.weights = weights
    
    def run(self):
        try:
            name, AlgoClass = ALGORITHMS[self.algorithm_key]
            algo = AlgoClass(graph=self.graph)
            result = algo.optimize(
                source=self.source,
                destination=self.dest,
                weights=self.weights
            )
            
            ms = MetricsService(self.graph)
            metrics = ms.calculate_all(
                result.path,
                self.weights['delay'],
                self.weights['reliability'],
                self.weights['resource']
            )
            
            opt_result = OptimizationResult(
                algorithm=name,
                path=result.path,
                total_delay=metrics.total_delay,
                total_reliability=metrics.total_reliability,
                resource_cost=metrics.resource_cost,
                weighted_cost=metrics.weighted_cost,
                computation_time_ms=result.computation_time_ms,
                seed_used=getattr(result, 'seed_used', None)
            )
            
            self.finished.emit(opt_result)
            
        except Exception as e:
            self.error.emit(str(e))

class ComparisonWorker(QThread):
    """Tüm algoritmaları karşılaştırma thread'i."""
    
    finished = pyqtSignal(list)  # results
    progress = pyqtSignal(int, int)  # current, total
    error = pyqtSignal(str)
    
    def __init__(self, graph, source, dest, weights, target_algorithms: Optional[List[str]] = None):
        super().__init__()
        self.graph = graph
        self.source = source
        self.dest = dest
        self.weights = weights
        self.target_algorithms = target_algorithms
    
    def run(self):
        try:
            results = []
            
            # Filter algorithms if specific targets requested
            if self.target_algorithms:
                algo_items = {k: v for k, v in ALGORITHMS.items() if k in self.target_algorithms}
            else:
                algo_items = ALGORITHMS
                
            total = len(algo_items)
            
            for i, (key, (name, AlgoClass)) in enumerate(algo_items.items()):
                self.progress.emit(i + 1, total)
                try:
                    algo = AlgoClass(graph=self.graph)
                    result = algo.optimize(
                        source=self.source,
                        destination=self.dest,
                        weights=self.weights
                    )
                    
                    ms = MetricsService(self.graph)
                    metrics = ms.calculate_all(
                        result.path,
                        self.weights['delay'],
                        self.weights['reliability'],
                        self.weights['resource']
                    )
                    
                    results.append(OptimizationResult(
                        algorithm=name,
                        path=result.path,
                        total_delay=metrics.total_delay,
                        total_reliability=metrics.total_reliability,
                        resource_cost=metrics.resource_cost,
                        weighted_cost=metrics.weighted_cost,
                        computation_time_ms=result.computation_time_ms,
                        seed_used=getattr(result, 'seed_used', None)
                    ))
                except Exception as e:
                    print(f"Error in {name}: {e}")
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

class ExperimentsWorker(QThread):
    """Toplu deney çalıştırma thread'i."""
    
    finished = pyqtSignal(dict)  # result dict
    progress = pyqtSignal(int, int, str) # current, total, message
    error = pyqtSignal(str)
    
    def __init__(self, graph, n_tests, n_repeats):
        super().__init__()
        self.graph = graph
        self.n_tests = n_tests
        self.n_repeats = n_repeats
        self.results = []
        
    def run(self):
        try:
            from src.experiments.experiment_runner import ExperimentRunner
            from src.experiments.test_cases import TestCaseGenerator
            
            # Test case'leri üret
            generator = TestCaseGenerator(self.graph)
            if self.n_tests == 25:
                # Önceden tanımlı 25 test case
                test_cases = generator.get_predefined_test_cases()
            else:
                # Rastgele test case'ler
                test_cases = generator.generate_test_cases(n_cases=self.n_tests)
            
            # Progress callback
            def progress_callback(current, total, message):
                self.progress.emit(current, total, message)
            
            # Experiment runner oluştur
            runner = ExperimentRunner(
                graph=self.graph,
                n_repeats=self.n_repeats,
                progress_callback=progress_callback
            )
            
            # Deneyleri çalıştır
            result = runner.run_experiments(test_cases)
            
            # Sonucu dictionary olarak gönder
            self.finished.emit(result)
            
        except Exception as e:
            import traceback
            error_msg = f"Deney hatası: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)

class ScalabilityWorker(QThread):
    """Ölçeklenebilirlik analizi thread'i."""
    
    finished = pyqtSignal(list)
    progress = pyqtSignal(int, int, str)
    error = pyqtSignal(str)
    
    def __init__(self, node_counts):
        super().__init__()
        self.node_counts = node_counts
        
    def run(self):
        results = []
        try:
            from src.services.graph_service import GraphService
            from src.experiments.experiment_runner import ExperimentRunner
            from src.experiments.test_cases import TestCaseGenerator
            
            total_steps = len(self.node_counts)
            
            for i, n_nodes in enumerate(self.node_counts):
                self.progress.emit(i+1, total_steps, f"{n_nodes} düğüm analiz ediliyor...")
                
                # Rastgele graf oluştur
                service = GraphService(seed=None) 
                graph = service.generate_graph(n_nodes=n_nodes, p=0.15)
                
                # Test case üret (10 tane yeterli)
                generator = TestCaseGenerator(graph)
                test_cases = generator.generate_test_cases(n_cases=10)
                
                # Deneyleri çalıştır (3 tekrar)
                runner = ExperimentRunner(graph, n_repeats=3)
                res = runner.run_experiments(test_cases)
                
                # Sonuçları işle
                comp_table = res['comparison_table']
                row = {'nodes': n_nodes}
                for item in comp_table:
                    alg = item['algorithm']
                    row[alg] = {
                        'cost': item['overall_avg_cost'],
                        'time': item['overall_avg_time_ms']
                    }
                results.append(row)
                
            self.finished.emit(results)
            
        except Exception as e:
            import traceback
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")



class MainWindow(QMainWindow):
    """Ana uygulama penceresi."""
    
    def __init__(self):
        super().__init__()
        self.graph_service: Optional[GraphService] = None
        self.current_worker: Optional[QThread] = None
        self.current_result: Optional[OptimizationResult] = None
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """UI kurulumu."""
        self.setWindowTitle("QoS Multi-Objective Routing")
        self.setMinimumSize(1280, 800)
        # Determine path to background image
        import os
        # __file__ is app/src/ui/main_window.py
        bg_path = os.path.join(os.path.dirname(__file__), "resources", "images", "graph_bg.png")
        bg_path = os.path.abspath(bg_path).replace("\\", "/")
        
        self.setStyleSheet(f"""
            QMainWindow {{
                border-image: url("{bg_path}") 0 0 0 0 stretch stretch;
            }}
            QWidget {{
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            /* Make key containers transparent/semi-transparent */
            QWidget#CentralWidget {{
                background: transparent;
            }}
        """)
        
        # Central widget
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)
        
        # Main vertical layout (Header - Content - Footer)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Header
        self.header_widget = HeaderWidget()
        main_layout.addWidget(self.header_widget)
        
        # 2. Content Area
        # [UI REFACTOR] Responsive grid system: Left (20%) | Center (60%) | Right (20%)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(20)  # Increased spacing for better breathing room
        content_layout.setContentsMargins(20, 20, 20, 20)  # Increased margins
        
        # Left Panel (Control Panel) - ~20% width
        # Wrap in scroll area to prevent cutoff issues
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #0f172a;
                width: 8px;
                margin: 0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        self.control_panel = ControlPanel()
        left_scroll.setWidget(self.control_panel)
        # Set minimum width but allow expansion
        left_scroll.setMinimumWidth(280)
        left_scroll.setMaximumWidth(320)
        # Ensure scroll area respects widget's minimum height
        left_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        content_layout.addWidget(left_scroll, 2)  # Stretch factor 2 (~20%)
        
        # Center Panel (Graph) - ~60% width, primary focus
        self.graph_widget = GraphWidget()
        # Set size policy for proper expansion
        self.graph_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.graph_widget, 6)  # Stretch factor 6 (~60%)
        
        # Right Panel Container (Scrollable Sidebar) - ~20% width
        right_scroll = QScrollArea()
        right_scroll.setMinimumWidth(400)
        right_scroll.setMaximumWidth(450)
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Style the scrollbar
        right_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #0f172a;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        
        right_sidebar = QWidget()
        right_sidebar.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_sidebar)
        right_layout.setContentsMargins(0, 0, 12, 0)  # Right margin for scrollbar breathing room
        right_layout.setSpacing(20)  # Increased spacing between sections
        
        # Results Panel (Top) - Flexible, can shrink if needed
        self.results_panel = ResultsPanel()
        right_layout.addWidget(self.results_panel, 3)  # Stretch factor 3 (gives priority but allows shrinking)
        
        # Experiments Panel (Bottom) - Fixed size when visible
        self.experiments_panel = ExperimentsPanel()
        self.experiments_panel.hide()  # Hidden by default
        right_layout.addWidget(self.experiments_panel, 1)  # Stretch factor 1 (lowest priority)
        
        right_scroll.setWidget(right_sidebar)
        content_layout.addWidget(right_scroll, 2)  # Stretch factor 2 (~20%)
        
        main_layout.addWidget(content_widget, 1)
        
        # 3. Footer
        self.footer_widget = FooterWidget()
        main_layout.addWidget(self.footer_widget)
        
        # Floating Widgets (Overlays)
        self.path_info_widget = PathInfoWidget(self.graph_widget)
        self.path_info_widget.move(20, 20)
        
        self.legend_widget = LegendWidget(self.graph_widget)
        # Position will be set in resizeEvent
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Hazır", 2000)
        
    def resizeEvent(self, event):
        """Pencere boyutu değiştiğinde overlay pozisyonlarını güncelle."""
        super().resizeEvent(event)
        # Legend sağ alt köşeye
        if hasattr(self, 'legend_widget') and hasattr(self, 'graph_widget'):
            gw_rect = self.graph_widget.geometry()
            # GraphWidget coordinates are relative to its parent (content_widget)
            # But legend is child of graph_widget, so relative to graph_widget (0,0)
            
            # Legend bottom-right inside graph widget
            # Note: GraphWidget has controls at bottom, so place legend top-right or above controls
            # Let's place it Top-Right
            self.legend_widget.move(
                20,
                self.graph_widget.height() - self.legend_widget.height() - 20
            )
            
    def _connect_signals(self):
        # Control panel
        self.control_panel.generate_graph_requested.connect(self._on_generate_graph)
        self.control_panel.load_csv_requested.connect(self._on_load_csv)
        self.control_panel.optimize_requested.connect(self._on_optimize)
        self.control_panel.compare_requested.connect(self._on_compare)
        self.control_panel.reset_requested.connect(self._on_reset)
        self.control_panel.demand_selected.connect(self._on_demand_selected)
        
        # Experiments panel
        self.experiments_panel.run_experiments_requested.connect(self._on_run_experiments)
        self.experiments_panel.run_scalability_requested.connect(self._on_run_scalability_analysis)
        self.experiments_panel.load_scenarios_requested.connect(self._on_load_test_scenarios)
        self.experiments_panel.compare_two_requested.connect(self._on_compare_two_algorithms)
        self.experiments_panel.show_path_requested.connect(self._on_show_path_requested)
        
        # Graph widget
        self.graph_widget.node_clicked.connect(self._on_node_clicked)
        # ====================================================================
        # [CHAOS MONKEY FEATURE] Edge Break Signal Connection
        # ====================================================================
        # GraphWidget'dan gelen edge_broken signal'ini dinler.
        # Bir edge kırıldığında otomatik olarak _on_edge_broken() çağrılır
        # ve sistem mevcut kaynak/hedef için yeniden optimizasyon yapar.
        # ====================================================================
        self.graph_widget.edge_broken.connect(self._on_edge_broken)
        
        # Results panel PDF export
        self.results_panel.export_pdf_requested.connect(self._on_export_pdf)
        self.results_panel.export_comparison_pdf_requested.connect(self._on_export_comparison_pdf)

    def _on_compare_two_algorithms(self, algo1: str, algo2: str):
        """İki algoritmayı kıyasla."""
        if not self._check_graph(): return
        
        # Parametreleri al
        source = self.control_panel.spin_source.value()
        dest = self.control_panel.spin_dest.value()
        if source == dest:
            QMessageBox.warning(self, "Uyarı", "Kaynak ve hedef farklı olmalı!")
            return
            
        weights = self.control_panel._get_weights()
        if not weights:
            QMessageBox.warning(self, "Uyarı", "Ağırlıklar eksik.")
            return

        self.control_panel.set_loading(True)
        self.status_bar.showMessage(f"Kıyaslanıyor: {algo1} vs {algo2}...")
        
        self.current_worker = ComparisonWorker(
            self.graph_service.graph, 
            source, 
            dest, 
            weights,
            target_algorithms=[algo1, algo2]
        )
        self.current_worker.finished.connect(self._on_two_algo_comparison_finished)
        self.current_worker.error.connect(self._on_error)
        # self.current_worker.progress.connect(...) 
        self.current_worker.start()

    def _on_two_algo_comparison_finished(self, results: List[OptimizationResult]):
        self.control_panel.set_loading(False)
        self.status_bar.showMessage("Kıyaslama tamamlandı!", 3000)
        
        if len(results) >= 2:
            r1 = results[0]
            r2 = results[1]
            self.experiments_panel.update_comparison_results(
                r1.algorithm, r1.weighted_cost, r1.computation_time_ms,
                r2.algorithm, r2.weighted_cost, r2.computation_time_ms
            )
            # İsteğe bağlı olarak sonuçları ana panele de yansıtabiliriz ama 
            # kullanıcı sadece kartta görmek istemiş gibi.
        else:
             QMessageBox.warning(self, "Hata", "Sonuçlar alınamadı.")
        
    def _on_generate_graph(self, n_nodes: int, prob: float, seed: int):
        self.control_panel.set_loading(True)
        self.graph_service = GraphService(seed=seed)
        
        self.current_worker = GraphGenerationWorker(self.graph_service, n_nodes, prob)
        self.current_worker.finished.connect(self._on_graph_generated)
        self.current_worker.error.connect(self._on_error)
        self.current_worker.start()
        
    def _on_graph_generated(self, graph, positions, info):
        self.control_panel.set_loading(False)
        self.graph_widget.set_graph(graph, positions)
        self.control_panel.set_node_range(info['node_count'])
        self.control_panel.hide_demands()  # Rastgele graf için talep yok
        self.results_panel.clear()
        self.path_info_widget.hide()
        
        # Update Header Stats
        self.header_widget.update_stats(
            info['node_count'], 
            info['edge_count'], 
            info['is_connected']
        )
        
        # Auto-Show Experiments Panel when starting new project
        self.experiments_panel.show()
    
    def _on_load_csv(self):
        """CSV dosyalarından graf yükle."""
        # Önce app ile aynı dizindeki graph_data klasörünü otomatik bul
        if os.path.exists(GRAPH_DATA_DIR) and os.path.isdir(GRAPH_DATA_DIR):
            data_dir = GRAPH_DATA_DIR
        else:
            # Bulunamazsa kullanıcıdan manuel seçim iste
            data_dir = QFileDialog.getExistingDirectory(
                self,
                "graph_data Klasörünü Seçin",
                PROJECT_ROOT,
                QFileDialog.ShowDirsOnly
            )
            if not data_dir:
                return
        
        self.control_panel.set_loading(True)
        
        try:
            self.graph_service = GraphService()
            graph = self.graph_service.load_from_csv(data_dir)
            positions = self.graph_service.get_node_positions()
            
            self.graph_widget.set_graph(graph, positions)
            
            info = self.graph_service.get_graph_info()
            n_nodes = info['node_count']
            
            self.control_panel.set_node_range(n_nodes)
            
            # Talep çiftlerini yükle
            demands = self.graph_service.get_demand_pairs_for_ui()
            self.control_panel.set_demands(demands)
            
            self.results_panel.clear()
            self.path_info_widget.hide()
            
            # Update Header Stats
            self.header_widget.update_stats(
                info['node_count'], 
                info['edge_count'], 
                info['is_connected']
            )
            
            # Auto-Show Experiments Panel
            self.experiments_panel.show()
            
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Dosya Bulunamadı", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"CSV yükleme hatası: {str(e)}")
        
        finally:
            self.control_panel.set_loading(False)
    
    def _on_demand_selected(self, source: int, dest: int, demand_mbps: int):
        """Talep çifti seçildiğinde."""
        self.graph_widget.set_source_destination(source, dest)
            
    def _on_optimize(self, algorithm: str, source: int, dest: int, weights: Dict, bandwidth_demand: float = 0.0, hyperparameters: Dict = None, n_runs: int = 1, seed: int = None):
        if not self._check_graph(): return
        if source == dest:
            QMessageBox.warning(self, "Uyarı", "Kaynak ve hedef farklı olmalı!")
            return
            
        self.control_panel.set_loading(True)
        
        # [UX] Clear previous results immediately to indicate new process started
        self.graph_widget.set_path([])
        self.results_panel.clear()
        
        self.graph_widget.set_source_destination(source, dest)
        
        # Store multi-start info for result handler
        self._multistart_n_runs = n_runs
        self._multistart_current_run = 0
        self._multistart_best_result = None
        self._multistart_all_results = []
        
        # Instantiate the algorithm class
        # seed: None = random, int = deterministic (reproducible)
        try:
            algorithm_name, AlgoClass = ALGORITHMS[algorithm]
            
            # Map Hyperparameters to Constructor Arguments
            algo_kwargs = {'graph': self.graph_service.graph, 'seed': seed}
            
            # Helper to map keys if they exist in hyperparameters
            def map_param(config_key, arg_name):
                if hyperparameters and config_key in hyperparameters:
                    algo_kwargs[arg_name] = hyperparameters[config_key]

            if algorithm == 'ga':
                map_param('GA_POPULATION_SIZE', 'population_size')
                map_param('GA_GENERATIONS', 'generations')
                map_param('GA_MUTATION_RATE', 'mutation_rate')
                map_param('GA_CROSSOVER_RATE', 'crossover_rate')
                map_param('GA_ELITISM', 'elitism')
                
            elif algorithm == 'aco':
                map_param('ACO_N_ANTS', 'n_ants')
                map_param('ACO_N_ITERATIONS', 'n_iterations')
                map_param('ACO_EVAPORATION_RATE', 'evaporation_rate')
                
                # ACO expects ranges, but UI provides single values
                # We fix the range to the single value to enforce it
                if hyperparameters:
                    if 'ACO_ALPHA' in hyperparameters:
                        val = float(hyperparameters['ACO_ALPHA'])
                        algo_kwargs['alpha_range'] = (val, val)
                    if 'ACO_BETA' in hyperparameters:
                        val = float(hyperparameters['ACO_BETA'])
                        algo_kwargs['beta_range'] = (val, val)
                
            elif algorithm == 'pso':
                map_param('PSO_N_PARTICLES', 'n_particles')
                map_param('PSO_N_ITERATIONS', 'n_iterations')
                map_param('PSO_W', 'w')
                map_param('PSO_C1', 'c1')
                map_param('PSO_C2', 'c2')
                
            elif algorithm == 'sa':
                map_param('SA_INITIAL_TEMPERATURE', 'initial_temp')
                map_param('SA_FINAL_TEMPERATURE', 'final_temp')
                map_param('SA_COOLING_RATE', 'cooling_rate')
                map_param('SA_ITERATIONS_PER_TEMP', 'iter_per_temp')
                
            elif algorithm in ['qlearning', 'sarsa']:
                map_param('QL_EPISODES', 'episodes')
                map_param('QL_LEARNING_RATE', 'learning_rate')
                map_param('QL_DISCOUNT_FACTOR', 'discount_factor')
                map_param('QL_EPSILON_START', 'epsilon_start')
                map_param('QL_EPSILON_END', 'epsilon_end')
                map_param('QL_EPSILON_DECAY', 'epsilon_decay')

            # Store algo settings for multi-start
            self._multistart_algo_class = AlgoClass
            self._multistart_algo_kwargs = algo_kwargs
            self._multistart_algo_name = algorithm_name
            self._multistart_weights = weights
            self._multistart_source = source
            self._multistart_dest = dest
            self._multistart_bandwidth = bandwidth_demand
            
            # Create new instance with mapped parameters
            algorithm_instance = AlgoClass(**algo_kwargs)
        except KeyError:
            QMessageBox.critical(self, "Hata", f"Bilinmeyen algoritma: {algorithm}")
            self.control_panel.set_loading(False)
            return
        
        # Log multi-start info
        if n_runs > 1:
            print(f"[Multi-Start] {algorithm_name} ile {n_runs} çalıştırma başlıyor...")
        
        # Use generic OptimizationWorker which supports progress callbacks for all algorithms
        self.current_worker = GenericOptimizationWorker(
            algorithm_instance=algorithm_instance,
            algorithm_name=algorithm_name,
            graph=self.graph_service.graph,
            source=source,
            dest=dest,
            weights=weights,
            bandwidth_demand=bandwidth_demand
        )
        
        self.current_worker.finished.connect(self._on_optimization_finished)
        self.current_worker.error.connect(self._on_error)
        self.current_worker.start()
        
    def _on_optimization_finished(self, result: OptimizationResult):
        # Multi-start logic
        if hasattr(self, '_multistart_n_runs') and self._multistart_n_runs > 1:
            self._multistart_current_run += 1
            self._multistart_all_results.append(result)
            
            # Track best result
            if self._multistart_best_result is None or result.weighted_cost < self._multistart_best_result.weighted_cost:
                self._multistart_best_result = result
            
            print(f"[Multi-Start] Çalıştırma {self._multistart_current_run}/{self._multistart_n_runs}: fitness={result.weighted_cost:.4f}")
            
            # If more runs needed, start next one
            if self._multistart_current_run < self._multistart_n_runs:
                # Create new algorithm instance
                algorithm_instance = self._multistart_algo_class(**self._multistart_algo_kwargs)
                
                self.current_worker = GenericOptimizationWorker(
                    algorithm_instance=algorithm_instance,
                    algorithm_name=self._multistart_algo_name,
                    graph=self.graph_service.graph,
                    source=self._multistart_source,
                    dest=self._multistart_dest,
                    weights=self._multistart_weights,
                    bandwidth_demand=self._multistart_bandwidth
                )
                self.current_worker.finished.connect(self._on_optimization_finished)
                self.current_worker.error.connect(self._on_error)
                self.current_worker.start()
                return
            
            # All runs complete - show statistics and best result
            all_costs = [r.weighted_cost for r in self._multistart_all_results]
            mean_cost = statistics.mean(all_costs)
            std_cost = statistics.stdev(all_costs) if len(all_costs) > 1 else 0
            min_cost = min(all_costs)
            max_cost = max(all_costs)
            
            print(f"[Multi-Start] Tamamlandı!")
            print(f"  En iyi: {min_cost:.4f}")
            print(f"  En kötü: {max_cost:.4f}")
            print(f"  Ortalama: {mean_cost:.4f} ± {std_cost:.4f}")
            
            # Use best result
            result = self._multistart_best_result
            
            # Reset multi-start state
            self._multistart_n_runs = 1
        
        self.current_result = result
        self.control_panel.set_loading(False)
        
        self.graph_widget.set_path(result.path)
        self.results_panel.show_single_result(result)
        self.path_info_widget.update_path(result.path)
        
        # [LIVE CONVERGENCE PLOT] Keep convergence widget visible if it was used (GA algorithm)
        # It will be hidden automatically for non-GA algorithms in _on_optimize
        
    def _on_compare(self, source: int, dest: int, weights: Dict):
        if not self._check_graph(): return
        
        self.control_panel.set_loading(True)
        self.graph_widget.set_source_destination(source, dest)
        
        self.current_worker = ComparisonWorker(
            self.graph_service.graph, source, dest, weights
        )
        self.current_worker.finished.connect(self._on_comparison_finished)
        self.current_worker.progress.connect(self._on_comparison_progress)
        self.current_worker.error.connect(self._on_error)
        self.current_worker.start()
        
    def _on_comparison_finished(self, results: List[OptimizationResult]):
        self.control_panel.set_loading(False)
        if not results: return
        
        best_result = min(results, key=lambda r: r.weighted_cost)
        self.graph_widget.set_path(best_result.path)
        self.results_panel.show_comparison(results)
        self.path_info_widget.update_path(best_result.path)
        
    def _on_comparison_progress(self, current, total):
        # Optional: update status bar or progress bar in control panel
        pass
        
    def _on_run_experiments(self, n_tests, n_repeats):
        if not self._check_graph():
            QMessageBox.warning(self, "Uyarı", "Önce bir graf yükleyin veya oluşturun!")
            return
            
        self.experiments_panel.set_loading(True)
        self.current_worker = ExperimentsWorker(
            self.graph_service.graph, n_tests, n_repeats
        )
        self.current_worker.progress.connect(self._on_experiment_progress)
        self.current_worker.finished.connect(self._on_experiments_finished)
        self.current_worker.error.connect(self._on_experiment_error)
        self.current_worker.start()
        
    def _on_experiment_progress(self, current, total, message):
        self.experiments_panel.set_progress(current, total)
        self.status_bar.showMessage(f"Deney: {current}/{total} - {message}")
        
    def _on_experiments_finished(self, result_data: dict):
        self.experiments_panel.set_loading(False)
        
        # Paneldeki kısa özeti de güncelle (string formatla)
        summary_text = (
            f"✅ Tamamlandı!\n"
            f"Test: {result_data.get('n_test_cases', 0)}\n"
            f"Süre: {result_data.get('total_time_sec', 0)}s"
        )
        self.experiments_panel.set_finished(summary_text)
        self.status_bar.showMessage("Dehey tamamlandı!", 5000)
        
        # Yeni dialogu göster
        dialog = TestResultsDialog(result_data, self)
        dialog.exec_()
        
    def _on_experiment_error(self, error_msg):
        self.experiments_panel.set_loading(False)
        self.status_bar.showMessage("Deney hatası!", 5000)
        QMessageBox.critical(self, "Deney Hatası", error_msg)
        
    def _on_error(self, error_msg):
        self.control_panel.set_loading(False)
        self.experiments_panel.set_loading(False)
        QMessageBox.critical(self, "Hata", str(error_msg))
        
    def _on_node_clicked(self, node_id):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            self.control_panel.set_destination(node_id)
            self.graph_widget.set_source_destination(
                self.control_panel.spin_source.value(), node_id
            )
        else:
            self.control_panel.set_source(node_id) # Sync Source Input
            self.graph_widget.set_source_destination(
                node_id, self.control_panel.spin_dest.value()
            )
    
    def _on_edge_broken(self, u: int, v: int):
        """
        [CHAOS MONKEY FEATURE] Edge kırıldığında otomatik olarak yeniden optimize et.
        
        Bu metod, GraphWidget'dan gelen edge_broken signal'ini işler.
        
        İşlem Akışı:
        1. Graf kontrolü yapılır
        2. Kaynak/hedef kontrolü yapılır (eğer aynıysa sadece mesaj gösterilir)
        3. Kırılan edge sonrası yol kontrolü yapılır (NetworkX has_path)
        4. Eğer yol varsa, mevcut algoritma ve ağırlıklarla otomatik re-optimization
        5. Eğer yol yoksa kullanıcıya uyarı gösterilir
        
        Args:
            u, v: Kırılan edge'in node ID'leri
        
        ÖNEMLİ NOTLAR:
        - Edge GraphWidget'da zaten graph'tan kaldırılmıştır
        - Mevcut control_panel ayarları (algoritma, ağırlıklar) kullanılır
        - Status bar'da kullanıcıya bilgi mesajı gösterilir
        """
        if not self._check_graph():
            return
        
        # Check if we have a current path and source/destination
        source = self.control_panel.spin_source.value()
        dest = self.control_panel.spin_dest.value()
        
        if source == dest:
            # No valid source/destination, just show message
            self.status_bar.showMessage(f"🔴 Link {u}-{v} kırıldı! Yeni yol hesaplamak için kaynak ve hedef seçin.", 5000)
            return
        
        # Check if path exists after breaking the edge
        try:
            has_path = self.graph_service.has_path(source, dest)
        except Exception:
            has_path = False
        
        if not has_path:
            QMessageBox.warning(
                self, 
                "Yol Bulunamadı", 
                f"Link {u}-{v} kırıldıktan sonra {source} ve {dest} arasında yol kalmadı!"
            )
            self.graph_widget.set_path([])
            self.results_panel.clear()
            return
        
        # Auto-optimize with current settings
        # Get current weights and algorithm from control panel
        weights = self.control_panel._get_weights()
        algorithm = self.control_panel._get_algorithm_key()
        
        # Get demand if available (replicate logic from _on_optimize_clicked)
        # We access private _demands here, assuming standard use
        demand = 0.0
        try:
            if self.control_panel.combo_demands.isVisible():
                idx = self.control_panel.combo_demands.currentIndex()
                if idx >= 0:
                     d_src, d_dst, d_val = self.control_panel._demands[idx]
                     if d_src == source and d_dst == dest:
                         demand = float(d_val)
        except Exception:
            pass # Fail safe
        
        if algorithm and weights:
            self.status_bar.showMessage(f"🔴 Link {u}-{v} kırıldı! Yeni yol hesaplanıyor...", 3000)
            # Trigger optimization
            self._on_optimize(algorithm, source, dest, weights, demand)
        else:
            self.status_bar.showMessage(f"🔴 Link {u}-{v} kırıldı! Yeni yol hesaplamak için optimize edin.", 5000)
            
    def _on_two_algo_comparison_finished(self, results: List[OptimizationResult]):
        self.control_panel.set_loading(False)
        self.status_bar.showMessage("Kıyaslama tamamlandı!", 3000)
        
        if len(results) >= 2:
            r1 = results[0]
            r2 = results[1]
            
            # Retrieve source/dest from the worker
            source = self.current_worker.source if hasattr(self.current_worker, 'source') else self.control_panel.spin_source.value()
            dest = self.current_worker.dest if hasattr(self.current_worker, 'dest') else self.control_panel.spin_dest.value()
            
            self.experiments_panel.update_comparison_results(
                r1.algorithm, r1.weighted_cost, r1.computation_time_ms, r1.path,
                r2.algorithm, r2.weighted_cost, r2.computation_time_ms, r2.path,
                source, dest
            )
        else:
             QMessageBox.warning(self, "Hata", "Sonuçlar alınamadı.")

    def _on_show_path_requested(self, path: List[int], color: str):
        """Kullanıcının seçtiği algoritma yolunu grafikte göster."""
        self.graph_widget.set_path(path, color)

    def _on_reset(self):
        """Projeyi tamamen sıfırla."""
        # 1. Stop any running threads
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()
            self.control_panel.set_loading(False)
            
        # 2. Clear Services
        self.graph_service = None
        self.current_result = None
        
        # 3. Clear UI
        self.graph_widget.clear()
        self.results_panel.clear()
        self.path_info_widget.hide()
        self.experiments_panel.hide()
        
        # Reset Header Stats
        self.header_widget.update_stats(0, 0, False)
        
        # Reset Control Panel Source/Dest range (Optional, or keep default 250)
        self.control_panel.reset_defaults()
            
    def _check_graph(self) -> bool:
        if self.graph_service is None or self.graph_service.graph is None:
            QMessageBox.warning(self, "Uyarı", "Önce graf oluşturun!")
            return False
        return True

    def _on_run_scalability_analysis(self, node_counts: List[int]):
        """Ölçeklenebilirlik analizini başlat."""
        self.experiments_panel.set_loading(True)
        self.status_bar.showMessage("Ölçeklenebilirlik analizi hazırlanıyor...", 3000)
        
        self.current_worker = ScalabilityWorker(node_counts)
        self.current_worker.progress.connect(self._on_scalability_progress)
        self.current_worker.finished.connect(self._on_scalability_finished)
        self.current_worker.error.connect(self._on_experiment_error)
        self.current_worker.start()
        
    def _on_scalability_progress(self, current, total, msg):
        self.status_bar.showMessage(f"Analiz: {current}/{total} - {msg}")
        
    def _on_scalability_finished(self, results):
        self.experiments_panel.set_loading(False)
        self.status_bar.showMessage("Analiz tamamlandı!", 5000)
        
        dialog = ScalabilityDialog(results, self)
        dialog.exec_()

    def _on_load_test_scenarios(self):
        """Test senaryolarını yükle ve göster."""
        if not self._check_graph():
            QMessageBox.warning(self, "Uyarı", "Önce bir graf yükleyin veya oluşturun!")
            return
            
        from src.experiments.test_cases import TestCaseGenerator
        
        generator = TestCaseGenerator(self.graph_service.graph)
        scenarios = generator.get_predefined_test_cases()
        
        dialog = ScenariosDialog(scenarios, self)
        dialog.exec_()



    # =========================================================================
    # PDF EXPORT HANDLERS
    # =========================================================================
    
    def _on_export_pdf(self):
        """Tek optimizasyon sonucunu PDF olarak kaydet."""
        result = self.results_panel.current_result
        if not result:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek sonuç bulunamadı.")
            return
        
        try:
            from src.services.report_service import get_report_service, ReportData, REPORTLAB_AVAILABLE
            
            if not REPORTLAB_AVAILABLE:
                QMessageBox.warning(
                    self, "Uyarı", 
                    "PDF oluşturmak için reportlab kütüphanesi gerekli.\n"
                    "Kurulum: pip install reportlab"
                )
                return
            
            # Dosya kaydetme dialogu
            from PyQt5.QtWidgets import QFileDialog
            import os
            
            default_name = f"QoS_Rapor_{result.algorithm.replace(' ', '_')}.pdf"
            filepath, _ = QFileDialog.getSaveFileName(
                self, "PDF Olarak Kaydet", default_name, "PDF Dosyaları (*.pdf)"
            )
            
            if not filepath:
                return
            
            # Geçici olarak graf görüntüsü kaydet
            import tempfile
            graph_image_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    graph_image_path = tmp.name
                    self.graph_widget.export_as_png(graph_image_path)
            except Exception as e:
                print(f"Graf görüntüsü kaydedilemedi: {e}")
                graph_image_path = None
            
            # Rapor verisi oluştur
            weights = self.control_panel._get_weights()
            info = self.graph_service.get_graph_info() if self.graph_service else {}
            
            report_data = ReportData(
                algorithm_name=result.algorithm,
                source=self.control_panel.spin_source.value(),
                destination=self.control_panel.spin_dest.value(),
                path=result.path,
                total_delay=result.total_delay,
                total_reliability=result.total_reliability,
                resource_cost=result.resource_cost,
                weighted_cost=result.weighted_cost,
                computation_time_ms=result.computation_time_ms,
                weights=weights,
                graph_image_path=graph_image_path,
                node_count=info.get('node_count', 0),
                edge_count=info.get('edge_count', 0)
            )
            
            # PDF oluştur
            service = get_report_service()
            service.generate_pdf_report(report_data, filepath)
            
            # Geçici dosyayı temizle
            if graph_image_path and os.path.exists(graph_image_path):
                os.unlink(graph_image_path)
            
            self.status_bar.showMessage(f"PDF kaydedildi: {filepath}", 5000)
            QMessageBox.information(self, "Başarılı", f"Rapor kaydedildi:\n{filepath}")
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası:\n{str(e)}")
            traceback.print_exc()
    
    def _on_export_comparison_pdf(self):
        """Karşılaştırma sonuçlarını PDF olarak kaydet."""
        results = self.results_panel.comparison_results
        if not results:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek karşılaştırma sonucu bulunamadı.")
            return
        
        try:
            from src.services.report_service import get_report_service, REPORTLAB_AVAILABLE
            
            if not REPORTLAB_AVAILABLE:
                QMessageBox.warning(
                    self, "Uyarı", 
                    "PDF oluşturmak için reportlab kütüphanesi gerekli.\n"
                    "Kurulum: pip install reportlab"
                )
                return
            
            # Dosya kaydetme dialogu
            from PyQt5.QtWidgets import QFileDialog
            
            default_name = "QoS_Karsilastirma_Raporu.pdf"
            filepath, _ = QFileDialog.getSaveFileName(
                self, "PDF Olarak Kaydet", default_name, "PDF Dosyaları (*.pdf)"
            )
            
            if not filepath:
                return
            
            # Sonuçları dict formatına dönüştür
            results_data = []
            for r in results:
                results_data.append({
                    'algorithm': r.algorithm,
                    'total_delay': r.total_delay,
                    'total_reliability': r.total_reliability,
                    'resource_cost': r.resource_cost,
                    'weighted_cost': r.weighted_cost,
                    'computation_time_ms': r.computation_time_ms
                })
            
            weights = self.control_panel._get_weights()
            source = self.control_panel.spin_source.value()
            dest = self.control_panel.spin_dest.value()
            
            # PDF oluştur
            service = get_report_service()
            service.generate_comparison_report(results_data, filepath, source, dest, weights)
            
            self.status_bar.showMessage(f"PDF kaydedildi: {filepath}", 5000)
            QMessageBox.information(self, "Başarılı", f"Rapor kaydedildi:\n{filepath}")
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Hata", f"PDF oluşturma hatası:\n{str(e)}")
            traceback.print_exc()
