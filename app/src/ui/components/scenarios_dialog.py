from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton
)
from PyQt5.QtCore import Qt

class ScenariosDialog(QDialog):
    """
    Önceden tanımlanmış test senaryolarını listeleyen pencere.
    """
    def __init__(self, scenarios: list, parent=None):
        super().__init__(parent)
        self.scenarios = scenarios
        self.setWindowTitle("Test Senaryoları Listesi")
        self.setMinimumSize(800, 600)
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
        icon = QLabel("⏱")
        icon.setStyleSheet("color: #a855f7; font-size: 24px;")
        title = QLabel("Test Senaryoları (S, D, B)")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #a855f7;")
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        desc = QLabel(
            "Aşağıda sistem tarafından otomatik oluşturulmuş 25 adet test senaryosu listelenmektedir.\n"
            "Bu senaryolar (S: Source, D: Destination, B: Bandwidth) parametrelerini içerir."
        )
        desc.setStyleSheet("color: #94a3b8; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.table = QTableWidget()
        columns = ["ID", "Kaynak (Source)", "Hedef (Dest)", "Bant Genişliği (Mbps)", "Ağırlıklar (D, R, C)"]
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
        self.table.setRowCount(len(self.scenarios))
        for i, case in enumerate(self.scenarios):
            # case is expected to be a TestCase object or dict
            # Using getattr/get for flexibility
            
            c_id = getattr(case, 'id', None) or case.get('id')
            src = getattr(case, 'source', None) or case.get('source')
            dst = getattr(case, 'destination', None) or case.get('destination')
            bw = getattr(case, 'bandwidth_requirement', None) or case.get('bandwidth_requirement')
            weights = getattr(case, 'weights', {}) or case.get('weights', {})
            
            w_str = f"D:{weights.get('delay',0):.2f}, R:{weights.get('reliability',0):.2f}, C:{weights.get('resource',0):.2f}"
            
            self._set_cell(i, 0, str(c_id))
            self._set_cell(i, 1, str(src))
            self._set_cell(i, 2, str(dst))
            self._set_cell(i, 3, str(bw))
            self._set_cell(i, 4, w_str)

    def _set_cell(self, row, col, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)
