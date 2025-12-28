"""
Pareto Frontier Dialog

Bu dialog Pareto optimal çözümleri görselleştirir:
- 3D Scatter Plot (Delay vs Reliability vs Resource)
- Pareto sınırı ve domine edilen çözümler
- İstatistikler ve karşılaştırma tablosu
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QWidget,
    QFileDialog, QMessageBox, QTabWidget, QSizePolicy, QComboBox,
    QGroupBox, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from typing import List, Dict, Optional
import json

# Matplotlib import
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from mpl_toolkits.mplot3d import Axes3D
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ParetoDialog(QDialog):
    """Pareto analiz sonuçlarını gösteren gelişmiş pencere."""
    
    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.result = result
        self.setWindowTitle("Pareto Optimalite Analizi")
        self.setMinimumSize(1000, 700)
        self._setup_style()
        self._setup_ui()
        self._populate_data()
    
    def _setup_style(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0f172a, stop:1 #1e293b);
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QTableWidget {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                gridline-color: #334155;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #334155;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
            }
            QHeaderView::section {
                background-color: #334155;
                color: #e2e8f0;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #334155;
                border-radius: 8px;
                background: #1e293b;
            }
            QTabBar::tab {
                background: #334155;
                color: #94a3b8;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
            }
            QGroupBox {
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title = QLabel("🎯 Pareto Optimalite Analizi")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)
        
        # İstatistik kartları
        stats_layout = self._create_stats_cards()
        layout.addLayout(stats_layout)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Tab 1: Pareto Grafiği
        if MATPLOTLIB_AVAILABLE:
            chart_tab = self._create_chart_tab()
            tabs.addTab(chart_tab, "📊 Pareto Grafiği")
        
        # Tab 2: Pareto Sınırı Tablosu
        frontier_tab = self._create_frontier_table()
        tabs.addTab(frontier_tab, f"⭐ Pareto Sınırı ({self.result.pareto_count})")
        
        # Tab 3: Tüm Çözümler
        all_tab = self._create_all_solutions_table()
        tabs.addTab(all_tab, f"📋 Tüm Çözümler ({self.result.total_solutions})")
        
        layout.addWidget(tabs, 1)
        
        # Footer butonları
        footer = self._create_footer()
        layout.addLayout(footer)
    
    def _create_stats_cards(self):
        layout = QHBoxLayout()
        
        # Kart verileri
        cards_data = [
            ("Toplam Çözüm", str(self.result.total_solutions), "#3b82f6"),
            ("Pareto Optimal", str(self.result.pareto_count), "#10b981"),
            ("Domine Edilen", str(self.result.dominated_count), "#f59e0b"),
            ("Süre (ms)", f"{self.result.computation_time_ms:.1f}", "#8b5cf6"),
        ]
        
        for title, value, color in cards_data:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: {color}20;
                    border: 1px solid {color};
                    border-radius: 10px;
                    padding: 15px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            
            val_label = QLabel(value)
            val_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
            val_label.setAlignment(Qt.AlignCenter)
            
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 12px; color: #94a3b8;")
            title_label.setAlignment(Qt.AlignCenter)
            
            card_layout.addWidget(val_label)
            card_layout.addWidget(title_label)
            layout.addWidget(card)
        
        return layout
    
    def _create_chart_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Matplotlib figürü
        fig = Figure(figsize=(10, 6), facecolor='#1e293b')
        canvas = FigureCanvas(fig)
        
        # 2D scatter plot (Delay vs Reliability, renk = Resource)
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0f172a')
        
        # Pareto sınırı
        pareto = self.result.pareto_frontier
        dominated = [s for s in self.result.all_solutions if s.is_dominated]
        
        if dominated:
            dom_delays = [s.delay for s in dominated]
            dom_rels = [s.reliability for s in dominated]
            ax.scatter(dom_delays, dom_rels, c='#64748b', alpha=0.5, 
                      s=50, label='Domine Edilen', marker='o')
        
        if pareto:
            par_delays = [s.delay for s in pareto]
            par_rels = [s.reliability for s in pareto]
            par_res = [s.resource_cost for s in pareto]
            
            scatter = ax.scatter(par_delays, par_rels, c=par_res, 
                                cmap='RdYlGn_r', s=100, 
                                label='Pareto Optimal', marker='*',
                                edgecolors='white', linewidths=1)
            
            cbar = fig.colorbar(scatter, ax=ax)
            cbar.set_label('Resource Cost', color='#e2e8f0')
            cbar.ax.yaxis.set_tick_params(color='#e2e8f0')
            cbar.outline.set_edgecolor('#334155')
            for label in cbar.ax.get_yticklabels():
                label.set_color('#e2e8f0')
        
        ax.set_xlabel('Gecikme (ms)', color='#e2e8f0', fontsize=12)
        ax.set_ylabel('Güvenilirlik', color='#e2e8f0', fontsize=12)
        ax.set_title('Pareto Sınırı: Gecikme vs Güvenilirlik', 
                    color='#f1f5f9', fontsize=14, fontweight='bold')
        ax.tick_params(colors='#94a3b8')
        ax.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#e2e8f0')
        ax.grid(True, alpha=0.2, color='#475569')
        
        for spine in ax.spines.values():
            spine.set_color('#334155')
        
        fig.tight_layout()
        layout.addWidget(canvas)
        
        return widget
    
    def _create_frontier_table(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.frontier_table = QTableWidget()
        self.frontier_table.setColumnCount(5)
        self.frontier_table.setHorizontalHeaderLabels([
            "Sıra", "Gecikme (ms)", "Güvenilirlik", "Kaynak Maliyeti", "Yol Uzunluğu"
        ])
        self.frontier_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.frontier_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.frontier_table)
        return widget
    
    def _create_all_solutions_table(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.all_table = QTableWidget()
        self.all_table.setColumnCount(6)
        self.all_table.setHorizontalHeaderLabels([
            "Sıra", "Gecikme (ms)", "Güvenilirlik", "Kaynak Maliyeti", 
            "Yol Uzunluğu", "Durum"
        ])
        self.all_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.all_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.all_table)
        return widget
    
    def _create_footer(self):
        layout = QHBoxLayout()
        
        # Tam ekran butonu
        self.fullscreen_btn = QPushButton("⛶ Tam Ekran")
        self.fullscreen_btn.setStyleSheet(self._btn_style("#3b82f6"))
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        layout.addWidget(self.fullscreen_btn)
        
        layout.addStretch()
        
        export_btn = QPushButton("📥 JSON Olarak Kaydet")
        export_btn.setStyleSheet(self._btn_style("#10b981"))
        export_btn.clicked.connect(self._on_export)
        layout.addWidget(export_btn)
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(self._btn_style("#64748b"))
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return layout
    
    def _toggle_fullscreen(self):
        """Tam ekran modunu aç/kapat."""
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("⛶ Tam Ekran")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("⛶ Normal")
    
    def keyPressEvent(self, event):
        """ESC ile tam ekrandan çık, F11 ile toggle."""
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("⛶ Tam Ekran")
        elif event.key() == Qt.Key_F11:
            self._toggle_fullscreen()
        else:
            super().keyPressEvent(event)
    
    def _btn_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color}cc;
            }}
        """
    
    def _populate_data(self):
        # Pareto sınırı tablosu
        pareto = sorted(self.result.pareto_frontier, key=lambda s: s.delay)
        self.frontier_table.setRowCount(len(pareto))
        
        for i, sol in enumerate(pareto):
            self.frontier_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.frontier_table.setItem(i, 1, QTableWidgetItem(f"{sol.delay:.2f}"))
            self.frontier_table.setItem(i, 2, QTableWidgetItem(f"{sol.reliability:.6f}"))
            self.frontier_table.setItem(i, 3, QTableWidgetItem(f"{sol.resource_cost:.4f}"))
            self.frontier_table.setItem(i, 4, QTableWidgetItem(str(len(sol.path))))
        
        # Tüm çözümler tablosu
        all_sols = sorted(self.result.all_solutions, 
                         key=lambda s: (s.is_dominated, s.delay))
        self.all_table.setRowCount(len(all_sols))
        
        for i, sol in enumerate(all_sols):
            self.all_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.all_table.setItem(i, 1, QTableWidgetItem(f"{sol.delay:.2f}"))
            self.all_table.setItem(i, 2, QTableWidgetItem(f"{sol.reliability:.6f}"))
            self.all_table.setItem(i, 3, QTableWidgetItem(f"{sol.resource_cost:.4f}"))
            self.all_table.setItem(i, 4, QTableWidgetItem(str(len(sol.path))))
            
            status = "⭐ Pareto" if not sol.is_dominated else f"❌ Domine ({sol.domination_count})"
            status_item = QTableWidgetItem(status)
            if not sol.is_dominated:
                status_item.setBackground(QColor("#10b98130"))
            self.all_table.setItem(i, 5, status_item)
    
    def _on_export(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "JSON Kaydet", "", "JSON Files (*.json)"
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.result.to_dict(), f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Başarılı", "Pareto analizi kaydedildi!")


__all__ = ["ParetoDialog"]
