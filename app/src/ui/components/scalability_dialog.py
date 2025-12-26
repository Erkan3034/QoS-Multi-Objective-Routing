from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QWidget,
    QFileDialog, QMessageBox, QTabWidget, QSizePolicy
)
from PyQt5.QtCore import Qt
import json
import csv

# Matplotlib Imports
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class ScalabilityDialog(QDialog):
    """
    Ölçeklenebilirlik analizi sonuçlarını gösteren gelişmiş pencere.
    - Sekme 1: Detaylı Veri Tablosu
    - Sekme 2: Grafiksel Karşılaştırma (Maliyet & Süre)
    """
    def __init__(self, results: list, parent=None):
        super().__init__(parent)
        self.results = results
        self.setWindowTitle("Ölçeklenebilirlik Analizi Sonuçları")
        self.setMinimumSize(1200, 800) # Increased size for charts
        self._setup_style()
        self._setup_ui()
        
    def _setup_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QTabWidget::pane {
                border: 1px solid #334155;
                background-color: #1e293b;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #0f172a;
                color: #94a3b8;
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #1e293b;
                color: #38bdf8;
                font-weight: bold;
            }
            QTableWidget {
                background-color: #1e293b;
                gridline-color: #334155;
                border: none;
                color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: #94a3b8;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header
        header_layout = QHBoxLayout()
        icon = QLabel("↗")
        icon.setStyleSheet("color: #3b82f6; font-size: 24px; font-weight: bold;")
        title = QLabel("Ölçeklenebilirlik Analizi Raporu")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6;")
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 2. Main Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_table_tab(), "📊 Veri Tablosu")
        tabs.addTab(self._create_charts_tab(), "📈 Grafiksel Analiz")
        layout.addWidget(tabs)

        # 3. Footer Actions
        layout.addLayout(self._create_footer_actions())

    def _create_table_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        desc = QLabel(
            "Farklı düğüm sayılarında (Node Count) algoritmaların performans özeti."
        )
        desc.setStyleSheet("color: #94a3b8; margin-bottom: 5px;")
        layout.addWidget(desc)

        self.table = QTableWidget()
        columns = [
            "Düğüm", 
            "GA Maliyet", "GA Süre", 
            "ACO Maliyet", "ACO Süre", 
            "PSO Maliyet", "PSO Süre",
            "SA Maliyet", "SA Süre",
            "QL Maliyet", "QL Süre",
            "SARSA Maliyet", "SARSA Süre"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Improve Table Readability
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive) # Allow resize
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents) 
        # ResizeToContents is better but can be slow. Let's try Stretch for small col count, or Interactive.
        # Given many columns, horizontal scroll is needed.
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("alternate-background-color: #1a2233;")
        
        self._populate_table()
        layout.addWidget(self.table)
        
        return widget

    def _create_charts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        if not MATPLOTLIB_AVAILABLE:
            error = QLabel("Matplotlib kütüphanesi bulunamadı. Grafik çizilemiyor.")
            error.setStyleSheet("color: #ef4444; font-size: 16px; font-weight: bold;")
            error.setAlignment(Qt.AlignCenter)
            layout.addWidget(error)
            return widget

        # Create Figures
        # Row 1: Cost Chart
        # Row 2: Time Chart
        
        # Chart 1: Ortalama Maliyet
        chart1_frame = QFrame()
        chart1_frame.setStyleSheet("background-color: #1e293b; border-radius: 8px;")
        vbox1 = QVBoxLayout(chart1_frame)
        
        lbl1 = QLabel("Ortalama Maliyet Karşılaştırması (Düşük Daha İyi)")
        lbl1.setStyleSheet("color: #e2e8f0; font-weight: bold; margin-bottom: 5px;")
        lbl1.setAlignment(Qt.AlignCenter)
        vbox1.addWidget(lbl1)
        
        fig1 = Figure(figsize=(5, 3), facecolor='#1e293b')
        canvas1 = FigureCanvas(fig1)
        canvas1.setStyleSheet("background: transparent;")
        self._plot_metric(fig1, 'cost', 'Maliyet (Normalize)')
        vbox1.addWidget(canvas1)
        
        layout.addWidget(chart1_frame)
        
        # Chart 2: Ortalama Süre
        chart2_frame = QFrame()
        chart2_frame.setStyleSheet("background-color: #1e293b; border-radius: 8px; margin-top: 10px;")
        vbox2 = QVBoxLayout(chart2_frame)
        
        lbl2 = QLabel("Ortalama Çalışma Süresi Karşılaştırması (ms)")
        lbl2.setStyleSheet("color: #e2e8f0; font-weight: bold; margin-bottom: 5px;")
        lbl2.setAlignment(Qt.AlignCenter)
        vbox2.addWidget(lbl2)
        
        fig2 = Figure(figsize=(5, 3), facecolor='#1e293b')
        canvas2 = FigureCanvas(fig2)
        canvas2.setStyleSheet("background: transparent;")
        self._plot_metric(fig2, 'time', 'Süre (ms)')
        vbox2.addWidget(canvas2)
        
        layout.addWidget(chart2_frame)
        
        return widget

    def _plot_metric(self, figure, metric_key, y_label):
        ax = figure.add_subplot(111, facecolor='#1e293b')
        
        # Extract Data
        # X-axis: Nodes
        nodes = [d.get('nodes', 0) for d in self.results]
        
        algorithms = {
            'GA': '#3b82f6',   # Blue
            'ACO': '#a855f7',  # Purple
            'PSO': '#f97316',  # Orange
            'SA': '#10b981',   # Emerald
            'QL': '#ec4899',   # Pink
            'SARSA': '#eab308' # Yellow
        }
        
        for alg, color in algorithms.items():
            y_values = []
            for d in self.results:
                y_values.append(d.get(alg, {}).get(metric_key, 0))
            
            ax.plot(nodes, y_values, marker='o', label=alg, color=color, linewidth=2)

        # Styling
        ax.set_xlabel('Düğüm Sayısı', color='#94a3b8')
        ax.set_ylabel(y_label, color='#94a3b8')
        ax.tick_params(colors='#64748b')
        ax.grid(True, alpha=0.1, color='#FFFFFF', linestyle='--')
        ax.spines['bottom'].set_color('#334155')
        ax.spines['top'].set_color('#334155')
        ax.spines['left'].set_color('#334155')
        ax.spines['right'].set_color('#334155')
        
        leg = ax.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0')
        figure.tight_layout()

    def _create_footer_actions(self):
        footer_layout = QHBoxLayout()
        
        # EXPORT BUTTONS
        btn_json = QPushButton("💾 JSON Kaydet")
        btn_json.setCursor(Qt.PointingHandCursor)
        btn_json.setStyleSheet(self._action_btn_style("#3b82f6"))
        btn_json.clicked.connect(self._on_export_json)
        
        btn_csv = QPushButton("📊 CSV Kaydet") 
        btn_csv.setCursor(Qt.PointingHandCursor)
        btn_csv.setStyleSheet(self._action_btn_style("#10b981"))
        btn_csv.clicked.connect(self._on_export_csv)
        
        footer_layout.addWidget(btn_json)
        footer_layout.addWidget(btn_csv)
        footer_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                padding: 8px 25px;
                border-radius: 6px;
                font-weight: bold;
                border: 1px solid #475569;
            }
            QPushButton:hover {
                background-color: #475569;
                border: 1px solid #94a3b8;
            }
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        return footer_layout

    def _action_btn_style(self, color):
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {color};
                padding: 8px 16px;
                border: 1px solid {color};
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: white;
            }}
        """

    def _populate_table(self):
        self.table.setRowCount(len(self.results))
        for i, row_data in enumerate(self.results):
            col = 0
            self._set_cell(i, col, str(row_data.get('nodes', '-'))); col += 1
            
            for alg_key in ['GA', 'ACO', 'PSO', 'SA', 'QL', 'SARSA']:
                data = row_data.get(alg_key, {})
                cost = data.get('cost', 0)
                time_val = data.get('time', 0)
                
                self._set_cell(i, col, f"{cost:.2f}"); col += 1
                self._set_cell(i, col, f"{time_val:.2f}"); col += 1

    def _set_cell(self, row, col, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)

    def _on_export_json(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "JSON Olarak Kaydet", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Başarılı", "Sonuçlar JSON olarak kaydedildi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme başarısız: {str(e)}")

    def _on_export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "CSV Olarak Kaydet", "", "CSV Files (*.csv)"
        )
        if filename:
            try:
                # utf-8-sig for Turkish characters in Excel
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    # Create header
                    header = ["Düğüm Sayısı"]
                    algorithms = ['GA', 'ACO', 'PSO', 'SA', 'QL', 'SARSA']
                    for alg in algorithms:
                        header.extend([f"{alg} Maliyet", f"{alg} Süre (ms)"])
                    writer.writerow(header)
                    
                    # Data
                    for row_data in self.results:
                        row = [row_data.get('nodes', '-')]
                        for alg in algorithms:
                            data = row_data.get(alg, {})
                            row.append(f"{data.get('cost', 0):.4f}")
                            row.append(f"{data.get('time', 0):.2f}")
                        writer.writerow(row)
                        
                QMessageBox.information(self, "Başarılı", "Sonuçlar CSV olarak kaydedildi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme başarısız: {str(e)}")
