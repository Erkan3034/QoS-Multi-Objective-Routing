
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QTabWidget, QWidget, 
    QFrame, QPushButton, QScrollArea
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

class TestResultsDialog(QDialog):
    """
    Gelişmiş Deney Sonuçları Penceresi
    - Özet İstatistikler (Cards)
    - Karşılaştırma Tablosu
    - Başarısızlık Raporu
    """
    
    def __init__(self, result_data: dict, parent=None):
        super().__init__(parent)
        self.result_data = result_data
        self.setWindowTitle("Detaylı Deney Sonuçları")
        self.setMinimumSize(1000, 700)
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
            QLabel {
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
            QScrollBar:vertical {
                background: #0f172a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 6px;
            }
        """)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header
        header = QLabel("Deney Sonuç Raporu")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(header)

        # 2. Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_summary_tab(), "📊 Özet")
        tabs.addTab(self._create_comparison_table(), "📈 Algoritma Karşılaştırması")
        tabs.addTab(self._create_failures_tab(), "⚠️ Başarısızlıklar")
        
        layout.addWidget(tabs)
        
        # 3. Footer Actions
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                padding: 8px 20px;
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

    def _create_summary_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Top Stats Row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)
        
        timestamp = self.result_data.get("timestamp", "-")[:19].replace("T", " ")
        
        self._add_stat_card(stats_layout, "Test Sayısı", str(self.result_data.get("n_test_cases", 0)), "#3b82f6")
        self._add_stat_card(stats_layout, "Toplam Süre", f"{self.result_data.get('total_time_sec', 0)}s", "#10b981")
        
        failure_count = self.result_data.get("failure_report", {}).get("total_failures", 0)
        color = "#ef4444" if failure_count > 0 else "#10b981"
        self._add_stat_card(stats_layout, "Başarısız Test", str(failure_count), color)
        
        layout.addLayout(stats_layout)
        
        # Best Algorithm Info
        comparison = self.result_data.get("comparison_table", [])
        if comparison:
            best_algo = comparison[0] # Sorted by cost
            
            info_frame = QFrame()
            info_frame.setStyleSheet("background-color: #0f172a; border-radius: 8px; padding: 15px;")
            info_layout = QVBoxLayout(info_frame)
            
            title = QLabel("🏆 En İyi Performans")
            title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fbbf24; margin-bottom: 10px;")
            info_layout.addWidget(title)
            
            detail = QLabel(
                f"Algoritma: <b>{best_algo['algorithm']}</b><br>"
                f"Ortalama Maliyet: {best_algo['overall_avg_cost']:.4f}<br>"
                f"Başarı Oranı: %{best_algo['success_rate']*100:.1f}"
            )
            detail.setStyleSheet("font-size: 14px; line-height: 1.5;")
            info_layout.addWidget(detail)
            
            layout.addWidget(info_frame)
            
        layout.addStretch()
        return widget

    def _add_stat_card(self, layout, title, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #0f172a;
                border: 1px solid {color};
                border-radius: 8px;
            }}
        """)
        vbox = QVBoxLayout(frame)
        
        lbl_value = QLabel(value)
        lbl_value.setAlignment(Qt.AlignCenter)
        lbl_value.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {color};")
        
        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("color: #94a3b8; font-size: 14px;")
        
        vbox.addWidget(lbl_value)
        vbox.addWidget(lbl_title)
        layout.addWidget(frame)

    def _create_comparison_table(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Algoritma", "Başarı (%)", "Bant Genişliği (%)", 
            "Ort. Maliyet", "Ort. Süre (ms)", "En İyi"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QTableWidget.NoSelection)
        
        data = self.result_data.get("comparison_table", [])
        table.setRowCount(len(data))
        
        for i, row in enumerate(data):
            self._set_cell(table, i, 0, row['algorithm'])
            self._set_cell(table, i, 1, f"%{row['success_rate']*100:.1f}")
            self._set_cell(table, i, 2, f"%{row['bandwidth_satisfaction_rate']*100:.1f}")
            self._set_cell(table, i, 3, f"{row['overall_avg_cost']:.4f}")
            self._set_cell(table, i, 4, f"{row['overall_avg_time_ms']:.2f}")
            self._set_cell(table, i, 5, f"{row['best_cost']:.4f}")
            
        layout.addWidget(table)
        return widget

    def _set_cell(self, table, row, col, val):
        item = QTableWidgetItem(str(val))
        item.setTextAlignment(Qt.AlignCenter)
        table.setItem(row, col, item)

    def _create_failures_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        failures = self.result_data.get("failure_report", {}).get("details", [])
        
        if not failures:
            lbl = QLabel("Harika! Hiç başarısız test yok. 🎉")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 18px; color: #10b981;")
            layout.addWidget(lbl)
            return widget

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        
        for fail in failures:
            frame = QFrame()
            frame.setStyleSheet("""
                QFrame {
                    background-color: #0f172a;
                    border-left: 4px solid #ef4444;
                    border-radius: 4px;
                    padding: 10px;
                }
            """)
            vbox = QVBoxLayout(frame)
            
            title = QLabel(f"{fail['algorithm']} - Test #{fail['test_case_id']}")
            title.setStyleSheet("font-weight: bold; color: #ef4444; font-size: 14px;")
            
            reason = QLabel(f"Neden: {fail['failure_reason']}")
            reason.setStyleSheet("color: #e2e8f0;")
            
            detail_text = fail.get('details')
            if detail_text:
                detail = QLabel(f"Detay: {detail_text}")
                detail.setStyleSheet("color: #94a3b8; font-style: italic;")
                vbox.addWidget(detail)
            
            info = QLabel(f"Kaynak: {fail['source']} -> Hedef: {fail['destination']} | Gereksinim: {fail['bandwidth_requirement']} Mbps")
            info.setStyleSheet("color: #64748b; font-size: 12px;")
            
            vbox.addWidget(title)
            vbox.addWidget(reason)
            vbox.addWidget(info)
            content_layout.addWidget(frame)
            
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget
