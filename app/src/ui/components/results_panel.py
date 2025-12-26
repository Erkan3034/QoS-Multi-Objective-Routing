"""
Sonuçlar Paneli Widget - Optimizasyon sonuçlarını gösterir
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGridLayout,
    QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPixmap
from typing import Dict, List, Optional
from dataclasses import dataclass
import os

# Matplotlib Imports
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

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
    min_bandwidth: float = 0.0

class ComparisonRow(QWidget):
    """Karşılaştırma sonucunu gösteren tek satır (kart)."""
    def __init__(self, rank: int, result: OptimizationResult, parent=None):
        super().__init__(parent)
        self._setup_ui(rank, result)
        
    def _setup_ui(self, rank: int, result: OptimizationResult):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        
        is_winner = (rank == 1)
        
        # Background Styling
        if is_winner:
            self.setStyleSheet("""
                QWidget {
                    background-color: #064e3b; /* emerald-900 */
                    border: 1px solid #10b981; /* emerald-500 */
                    border-radius: 12px;
                }
            """)
        else:
             self.setStyleSheet("""
                QWidget {
                    background-color: #1e293b; /* slate-800 */
                    border: 1px solid #334155;
                    border-radius: 12px;
                }
            """)
        
        # === Header: Rank + Dot + Name + Time ===
        header = QHBoxLayout()
        header.setSpacing(8)
        
        # Rank Circle
        lbl_rank = QLabel(str(rank))
        lbl_rank.setFixedSize(20, 20)
        lbl_rank.setAlignment(Qt.AlignCenter)
        rank_bg = "#10b981" if is_winner else "#475569"
        lbl_rank.setStyleSheet(f"""
            background-color: {rank_bg}; 
            color: white; 
            border-radius: 10px; 
            font-size: 11px; 
            font-weight: bold;
            border: none;
        """)
        header.addWidget(lbl_rank)
        
        # Name
        lbl_name = QLabel(f"{result.algorithm}")
        lbl_name.setStyleSheet(f"color: white; font-weight: bold; font-size: 13px; border: none; background: transparent;")
        header.addWidget(lbl_name)
        
        header.addStretch()
        
        # Time
        lbl_time = QLabel(f"{result.computation_time_ms:.0f}ms")
        lbl_time.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        header.addWidget(lbl_time)
        
        layout.addLayout(header)
        
        # === Metrics Row ===
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(10)
        
        # Helper for columns
        def add_metric(label, val, color):
            box = QHBoxLayout()
            box.setSpacing(4)
            l = QLabel(label)
            l.setStyleSheet("color: #64748b; font-size: 10px; border: none; background: transparent;")
            v = QLabel(val)
            v.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
            box.addWidget(l)
            box.addWidget(v)
            metrics_layout.addLayout(box)
            
        # Metrics
        add_metric("Maliyet:", f"{result.weighted_cost:.4f}", "white")
        add_metric("Gecikme:", f"{result.total_delay:.0f}ms", "#3b82f6")
        add_metric("Hop:", f"{len(result.path)-1}", "#f59e0b")
        
        metrics_layout.addStretch()
        layout.addLayout(metrics_layout)


class ResultsPanel(QWidget):
    """Sonuçlar paneli widget'ı."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400) # Increased width as requested
        self._setup_ui()
    
    def _setup_ui(self):
        """UI kurulumu."""
        # Main Panel Styling
        self.setObjectName("ResultsPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget#ResultsPanel {
                background-color: #111827; 
                border-radius: 16px;
                border: 1px solid #1f2937;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #0f172a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)
        
        # === HEADER ===
        header_layout = QHBoxLayout()
        self.header_title = QLabel("Sonuçlar")
        self.header_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(self.header_title)
        
        # Collapse/Expand Button (Visible only in comparison mode)
        from PyQt5.QtWidgets import QToolButton
        self.btn_toggle_compare = QToolButton()
        self.btn_toggle_compare.setText("➖") 
        self.btn_toggle_compare.setFixedSize(24, 24)
        self.btn_toggle_compare.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_compare.setStyleSheet("""
            QToolButton {
                background-color: #334155; 
                color: white; 
                border-radius: 4px;
                border: none;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #475569;
            }
        """)
        self.btn_toggle_compare.setToolTip("Listeyi Gizle/Göster")
        self.btn_toggle_compare.clicked.connect(self._toggle_comparison_view)
        self.btn_toggle_compare.hide()
        header_layout.addWidget(self.btn_toggle_compare)
        
        header_layout.addStretch()
        
        # Single Result Tags
        self.algo_tag = QLabel("Genetic")
        self.algo_tag.setAlignment(Qt.AlignCenter)
        self.algo_tag.setFixedHeight(24)
        self.algo_tag.setStyleSheet("""
            background-color: #581c87; color: #d8b4fe; padding: 0 12px;
            border-radius: 12px; font-size: 12px; font-weight: bold; border: 1px solid #7e22ce;
        """)
        self.algo_tag.hide()
        header_layout.addWidget(self.algo_tag)
        layout.addLayout(header_layout)
        
        # === SINGLE RESULT VIEWS ===
        self._setup_single_result_views(layout)

        # === COMPARISON VIEW ===
        self._setup_comparison_view(layout)
        
        self.compare_widget.hide()
        
        # === FOOTER ===
        self._setup_footer(layout)
        
        self._setup_placeholder()
        layout.addStretch()

    def _toggle_comparison_view(self):
        """Karşılaştırma listesini aç/kapat."""
        # compare_widget layout: [ChartContainer, ListContainer]
        if hasattr(self, 'compare_list_container'):
            is_visible = self.compare_list_container.isVisible()
            self.compare_list_container.setVisible(not is_visible)
            
            if not is_visible:
                self.btn_toggle_compare.setText("➖")
            else:
                self.btn_toggle_compare.setText("➕")

    def _setup_single_result_views(self, parent_layout):
        # Path
        self.path_group = QWidget()
        self.path_group.setObjectName("PathGroup")
        self.path_group.setStyleSheet("""
            QWidget#PathGroup { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; }
        """)
        path_layout = QVBoxLayout(self.path_group)
        path_layout.setContentsMargins(12, 8, 12, 8)
        
        self.lbl_path_title = QLabel("Bulunan Yol")
        self.lbl_path_title.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        path_layout.addWidget(self.lbl_path_title)
        
        self.lbl_path_value = QLabel("-")
        self.lbl_path_value.setWordWrap(True)
        self.lbl_path_value.setStyleSheet("color: #f1f5f9; font-size: 15px; font-weight: bold; font-family: 'Consolas', monospace;")
        path_layout.addWidget(self.lbl_path_value)
        
        parent_layout.addWidget(self.path_group)
        self.path_group.hide()
        
        # Metrics Grid
        self.metrics_container = QWidget()
        self.metrics_grid = QGridLayout(self.metrics_container)
        self.metrics_grid.setContentsMargins(0, 0, 0, 0)
        self.metrics_grid.setSpacing(12) # Reduced spacing
        
        self.card_delay = self._create_metric_card("icon_delay.svg", "Toplam Gecikme", "0.00 ms", "#3b82f6")
        self.metrics_grid.addWidget(self.card_delay, 0, 0)
        self.card_rel = self._create_metric_card("icon_reliability.svg", "Güvenilirlik", "0.00 %", "#22c55e")
        self.metrics_grid.addWidget(self.card_rel, 0, 1)
        self.card_res = self._create_metric_card("icon_resource.svg", "Kaynak Maliyeti", "0.00", "#eab308")
        self.metrics_grid.addWidget(self.card_res, 1, 0)
        self.card_weighted = self._create_metric_card("icon_weighted.svg", "Ağırlıklı Maliyet", "0.0000", "#a855f7")
        self.metrics_grid.addWidget(self.card_weighted, 1, 1)
        
        parent_layout.addWidget(self.metrics_container)

    def _setup_comparison_view(self, parent_layout):
        self.compare_widget = QWidget()
        layout = QVBoxLayout(self.compare_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 1. Comparison Chart
        if MATPLOTLIB_AVAILABLE:
            self.chart_frame = QFrame()
            self.chart_frame.setStyleSheet("background-color: #1e293b; border-radius: 8px; border: 1px solid #334155;")
            self.chart_frame.setFixedHeight(120) 
            chart_layout = QVBoxLayout(self.chart_frame)
            chart_layout.setContentsMargins(0, 5, 0, 0)
            
            self.figure = Figure(figsize=(3, 1.5), facecolor='#1e293b')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background: transparent;")
            chart_layout.addWidget(self.canvas)
            layout.addWidget(self.chart_frame)
            
        # 2. List Container (No Scroll Area here, use parent scroll)
        self.compare_list_container = QWidget()
        layout.addWidget(self.compare_list_container)
        
        self.compare_list_layout = QVBoxLayout(self.compare_list_container)
        self.compare_list_layout.setSpacing(8)
        self.compare_list_layout.setContentsMargins(0, 0, 0, 0)
        self.compare_list_layout.addStretch()
        
        parent_layout.addWidget(self.compare_widget)

    def _setup_footer(self, parent_layout):
        self.footer_container = QWidget()
        layout = QHBoxLayout(self.footer_container)
        layout.setContentsMargins(0, 10, 0, 0)
        
        lbl_title = QLabel("Hesaplama Süresi:")
        lbl_title.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(lbl_title)
        
        layout.addStretch()
        
        self.lbl_time_value = QLabel("0.00 ms")
        self.lbl_time_value.setStyleSheet("color: #f1f5f9; font-size: 13px; font-weight: bold;")
        layout.addWidget(self.lbl_time_value)
        
        parent_layout.addWidget(self.footer_container)
        self.footer_container.hide()

    def _setup_placeholder(self):
        self.placeholder = QWidget()
        layout = QVBoxLayout(self.placeholder)
        layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel("⮆") 
        icon.setStyleSheet("font-size: 48px; color: #334155;")
        layout.addWidget(icon)
        
        text = QLabel("Optimizasyon sonuçları\nburada görünecek")
        text.setAlignment(Qt.AlignCenter)
        text.setStyleSheet("color: #64748b; font-size: 14px;")
        layout.addWidget(text)
        
        self.layout().addWidget(self.placeholder)
        self.metrics_container.hide() # Initially hidden

    def _create_metric_card(self, icon, title, value, color):
        card = QWidget()
        card.setStyleSheet(f"background-color: #1e293b; border: 1px solid #334155; border-radius: 12px;")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(8, 8, 8, 8)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
        lay.addWidget(lbl_title)
        
        lbl_val = QLabel(value)
        lbl_val.setObjectName("ValueLabel")
        lbl_val.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        lay.addWidget(lbl_val)
        return card

    def _update_card(self, card, value):
        lbl = card.findChild(QLabel, "ValueLabel")
        if lbl: lbl.setText(str(value))

    def _update_chart(self, results: List[OptimizationResult]):
        if not MATPLOTLIB_AVAILABLE: return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111, facecolor='#1e293b')
        
        # Prepare Data (Top 3 or 5 to keep it clean?) Show all 6.
        # Shorten names
        names = [r.algorithm.replace("Algorithm", "").replace("Optimization", "").strip()[:5] for r in results]
        costs = [r.weighted_cost for r in results]
        colors = ['#22c55e', '#eab308', '#3b82f6', '#ef4444', '#ec4899', '#6366f1']
        
        bars = ax.bar(names, costs, color=colors[:len(results)])
        
        ax.set_title("Maliyet Karşılaştırması", color='#94a3b8', fontsize=9, pad=2)
        ax.tick_params(axis='x', colors='#64748b', labelsize=7)
        ax.tick_params(axis='y', colors='#64748b', labelsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#334155')
        ax.spines['left'].set_visible(False)
        ax.grid(axis='y', alpha=0.1, linestyle='--')
        
        self.figure.tight_layout()
        self.canvas.draw()

    def show_single_result(self, result: OptimizationResult):
        if hasattr(self, 'placeholder'): self.placeholder.hide()
        self.compare_widget.hide()
        self.metrics_container.show()
        self.path_group.show()
        self.footer_container.show()
        
        # Hide toggle button in single view
        self.btn_toggle_compare.hide()
        
        self.header_title.setText("Sonuçlar")
        self.algo_tag.setText(result.algorithm)
        self.algo_tag.show()
        
        self.lbl_path_title.setText(f"Bulunan Yol ({len(result.path)-1} hop)")
        if len(result.path) > 10:
             self.lbl_path_value.setText(f"{result.path[0]} → ... → {result.path[-1]}")
        else:
             self.lbl_path_value.setText(" → ".join(map(str, result.path)))
             
        self._update_card(self.card_delay, f"{result.total_delay:.2f} ms")
        self._update_card(self.card_rel, f"{result.total_reliability*100:.2f} %")
        self._update_card(self.card_res, f"{result.resource_cost:.2f}")
        self._update_card(self.card_weighted, f"{result.weighted_cost:.4f}")
        self.lbl_time_value.setText(f"{result.computation_time_ms:.2f} ms")

    def show_comparison(self, results: List[OptimizationResult]):
        if hasattr(self, 'placeholder'): self.placeholder.hide()
        self.metrics_container.hide()
        self.path_group.hide()
        self.algo_tag.hide()
        
        # Show toggle button in comparison view
        self.btn_toggle_compare.show()
        self.btn_toggle_compare.setText("➖") # Reset to expanded state
        if hasattr(self, 'compare_list_container'):
             self.compare_list_container.show()
        
        self.header_title.setText("Karşılaştırma")
        self.compare_widget.show()
        self.footer_container.show()
        
        # Sort by cost
        results.sort(key=lambda x: x.weighted_cost)
        
        # Update Chart
        self._update_chart(results)
        
        # Clear list
        while self.compare_list_layout.count() > 1:
            child = self.compare_list_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        # Add Rows
        for i, res in enumerate(results):
            row = ComparisonRow(i+1, res)
            self.compare_list_layout.insertWidget(i, row)
            
        self.lbl_time_value.setText(f"{len(results)} algoritma")

    def clear(self):
        if hasattr(self, 'placeholder'): self.placeholder.show()
        self.metrics_container.hide()
        self.path_group.hide()
        self.footer_container.hide()
        self.compare_widget.hide()
        self.algo_tag.hide()
        self.btn_toggle_compare.hide()


