"""
Sonuçlar Paneli Widget - Optimizasyon sonuçlarını gösterir
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QGridLayout,
    QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPixmap
from typing import Dict, List, Optional
from dataclasses import dataclass
import os

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

class ComparisonRow(QWidget):
    """Karşılaştırma sonucunu gösteren tek satır (kart)."""
    def __init__(self, rank: int, result: OptimizationResult, parent=None):
        super().__init__(parent)
        self._setup_ui(rank, result)
        
    def _setup_ui(self, rank: int, result: OptimizationResult):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
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
                    background-color: transparent;
                    border: none;
                }
            """)
        
        # === Header: Rank + Dot + Name + Trophy + Time ===
        header = QHBoxLayout()
        header.setSpacing(8)
        
        # Dot Color based on algo
        colors = {
            "Genetic": "#22c55e", "AntColony": "#eab308", 
            "ParticleSwarm": "#3b82f6", "SimulatedAnnealing": "#ef4444", # Red for SA matching image
            "SARSA": "#ec4899", "QLearning": "#6366f1"
        }
        color = colors.get(result.algorithm, "#94a3b8")
        
        # Dot
        lbl_dot = QLabel("●")
        lbl_dot.setStyleSheet(f"color: {color}; font-size: 14px; border: none; background: transparent;")
        header.addWidget(lbl_dot)
        
        # Name
        lbl_name = QLabel(f"{rank}. {result.algorithm}")
        lbl_name.setStyleSheet(f"color: white; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        header.addWidget(lbl_name)
        
        # Trophy icon if rank 1
        if is_winner:
            lbl_trophy = QLabel("🏆")
            lbl_trophy.setStyleSheet("font-size: 14px; border: none; background: transparent;")
            header.addWidget(lbl_trophy)
            
        header.addStretch()
        
        # Time
        lbl_time = QLabel(f"{result.computation_time_ms:.0f}ms")
        lbl_time.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500; border: none; background: transparent;")
        header.addWidget(lbl_time)
        
        layout.addLayout(header)
        
        # === Metrics Row ===
        # Grid layout for perfect alignment: Maliyet, Gecikme, Guvenilirlik, Hop
        metrics_layout = QHBoxLayout()
        # metrics_layout.setSpacing(16)
        
        # Helper for columns
        def add_metric_col(label_text, val_text, val_color):
            col = QVBoxLayout()
            col.setSpacing(2)
            
            l = QLabel(label_text)
            l.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500; border: none; background: transparent;")
            l.setAlignment(Qt.AlignCenter)
            
            v = QLabel(val_text)
            v.setStyleSheet(f"color: {val_color}; font-size: 12px; font-weight: bold; border: none; background: transparent;")
            v.setAlignment(Qt.AlignCenter)
            
            col.addWidget(l)
            col.addWidget(v)
            metrics_layout.addLayout(col)
            
        # 1. Maliyet (Cost) - White
        add_metric_col("Maliyet", f"{result.weighted_cost:.4f}", "white")
        
        # 2. Gecikme (Delay) - Blue
        add_metric_col("Gecikme", f"{result.total_delay:.1f}ms", "#3b82f6")
        
        # 3. Guvenilirlik - Green
        add_metric_col("Güvenilirlik", f"{result.total_reliability*100:.2f}%", "#22c55e")
        
        # 4. Hop - Orange
        add_metric_col("Hop", f"{len(result.path)-1}", "#f59e0b")
        
        layout.addLayout(metrics_layout)


class ResultsPanel(QWidget):
    """Sonuçlar paneli widget'ı."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI kurulumu."""
        # Main Panel Styling (Card View)
        self.setObjectName("ResultsPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            QWidget#ResultsPanel {
                background-color: #111827; /* gray-900/slate-900 (darker) */
                border-radius: 16px;
                border: 1px solid #1f2937;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Slightly reduced spacing to give more room to convergence plot
        layout.setContentsMargins(14, 14, 14, 14)  # Slightly reduced margins
        
        # === HEADER (Sonuçlar + Algo Tag) ===
        header_layout = QHBoxLayout()
        self.header_title = QLabel("Sonuçlar")
        self.header_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(self.header_title)
        
        header_layout.addStretch()
        
        # Best Algo Badge (For Comparison View)
        self.lbl_best_algo = QLabel("Genetic")
        self.lbl_best_algo.setAlignment(Qt.AlignCenter)
        self.lbl_best_algo.setFixedHeight(24)
        self.lbl_best_algo.setStyleSheet("""
            background-color: #059669; /* emerald-600 */
            color: white; 
            padding: 0 12px; 
            border-radius: 12px; 
            font-size: 11px; 
            font-weight: bold;
            border: 1px solid #047857;
        """)
        self.lbl_best_algo.hide()
        header_layout.addWidget(self.lbl_best_algo)
        
        # Pill shaped tag
        self.algo_tag = QLabel("Genetic")
        self.algo_tag.setAlignment(Qt.AlignCenter)
        self.algo_tag.setFixedHeight(24)
        self.algo_tag.setStyleSheet("""
            background-color: #581c87; /* purple-900 */
            color: #d8b4fe; /* purple-200 */
            padding: 0 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            border: 1px solid #7e22ce;
        """)
        self.algo_tag.hide()
        header_layout.addWidget(self.algo_tag)
        
        layout.addLayout(header_layout)
        
        # === PATH SECTION ===
        # === PATH SECTION (Sub-Card) ===
        self.path_group = QWidget()
        self.path_group.setObjectName("PathGroup")
        self.path_group.setStyleSheet("""
            QWidget#PathGroup {
                background-color: #1e293b; /* slate-800 */
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        path_layout = QVBoxLayout(self.path_group)
        path_layout.setContentsMargins(12, 8, 12, 8)
        path_layout.setSpacing(4)
        
        # Title "Bulunan Yol"
        # Title "Bulunan Yol"
        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        
        lbl_icon = QLabel()
        path_icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", "icon_path.svg")
        if os.path.exists(path_icon_path):
            pixmap = QPixmap(path_icon_path)
            lbl_icon.setPixmap(pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            lbl_icon.setText("🔗") 
            lbl_icon.setStyleSheet("color: #94a3b8; font-size: 14px;")
            
        title_row.addWidget(lbl_icon)

        self.lbl_path_title = QLabel("Bulunan Yol")
        self.lbl_path_title.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 500;")
        title_row.addWidget(self.lbl_path_title)
        
        title_row.addStretch()
        path_layout.addLayout(title_row)
        
        # Path string "3 hop: 2 -> 45 -> 105 -> 249"
        self.lbl_path_value = QLabel("-")
        self.lbl_path_value.setWordWrap(True)
        self.lbl_path_value.setTextInteractionFlags(Qt.TextSelectableByMouse)  # Allow text selection
        self.lbl_path_value.setStyleSheet("color: #f1f5f9; font-size: 15px; font-weight: bold; font-family: 'Consolas', monospace;")
        path_layout.addWidget(self.lbl_path_value)
        
        layout.addWidget(self.path_group)
        self.path_group.hide() # Hidden initially
        
        # === METRICS GRID ===
        self.metrics_container = QWidget()
        self.metrics_grid = QGridLayout(self.metrics_container)
        self.metrics_grid.setContentsMargins(0, 0, 0, 0)
        self.metrics_grid.setSpacing(16)
        
        # 1. Delay (Top Left) - Blue
        self.card_delay = self._create_metric_card("icon_delay.svg", "Toplam Gecikme", "0.00 ms", "#3b82f6")
        self.metrics_grid.addWidget(self.card_delay, 0, 0)
        
        # 2. Reliability (Top Right) - Green
        self.card_rel = self._create_metric_card("icon_reliability.svg", "Güvenilirlik", "0.00 %", "#22c55e")
        self.metrics_grid.addWidget(self.card_rel, 0, 1)
        
        # 3. Resource (Bottom Left) - Yellow/Orange
        self.card_res = self._create_metric_card("icon_resource.svg", "Kaynak Maliyeti", "0.00", "#eab308")
        self.metrics_grid.addWidget(self.card_res, 1, 0)
        
        # 4. Weighted (Bottom Right) - Purple
        # Use a better icon for cost/down trend if possible
        self.card_weighted = self._create_metric_card("icon_weighted.svg", "Ağırlıklı Maliyet", "0.0000", "#a855f7")
        self.metrics_grid.addWidget(self.card_weighted, 1, 1)
        
        layout.addWidget(self.metrics_container)
        
        # === FOOTER (Computation Time) ===
        # === FOOTER (Computation Time) ===
        # Wrap footer in a container to toggle visibility
        self.footer_container = QWidget()
        footer_layout_main = QVBoxLayout(self.footer_container)
        footer_layout_main.setContentsMargins(0, 0, 0, 0)
        footer_layout_main.setSpacing(12) # Spacing between line and text

        footer_line = QFrame()
        footer_line.setFrameShape(QFrame.HLine)
        footer_line.setStyleSheet("color: #334155;")
        footer_layout_main.addWidget(footer_line)

        footer_row_layout = QHBoxLayout()
        footer_row_layout.setSpacing(6)
        
        # Icon
        lbl_time_icon = QLabel()
        time_icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", "icon_time.svg")
        if os.path.exists(time_icon_path):
            pixmap = QPixmap(time_icon_path)
            lbl_time_icon.setPixmap(pixmap.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            lbl_time_icon.setText("⏱")
            lbl_time_icon.setStyleSheet("color: #94a3b8; font-size: 13px;")
        footer_row_layout.addWidget(lbl_time_icon)
        
        lbl_time_title = QLabel("Hesaplama Süresi")
        lbl_time_title.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: 500;")
        footer_row_layout.addWidget(lbl_time_title)
        
        footer_row_layout.addStretch()
        
        self.lbl_time_value = QLabel("0.00 ms")
        self.lbl_time_value.setStyleSheet("color: #f1f5f9; font-size: 14px; font-weight: bold;")
        footer_row_layout.addWidget(self.lbl_time_value)
        
        footer_layout_main.addLayout(footer_row_layout)
        
        layout.addWidget(self.footer_container)
        self.footer_container.hide() # Hidden initially

        # === COMPARISON LIST (Initially Hidden) ===
        self.compare_widget = QWidget()
        compare_layout = QVBoxLayout(self.compare_widget)
        compare_layout.setContentsMargins(0, 0, 0, 0)
        
        # Removed inner header to use main panel header instead
        
        self.compare_container = QWidget()
        self.compare_list_layout = QVBoxLayout(self.compare_container)
        self.compare_list_layout.setSpacing(10)
        self.compare_list_layout.setContentsMargins(0, 0, 0, 0) # No padding needed
        self.compare_list_layout.addStretch()
        
        compare_layout.addWidget(self.compare_container)
        
        layout.addWidget(self.compare_widget)
        self.compare_widget.hide()
        
        self._setup_placeholder()
        
        layout.addStretch()

    def _setup_placeholder(self):
        self.placeholder = QWidget()
        layout = QVBoxLayout(self.placeholder)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        # Icon
        icon_label = QLabel("⮆") # Abstract path icon
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px; color: #334155;")
        layout.addWidget(icon_label)
        
        # Text
        text_label = QLabel("Optimizasyon sonuçları\nburada görünecek")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("color: #64748b; font-size: 14px;")
        layout.addWidget(text_label)
        
        self.layout().addWidget(self.placeholder)
        self.metrics_container.hide() # Ensure metrics are hidden initially

    def _create_metric_card(self, icon, title, value, title_color):
        """Metrik kartı oluştur (Styled Card)."""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #1e293b; /* slate-800 */
                border: 1px solid #334155;
                border-radius: 12px;
            }
        """)
        
        lay = QVBoxLayout(card)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(1)
        
        # Title Row
        title_row = QHBoxLayout()
        title_row.setSpacing(4)
        
        # Icon
        lbl_icon = QLabel()
        lbl_icon.setStyleSheet("border: none; background: transparent;") # Reset style for icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", icon)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            lbl_icon.setPixmap(pixmap.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            lbl_icon.setText("?")
            lbl_icon.setStyleSheet(f"color: {title_color}; font-size: 12px; border: none; background: transparent;")
            
        title_row.addWidget(lbl_icon)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {title_color}; font-size: 10px; font-weight: 700; border: none; background: transparent;")
        title_row.addWidget(lbl_title)
        
        title_row.addStretch()
        lay.addLayout(title_row)
        
        # Value
        lbl_value = QLabel(value)
        lbl_value.setObjectName("ValueLabel") # Helper for finding later
        lbl_value.setWordWrap(True)  # Enable word wrap for large numbers
        lbl_value.setAlignment(Qt.AlignCenter)  # Center align for better appearance
        lbl_value.setStyleSheet("color: #f1f5f9; font-size: 16px; font-weight: bold; margin-top: 0px; border: none; background: transparent;")
        lay.addWidget(lbl_value)
        
        return card

    def _update_card(self, card_widget, value):
        """Kart değerini güncelle."""
        # Find the value label inside the card widget
        # The structure is Card -> QVBoxLayout -> [TitleLayout, ValueLabel]
        # We can findChild by type or iterate. Since we set ObjectName, try findChild.
        lbl_value = card_widget.findChild(QLabel, "ValueLabel")
        if lbl_value:
            lbl_value.setText(str(value))

    def show_single_result(self, result: OptimizationResult):
        """Tek sonucu göster."""
        if hasattr(self, 'placeholder'):
            self.placeholder.hide()
            
        self.compare_widget.hide()
        self.metrics_container.show()
        self.path_group.show() # Show Path
        self.footer_container.show() # Show Footer
        
        self.lbl_path_title.show()
        self.lbl_path_value.show()
        
        # Reset Header
        self.header_title.setText("Sonuçlar")
        self.lbl_best_algo.hide()
        
        # Update details
        self.algo_tag.setText(result.algorithm)
        self.algo_tag.show()
        
        # Path
        if not result.path:
            self.lbl_path_title.setText("🔗 Yol Bulunamadı")
            self.lbl_path_value.setText("-")
            return

        hops = len(result.path) - 1
        self.lbl_path_title.setText(f"Bulunan Yol ({hops} hop)")
        
        if len(result.path) > 5:
            path_str = f"{result.path[0]} → ... → {result.path[-1]}"
        else:
            path_str = " → ".join(map(str, result.path))
            
        self.lbl_path_value.setText(path_str)
        
        # Metrics
        self._update_card(self.card_delay, f"{result.total_delay:.2f} ms")
        self._update_card(self.card_rel, f"{result.total_reliability * 100:.2f} %")
        self._update_card(self.card_res, f"{result.resource_cost:.2f}")
        self._update_card(self.card_weighted, f"{result.weighted_cost:.4f}")
        
        self.lbl_time_value.setText(f"{result.computation_time_ms:.2f} ms")

    def show_comparison(self, results: List[OptimizationResult]):
        """Karşılaştırma sonuçlarını liste olarak göster."""
        if hasattr(self, 'placeholder'):
            self.placeholder.hide()
            
        self.metrics_container.hide()
        self.lbl_path_title.hide()
        self.lbl_path_value.hide()
        self.algo_tag.hide()
        
        # Update Header
        self.header_title.setText("Karşılaştırma Sonuçları")
        self.path_group.hide() # Hide Path
        self.footer_container.show() # Show Footer (for total algorithms count)
        
        self.compare_widget.show()
        
        # Clear previous items (except stretch at end)
        while self.compare_list_layout.count() > 1:
            child = self.compare_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Sort by cost
        results.sort(key=lambda x: x.weighted_cost)
        
        # Update Best Badge
        if results:
            algo_name = results[0].algorithm.replace(" Algorithm", "").replace("Algorithm", "").strip()
            self.lbl_best_algo.setText(f"{algo_name}")
            self.lbl_best_algo.show()
        
        # Add new items
        for i, res in enumerate(results):
             row = ComparisonRow(i + 1, res)
             self.compare_list_layout.insertWidget(i, row)
             
        self.lbl_time_value.setText(f"{len(results)} algoritma")

    def clear(self):
        """Temizle."""
        if hasattr(self, 'placeholder'):
            self.placeholder.show()
            self.metrics_container.hide()
            self.path_group.hide()
            self.footer_container.hide()
            self.compare_widget.hide()
            
        self.algo_tag.hide()
        self.lbl_path_value.setText("-")
        self._update_card(self.card_delay, "-")
        self._update_card(self.card_rel, "-")
        self._update_card(self.card_res, "-")
        self._update_card(self.card_weighted, "-")
        self.lbl_time_value.setText("")


