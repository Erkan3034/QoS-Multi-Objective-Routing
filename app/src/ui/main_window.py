"""
Ana Pencere - QoS Routing Desktop Application
"""
import sys
import os
import random
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QStatusBar, QApplication, QTabWidget, QSplitter,
    QScrollArea, QFrame, QFileDialog
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

from src.services.graph_service import GraphService
from src.services.metrics_service import MetricsService
from src.algorithms import ALGORITHMS

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

class OptimizationWorker(QThread):
    """Arka plan optimizasyon thread'i."""
    
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
                computation_time_ms=result.computation_time_ms
            )
            
            self.finished.emit(opt_result)
            
        except Exception as e:
            self.error.emit(str(e))

class ComparisonWorker(QThread):
    """Tüm algoritmaları karşılaştırma thread'i."""
    
    finished = pyqtSignal(list)  # results
    progress = pyqtSignal(int, int)  # current, total
    error = pyqtSignal(str)
    
    def __init__(self, graph, source, dest, weights):
        super().__init__()
        self.graph = graph
        self.source = source
        self.dest = dest
        self.weights = weights
    
    def run(self):
        try:
            results = []
            total = len(ALGORITHMS)
            
            for i, (key, (name, AlgoClass)) in enumerate(ALGORITHMS.items()):
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
                        computation_time_ms=result.computation_time_ms
                    ))
                except Exception as e:
                    print(f"Error in {name}: {e}")
            
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(str(e))

class ExperimentsWorker(QThread):
    """Toplu deney çalıştırma thread'i."""
    
    finished = pyqtSignal(str)  # summary
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
            
            # Özet oluştur
            comparison = result.get_comparison_table()
            summary = f"✅ Deney Tamamlandı!\n\n"
            summary += f"Test Sayısı: {len(test_cases)}\n"
            summary += f"Tekrar Sayısı: {self.n_repeats}\n"
            summary += f"Toplam Süre: {result.total_time_sec:.2f} saniye\n"
            summary += f"Başarısız Test: {len(result.failure_report.failed_cases)}\n\n"
            summary += "Algoritma Karşılaştırması:\n"
            for algo in comparison:
                summary += f"  • {algo['algorithm']}: "
                summary += f"Ort. Maliyet={algo['overall_avg_cost']:.4f}, "
                summary += f"Başarı Oranı={algo['success_rate']*100:.1f}%\n"
            
            self.finished.emit(summary)
            
        except Exception as e:
            import traceback
            error_msg = f"Deney hatası: {str(e)}\n{traceback.format_exc()}"
            self.error.emit(error_msg)

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
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f172a;
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main vertical layout (Header - Content - Footer)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 1. Header
        self.header_widget = HeaderWidget()
        main_layout.addWidget(self.header_widget)
        
        # 2. Content Area
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(16, 16, 16, 16)
        
        # Left Panel (Control Panel)
        self.control_panel = ControlPanel()
        content_layout.addWidget(self.control_panel)
        
        # Right Panel Container (Scrollable Sidebar)
        right_scroll = QScrollArea()
        right_scroll.setFixedWidth(340) # 320 content + 20 scroll
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
        right_layout.setContentsMargins(0, 0, 10, 0) # Right margin for scrollbar breathing room
        right_layout.setSpacing(16)
        
        # Results Panel (Top)
        # Results Panel (Top)
        self.results_panel = ResultsPanel()
        right_layout.addWidget(self.results_panel, 1) # Stretch to fill available space
        
        # Experiments Panel (Bottom)
        self.experiments_panel = ExperimentsPanel()
        self.experiments_panel.hide() # Hidden by default
        right_layout.addWidget(self.experiments_panel)
        
        # right_layout.addStretch() # Removed to allow results_panel to expand
        
        right_scroll.setWidget(right_sidebar)
        content_layout.addWidget(right_scroll)
        
        # Center (Graph) - Correct placement between Left and Right
        # Note: We need to insert it at index 1
        self.graph_widget = GraphWidget()
        content_layout.insertWidget(1, self.graph_widget, 1)
        
        main_layout.addWidget(content_widget, 1)
        
        # 3. Footer
        self.footer_widget = FooterWidget()
        main_layout.addWidget(self.footer_widget)
        
        # Floating Widgets (Overlays)
        self.path_info_widget = PathInfoWidget(self.graph_widget)
        self.path_info_widget.move(20, 20)
        
        self.legend_widget = LegendWidget(self.graph_widget)
        # Position will be set in resizeEvent
        
        # Status bar (Hidden by default as we have footer, but kept for compatibility)
        self.status_bar = QStatusBar()
        self.status_bar.hide()
        self.setStatusBar(self.status_bar)
        
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
        
        # Graph widget
        self.graph_widget.node_clicked.connect(self._on_node_clicked)
        
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
            
    def _on_optimize(self, algorithm: str, source: int, dest: int, weights: Dict):
        if not self._check_graph(): return
        if source == dest:
            QMessageBox.warning(self, "Uyarı", "Kaynak ve hedef farklı olmalı!")
            return
            
        self.control_panel.set_loading(True)
        self.graph_widget.set_source_destination(source, dest)
        
        self.current_worker = OptimizationWorker(
            self.graph_service.graph, algorithm, source, dest, weights
        )
        self.current_worker.finished.connect(self._on_optimization_finished)
        self.current_worker.error.connect(self._on_error)
        self.current_worker.start()
        
    def _on_optimization_finished(self, result: OptimizationResult):
        self.current_result = result
        self.control_panel.set_loading(False)
        
        self.graph_widget.set_path(result.path)
        self.results_panel.show_single_result(result)
        self.path_info_widget.update_path(result.path)
        
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
        
    def _on_experiments_finished(self, summary):
        self.experiments_panel.set_loading(False)
        self.experiments_panel.set_finished(summary)
        self.status_bar.showMessage("Deney tamamlandı!", 5000)
        QMessageBox.information(self, "Deney Tamamlandı", summary)
        
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
