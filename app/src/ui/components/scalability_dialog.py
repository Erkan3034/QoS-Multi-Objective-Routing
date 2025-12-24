from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QWidget
)
from PyQt5.QtCore import Qt

class ScalabilityDialog(QDialog):
    """
    Ölçeklenebilirlik analizi sonuçlarını gösteren pencere.
    """
    def __init__(self, results: list, parent=None):
        super().__init__(parent)
        self.results = results
        self.setWindowTitle("Ölçeklenebilirlik Analizi Sonuçları")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
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
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        icon = QLabel("↗")
        icon.setStyleSheet("color: #3b82f6; font-size: 24px; font-weight: bold;")
        title = QLabel("Ölçeklenebilirlik Analizi Raporu")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6;")
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        desc = QLabel(
            "Farklı düğüm sayılarında (Node Count) algoritmaların ortalama çalışma süreleri ve maliyetleri aşağıdadır.\n"
            "Düşük süre (ms) ve düşük maliyet daha iyi performansı gösterir."
        )
        desc.setStyleSheet("color: #94a3b8; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.table = QTableWidget()
        # Columns: Nodes, GA Cost, GA Time, ACO Cost, ACO Time, PSO Cost, PSO Time
        columns = [
            "Düğüm Sayısı", 
            "GA Maliyet", "GA Süre (ms)", 
            "ACO Maliyet", "ACO Süre (ms)", 
            "PSO Maliyet", "PSO Süre (ms)"
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("alternate-background-color: #1a2233;")
        
        self._populate_table()
        layout.addWidget(self.table)

        # Footer
        footer_layout = QHBoxLayout()
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
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)

    def _populate_table(self):
        self.table.setRowCount(len(self.results))
        for i, row_data in enumerate(self.results):
            # row_data expected format: 
            # {'nodes': 50, 'GA': {'cost': x, 'time': y}, 'ACO': ..., 'PSO': ...}
            
            self._set_cell(i, 0, str(row_data.get('nodes', '-')))
            
            ga = row_data.get('GA', {})
            self._set_cell(i, 1, f"{ga.get('cost', 0):.2f}")
            self._set_cell(i, 2, f"{ga.get('time', 0):.2f}")
            
            aco = row_data.get('ACO', {})
            self._set_cell(i, 3, f"{aco.get('cost', 0):.2f}")
            self._set_cell(i, 4, f"{aco.get('time', 0):.2f}")
            
            pso = row_data.get('PSO', {})
            self._set_cell(i, 5, f"{pso.get('cost', 0):.2f}")
            self._set_cell(i, 6, f"{pso.get('time', 0):.2f}")

    def _set_cell(self, row, col, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)
