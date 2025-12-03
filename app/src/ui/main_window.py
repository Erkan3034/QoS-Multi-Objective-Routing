"""
Ana Pencere - QoS Routing Desktop Application
"""
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QMessageBox, QStatusBar, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Dict, List, Optional

from src.ui.components.graph_widget import GraphWidget
from src.ui.components.control_panel import ControlPanel
from src.ui.components.results_panel import ResultsPanel, OptimizationResult
from src.services.graph_service import GraphService
from src.services.metrics_service import MetricsService
from src.algorithms import ALGORITHMS


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
            
            # Metrikleri hesapla
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
        self.setMinimumSize(1200, 800)
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
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)
        
        # Left panel (Control)
        self.control_panel = ControlPanel()
        main_layout.addWidget(self.control_panel)
        
        # Center (Graph)
        self.graph_widget = GraphWidget()
        main_layout.addWidget(self.graph_widget, 1)  # stretch factor
        
        # Right panel (Results)
        self.results_panel = ResultsPanel()
        main_layout.addWidget(self.results_panel)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #1e293b;
                color: #94a3b8;
                border-top: 1px solid #334155;
            }
        """)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Hazır. Graf oluşturmak için 'Graf Oluştur' butonuna tıklayın.")
    
    def _connect_signals(self):
        """Sinyalleri bağla."""
        # Control panel signals
        self.control_panel.generate_graph_requested.connect(self._on_generate_graph)
        self.control_panel.optimize_requested.connect(self._on_optimize)
        self.control_panel.compare_requested.connect(self._on_compare)
        
        # Graph widget signals
        self.graph_widget.node_clicked.connect(self._on_node_clicked)
    
    def _on_generate_graph(self, n_nodes: int, prob: float, seed: int):
        """Graf oluştur."""
        self.status_bar.showMessage("Graf oluşturuluyor...")
        self.control_panel.set_loading(True)
        
        try:
            self.graph_service = GraphService(seed=seed)
            graph = self.graph_service.generate_graph(n_nodes=n_nodes, p=prob)
            positions = self.graph_service.get_node_positions()
            
            self.graph_widget.set_graph(graph, positions)
            self.control_panel.set_node_range(n_nodes)
            self.results_panel.clear()
            
            info = self.graph_service.get_graph_info()
            self.status_bar.showMessage(
                f"Graf oluşturuldu: {info['node_count']} düğüm, {info['edge_count']} kenar, "
                f"ortalama derece: {info['average_degree']:.1f}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Graf oluşturma hatası: {str(e)}")
            self.status_bar.showMessage("Hata oluştu")
        
        finally:
            self.control_panel.set_loading(False)
    
    def _on_optimize(self, algorithm: str, source: int, dest: int, weights: Dict):
        """Optimizasyon çalıştır."""
        if self.graph_service is None or self.graph_service.graph is None:
            QMessageBox.warning(self, "Uyarı", "Önce graf oluşturun!")
            return
        
        if source == dest:
            QMessageBox.warning(self, "Uyarı", "Kaynak ve hedef farklı olmalı!")
            return
        
        self.status_bar.showMessage(f"Optimizasyon çalışıyor ({ALGORITHMS[algorithm][0]})...")
        self.control_panel.set_loading(True)
        
        # Kaynak/hedef göster
        self.graph_widget.set_source_destination(source, dest)
        
        # Worker thread başlat
        self.current_worker = OptimizationWorker(
            self.graph_service.graph, algorithm, source, dest, weights
        )
        self.current_worker.finished.connect(self._on_optimization_finished)
        self.current_worker.error.connect(self._on_optimization_error)
        self.current_worker.start()
    
    def _on_optimization_finished(self, result: OptimizationResult):
        """Optimizasyon tamamlandı."""
        self.current_result = result
        self.control_panel.set_loading(False)
        
        # Yolu göster
        self.graph_widget.set_path(result.path)
        
        # Sonuçları göster
        self.results_panel.show_single_result(result)
        
        self.status_bar.showMessage(
            f"✓ {result.algorithm}: {len(result.path)-1} hop, "
            f"maliyet: {result.weighted_cost:.4f}, süre: {result.computation_time_ms:.1f}ms"
        )
    
    def _on_optimization_error(self, error_msg: str):
        """Optimizasyon hatası."""
        self.control_panel.set_loading(False)
        QMessageBox.critical(self, "Hata", f"Optimizasyon hatası: {error_msg}")
        self.status_bar.showMessage("Hata oluştu")
    
    def _on_compare(self, source: int, dest: int, weights: Dict):
        """Tüm algoritmaları karşılaştır."""
        if self.graph_service is None or self.graph_service.graph is None:
            QMessageBox.warning(self, "Uyarı", "Önce graf oluşturun!")
            return
        
        if source == dest:
            QMessageBox.warning(self, "Uyarı", "Kaynak ve hedef farklı olmalı!")
            return
        
        self.status_bar.showMessage("Tüm algoritmalar karşılaştırılıyor...")
        self.control_panel.set_loading(True)
        
        # Kaynak/hedef göster
        self.graph_widget.set_source_destination(source, dest)
        
        # Worker thread başlat
        self.current_worker = ComparisonWorker(
            self.graph_service.graph, source, dest, weights
        )
        self.current_worker.finished.connect(self._on_comparison_finished)
        self.current_worker.progress.connect(self._on_comparison_progress)
        self.current_worker.error.connect(self._on_optimization_error)
        self.current_worker.start()
    
    def _on_comparison_progress(self, current: int, total: int):
        """Karşılaştırma ilerlemesi."""
        self.status_bar.showMessage(f"Algoritma {current}/{total} çalıştırılıyor...")
    
    def _on_comparison_finished(self, results: List[OptimizationResult]):
        """Karşılaştırma tamamlandı."""
        self.control_panel.set_loading(False)
        
        if not results:
            QMessageBox.warning(self, "Uyarı", "Hiçbir algoritma başarılı olmadı!")
            return
        
        # En iyi sonucun yolunu göster
        best_result = min(results, key=lambda r: r.weighted_cost)
        self.graph_widget.set_path(best_result.path)
        self.current_result = best_result
        
        # Karşılaştırma tablosunu göster
        self.results_panel.show_comparison(results)
        
        self.status_bar.showMessage(
            f"✓ Karşılaştırma tamamlandı. En iyi: {best_result.algorithm} "
            f"({best_result.weighted_cost:.4f})"
        )
    
    def _on_node_clicked(self, node_id: int):
        """Düğüme tıklandı."""
        # Shift tuşu basılıysa hedef, değilse kaynak olarak ayarla
        modifiers = QApplication.keyboardModifiers()
        
        if modifiers == Qt.ShiftModifier:
            self.control_panel.set_destination(node_id)
            self.graph_widget.set_source_destination(
                self.control_panel.spin_source.value(), node_id
            )
            self.status_bar.showMessage(f"Hedef düğüm: {node_id}")
        else:
            self.control_panel.set_source(node_id)
            self.graph_widget.set_source_destination(
                node_id, self.control_panel.spin_dest.value()
            )
            self.status_bar.showMessage(f"Kaynak düğüm: {node_id} (Shift+tıklama ile hedef seç)")

