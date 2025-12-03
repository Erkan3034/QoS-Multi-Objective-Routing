"""
Sonuçlar Paneli Widget - Optimizasyon sonuçlarını gösterir
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class OptimizationResult:
    """Optimizasyon sonucu veri sınıfı."""
    algorithm: str
    path: List[int]
    total_delay: float
    total_reliability: float
    resource_cost: float
    weighted_cost: float
    computation_time_ms: float


class ResultsPanel(QWidget):
    """Sonuçlar paneli widget'ı."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI kurulumu."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # === TEK SONUÇ ===
        self.result_group = QGroupBox("📈 Sonuç")
        self.result_group.setStyleSheet(self._group_style())
        result_layout = QVBoxLayout(self.result_group)
        
        # Algorithm name
        self.label_algorithm = QLabel("Algoritma: -")
        self.label_algorithm.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 14px;")
        result_layout.addWidget(self.label_algorithm)
        
        # Path
        self.label_path = QLabel("Yol: -")
        self.label_path.setWordWrap(True)
        self.label_path.setStyleSheet("color: #94a3b8; font-size: 11px;")
        result_layout.addWidget(self.label_path)
        
        # Metrics grid
        metrics_layout = QVBoxLayout()
        metrics_layout.setSpacing(4)
        
        self.label_delay = self._create_metric_label("Gecikme:", "-")
        self.label_reliability = self._create_metric_label("Güvenilirlik:", "-")
        self.label_resource = self._create_metric_label("Kaynak Maliyeti:", "-")
        self.label_weighted = self._create_metric_label("Ağırlıklı Maliyet:", "-", highlight=True)
        self.label_time = self._create_metric_label("Hesaplama Süresi:", "-")
        self.label_hops = self._create_metric_label("Hop Sayısı:", "-")
        
        metrics_layout.addWidget(self.label_delay)
        metrics_layout.addWidget(self.label_reliability)
        metrics_layout.addWidget(self.label_resource)
        metrics_layout.addWidget(self.label_weighted)
        metrics_layout.addWidget(self.label_time)
        metrics_layout.addWidget(self.label_hops)
        
        result_layout.addLayout(metrics_layout)
        layout.addWidget(self.result_group)
        
        # === KARŞILAŞTIRMA TABLOSU ===
        self.compare_group = QGroupBox("📊 Karşılaştırma")
        self.compare_group.setStyleSheet(self._group_style())
        compare_layout = QVBoxLayout(self.compare_group)
        
        self.compare_table = QTableWidget()
        self.compare_table.setColumnCount(4)
        self.compare_table.setHorizontalHeaderLabels(["Algoritma", "Maliyet", "Süre", "Hop"])
        self.compare_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.compare_table.setAlternatingRowColors(True)
        self.compare_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e293b;
                color: #e2e8f0;
                border: none;
                gridline-color: #334155;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
            }
            QHeaderView::section {
                background-color: #334155;
                color: #e2e8f0;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
        """)
        self.compare_table.setMaximumHeight(200)
        compare_layout.addWidget(self.compare_table)
        
        self.label_best = QLabel("En İyi: -")
        self.label_best.setStyleSheet("color: #22c55e; font-weight: bold;")
        compare_layout.addWidget(self.label_best)
        
        layout.addWidget(self.compare_group)
        self.compare_group.hide()  # Başlangıçta gizli
        
        layout.addStretch()
    
    def _group_style(self) -> str:
        return """
            QGroupBox {
                font-weight: bold;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
    
    def _create_metric_label(self, name: str, value: str, highlight: bool = False) -> QLabel:
        """Metrik label oluştur."""
        label = QLabel(f"{name} {value}")
        if highlight:
            label.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 13px;")
        else:
            label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        return label
    
    def show_single_result(self, result: OptimizationResult):
        """Tek sonucu göster."""
        self.compare_group.hide()
        self.result_group.show()
        
        self.label_algorithm.setText(f"Algoritma: {result.algorithm}")
        
        # Path'i kısalt
        path_str = " → ".join(str(n) for n in result.path[:5])
        if len(result.path) > 5:
            path_str += f" → ... → {result.path[-1]}"
        self.label_path.setText(f"Yol: {path_str}")
        
        self.label_delay.setText(f"Gecikme: {result.total_delay:.2f} ms")
        self.label_reliability.setText(f"Güvenilirlik: {result.total_reliability * 100:.2f}%")
        self.label_resource.setText(f"Kaynak Maliyeti: {result.resource_cost:.4f}")
        self.label_weighted.setText(f"Ağırlıklı Maliyet: {result.weighted_cost:.6f}")
        self.label_time.setText(f"Hesaplama Süresi: {result.computation_time_ms:.1f} ms")
        self.label_hops.setText(f"Hop Sayısı: {len(result.path) - 1}")
    
    def show_comparison(self, results: List[OptimizationResult]):
        """Karşılaştırma sonuçlarını göster."""
        self.result_group.hide()
        self.compare_group.show()
        
        # Tabloyu temizle ve doldur
        self.compare_table.setRowCount(len(results))
        
        best_cost = float('inf')
        best_algo = ""
        
        for i, result in enumerate(sorted(results, key=lambda r: r.weighted_cost)):
            # Algorithm
            item_algo = QTableWidgetItem(result.algorithm)
            self.compare_table.setItem(i, 0, item_algo)
            
            # Cost
            item_cost = QTableWidgetItem(f"{result.weighted_cost:.4f}")
            self.compare_table.setItem(i, 1, item_cost)
            
            # Time
            item_time = QTableWidgetItem(f"{result.computation_time_ms:.0f}ms")
            self.compare_table.setItem(i, 2, item_time)
            
            # Hops
            item_hops = QTableWidgetItem(str(len(result.path) - 1))
            self.compare_table.setItem(i, 3, item_hops)
            
            # En iyi'yi işaretle
            if result.weighted_cost < best_cost:
                best_cost = result.weighted_cost
                best_algo = result.algorithm
            
            # İlk satırı vurgula (en iyi)
            if i == 0:
                for j in range(4):
                    item = self.compare_table.item(i, j)
                    if item:
                        item.setBackground(QColor(34, 197, 94, 50))
        
        self.label_best.setText(f"🏆 En İyi: {best_algo} ({best_cost:.4f})")
    
    def clear(self):
        """Sonuçları temizle."""
        self.label_algorithm.setText("Algoritma: -")
        self.label_path.setText("Yol: -")
        self.label_delay.setText("Gecikme: -")
        self.label_reliability.setText("Güvenilirlik: -")
        self.label_resource.setText("Kaynak Maliyeti: -")
        self.label_weighted.setText("Ağırlıklı Maliyet: -")
        self.label_time.setText("Hesaplama Süresi: -")
        self.label_hops.setText("Hop Sayısı: -")
        self.compare_table.setRowCount(0)
        self.label_best.setText("En İyi: -")

