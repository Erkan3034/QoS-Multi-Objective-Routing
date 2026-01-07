from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QGridLayout,
    QLineEdit, QComboBox, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QKeyEvent

class ScenariosDialog(QDialog):
    """
    Önceden tanımlanmış test senaryolarını listeleyen profesyonel pencere.
    """
    def __init__(self, scenarios: list, parent=None):
        super().__init__(parent)
        self.scenarios = scenarios
        self.filtered_scenarios = scenarios.copy()
        self.is_fullscreen = False
        self.original_geometry = None
        self.setWindowTitle("Test Senaryoları Listesi")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QTableWidget {
                background-color: #1e293b;
                gridline-color: #334155;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
                selection-background-color: #334155;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #1e293b;
            }
            QTableWidget::item:selected {
                background-color: #334155;
                color: #38bdf8;
            }
            QTableWidget::item:hover {
                background-color: #1e293b;
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: #94a3b8;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #334155;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QScrollBar:vertical {
                background: #0f172a;
                width: 14px;
                border-radius: 7px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background: #0f172a;
                height: 14px;
                border-radius: 7px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background: #475569;
                border-radius: 7px;
                min-width: 30px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #64748b;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header Section
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(12)
        
        # Title Row with Fullscreen Button
        title_row = QHBoxLayout()
        icon = QLabel("📋")
        icon.setStyleSheet("color: #a855f7; font-size: 32px;")
        title = QLabel("Test Senaryoları")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #a855f7;")
        title_row.addWidget(icon)
        title_row.addWidget(title)
        title_row.addStretch()
        
        # Fullscreen Toggle Button
        self.btn_fullscreen = QPushButton("⛶")
        self.btn_fullscreen.setToolTip("Tam Ekran (F11)")
        self.btn_fullscreen.setCursor(Qt.PointingHandCursor)
        self.btn_fullscreen.setMinimumSize(40, 40)
        self.btn_fullscreen.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #94a3b8;
                border: 1px solid #475569;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #475569;
                color: #e2e8f0;
                border-color: #64748b;
            }
            QPushButton:pressed {
                background-color: #1e293b;
            }
        """)
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        title_row.addWidget(self.btn_fullscreen)
        
        header_layout.addLayout(title_row)
        
        # Description
        desc = QLabel(
            "Sistem tarafından otomatik oluşturulmuş test senaryoları. "
            "Her senaryo kaynak (S), hedef (D), bant genişliği (B) ve ağırlık (W) parametrelerini içerir."
        )
        desc.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.5;")
        desc.setWordWrap(True)
        header_layout.addWidget(desc)
        
        # Stats Cards - Enhanced with more details
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        
        # Calculate statistics
        unique_sources = len(set(
            getattr(s, 'source', None) or s.get('source', 0) 
            for s in self.scenarios
        ))
        unique_dests = len(set(
            getattr(s, 'destination', None) or s.get('destination', 0) 
            for s in self.scenarios
        ))
        
        # Bandwidth statistics
        bandwidths = [
            getattr(s, 'bandwidth_requirement', None) or s.get('bandwidth_requirement', 0)
            for s in self.scenarios
        ]
        min_bw = min(bandwidths) if bandwidths else 0
        max_bw = max(bandwidths) if bandwidths else 0
        avg_bw = sum(bandwidths) / len(bandwidths) if bandwidths else 0
        
        # Weight statistics
        weights_list = [
            getattr(s, 'weights', {}) or s.get('weights', {})
            for s in self.scenarios
        ]
        avg_delay_w = sum(w.get('delay', 0.33) for w in weights_list) / len(weights_list) if weights_list else 0.33
        avg_rel_w = sum(w.get('reliability', 0.33) for w in weights_list) / len(weights_list) if weights_list else 0.33
        avg_res_w = sum(w.get('resource', 0.34) for w in weights_list) / len(weights_list) if weights_list else 0.34
        
        total_card = self._create_stat_card("Toplam Senaryo", str(len(self.scenarios)), "#a855f7")
        stats_layout.addWidget(total_card)
        
        sources_card = self._create_stat_card("Farklı Kaynak", str(unique_sources), "#3b82f6")
        stats_layout.addWidget(sources_card)
        
        dests_card = self._create_stat_card("Farklı Hedef", str(unique_dests), "#22c55e")
        stats_layout.addWidget(dests_card)
        
        bw_range_card = self._create_stat_card("Bant Aralığı", f"{min_bw}-{max_bw}", "#f59e0b")
        stats_layout.addWidget(bw_range_card)
        
        avg_bw_card = self._create_stat_card("Ort. Bant", f"{int(avg_bw)}", "#ec4899")
        stats_layout.addWidget(avg_bw_card)
        
        stats_layout.addStretch()
        header_layout.addLayout(stats_layout)
        
        # Additional Info Row
        info_row = QHBoxLayout()
        info_row.setSpacing(16)
        
        weights_info = QLabel(
            f"📊 Ortalama Ağırlıklar: "
            f"Gecikme {avg_delay_w:.2f} | "
            f"Güvenilirlik {avg_rel_w:.2f} | "
            f"Kaynak {avg_res_w:.2f}"
        )
        weights_info.setStyleSheet("color: #64748b; font-size: 12px; padding: 8px; background-color: #0f172a; border-radius: 6px;")
        info_row.addWidget(weights_info)
        
        info_row.addStretch()
        header_layout.addLayout(info_row)
        
        layout.addWidget(header_frame)

        # Filter Section
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(12)
        
        filter_label = QLabel("🔍 Filtrele:")
        filter_label.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600;")
        filter_layout.addWidget(filter_label)
        
        # Search by ID/Source/Dest
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ID, Kaynak veya Hedef ara...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #a855f7;
            }
        """)
        self.search_input.textChanged.connect(self._filter_table)
        filter_layout.addWidget(self.search_input, 2)
        
        # Filter by Bandwidth
        bw_label = QLabel("Bant Genişliği:")
        bw_label.setStyleSheet("color: #94a3b8; font-size: 13px;")
        filter_layout.addWidget(bw_label)
        
        self.bw_filter = QComboBox()
        self.bw_filter.addItems(["Tümü", "0-100 Mbps", "100-500 Mbps", "500-1000 Mbps", "1000+ Mbps"])
        self.bw_filter.setStyleSheet("""
            QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e2e8f0;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #475569;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                border: 1px solid #334155;
                selection-background-color: #334155;
                color: #e2e8f0;
            }
        """)
        self.bw_filter.currentTextChanged.connect(self._filter_table)
        filter_layout.addWidget(self.bw_filter)
        
        # Clear filter button
        clear_btn = QPushButton("Temizle")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #e2e8f0;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """)
        clear_btn.clicked.connect(self._clear_filters)
        filter_layout.addWidget(clear_btn)
        
        layout.addWidget(filter_frame)
        
        # Table Section
        table_header = QHBoxLayout()
        table_label = QLabel("Senaryo Detayları")
        table_label.setStyleSheet("color: #e2e8f0; font-size: 16px; font-weight: 600; margin-top: 8px;")
        table_header.addWidget(table_label)
        table_header.addStretch()
        
        # Row count label
        self.row_count_label = QLabel(f"Gösterilen: {len(self.scenarios)}")
        self.row_count_label.setStyleSheet("color: #64748b; font-size: 12px;")
        table_header.addWidget(self.row_count_label)
        
        layout.addLayout(table_header)
        
        self.table = QTableWidget()
        columns = ["ID", "Kaynak (S)", "Hedef (D)", "Bant Genişliği (Mbps)", "Ağırlıklar (D, R, C)"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Better column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID - auto
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Source - auto
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Dest - auto
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Bandwidth - auto
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Weights - stretch
        
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Set row height
        self.table.verticalHeader().setDefaultSectionSize(42)
        
        self._populate_table()
        layout.addWidget(self.table, 1)  # Stretch factor

        # Footer
        footer_layout = QHBoxLayout()
        
        info_label = QLabel(f"💡 Toplam {len(self.scenarios)} senaryo | Filtrelenmiş: {len(self.filtered_scenarios)}")
        info_label.setStyleSheet("color: #64748b; font-size: 12px;")
        footer_layout.addWidget(info_label)
        
        footer_layout.addStretch()
        
        # Export button (optional, for future use)
        export_btn = QPushButton("📥 Dışa Aktar")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setMinimumWidth(120)
        export_btn.setMinimumHeight(40)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #e2e8f0;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton:pressed {
                background-color: #1e293b;
            }
        """)
        export_btn.clicked.connect(self._on_export_scenarios)
        footer_layout.addWidget(export_btn)
        
        close_btn = QPushButton("Kapat")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setMinimumWidth(120)
        close_btn.setMinimumHeight(40)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: white;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
            QPushButton:pressed {
                background-color: #1e293b;
            }
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def _toggle_fullscreen(self):
        """Tam ekran modunu aç/kapat."""
        if self.is_fullscreen:
            self.showNormal()
            if self.original_geometry:
                self.setGeometry(self.original_geometry)
            self.btn_fullscreen.setText("⛶")
            self.btn_fullscreen.setToolTip("Tam Ekran (F11)")
            self.is_fullscreen = False
        else:
            self.original_geometry = self.geometry()
            self.showFullScreen()
            self.btn_fullscreen.setText("⛶")
            self.btn_fullscreen.setToolTip("Tam Ekrandan Çık (F11 veya ESC)")
            self.is_fullscreen = True
    
    def _filter_table(self):
        """Tabloyu filtrele."""
        search_text = self.search_input.text().lower().strip()
        bw_filter = self.bw_filter.currentText()
        
        self.filtered_scenarios = []
        
        for scenario in self.scenarios:
            # Get scenario data
            c_id = str(getattr(scenario, 'id', None) or scenario.get('id', ''))
            src = str(getattr(scenario, 'source', None) or scenario.get('source', ''))
            dst = str(getattr(scenario, 'destination', None) or scenario.get('destination', ''))
            bw = getattr(scenario, 'bandwidth_requirement', None) or scenario.get('bandwidth_requirement', 0)
            
            # Search filter
            matches_search = (
                not search_text or
                search_text in c_id.lower() or
                search_text in src.lower() or
                search_text in dst.lower()
            )
            
            # Bandwidth filter
            matches_bw = True
            if bw_filter != "Tümü":
                if bw_filter == "0-100 Mbps":
                    matches_bw = 0 <= bw < 100
                elif bw_filter == "100-500 Mbps":
                    matches_bw = 100 <= bw < 500
                elif bw_filter == "500-1000 Mbps":
                    matches_bw = 500 <= bw < 1000
                elif bw_filter == "1000+ Mbps":
                    matches_bw = bw >= 1000
            
            if matches_search and matches_bw:
                self.filtered_scenarios.append(scenario)
        
        # Update table
        self._populate_table()
        
        # Update row count
        self.row_count_label.setText(f"Gösterilen: {len(self.filtered_scenarios)}")
    
    def _clear_filters(self):
        """Filtreleri temizle."""
        self.search_input.clear()
        self.bw_filter.setCurrentIndex(0)
        self.filtered_scenarios = self.scenarios.copy()
        self._populate_table()
        self.row_count_label.setText(f"Gösterilen: {len(self.filtered_scenarios)}")
    
    def keyPressEvent(self, event: QKeyEvent):
        """Klavye kısayolları."""
        if event.key() == Qt.Key_F11:
            self._toggle_fullscreen()
        elif event.key() == Qt.Key_Escape and self.is_fullscreen:
            self._toggle_fullscreen()
        else:
            super().keyPressEvent(event)
    
    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """İstatistik kartı oluşturur."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #0f172a;
                border: 1px solid {color}40;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(4)
        card_layout.setContentsMargins(12, 8, 12, 8)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(value_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(title_label)
        
        return card

    def _populate_table(self):
        self.table.setRowCount(len(self.filtered_scenarios))
        for i, case in enumerate(self.filtered_scenarios):
            # case is expected to be a TestCase object or dict
            # Using getattr/get for flexibility
            
            c_id = getattr(case, 'id', None) or case.get('id')
            src = getattr(case, 'source', None) or case.get('source')
            dst = getattr(case, 'destination', None) or case.get('destination')
            bw = getattr(case, 'bandwidth_requirement', None) or case.get('bandwidth_requirement')
            weights = getattr(case, 'weights', {}) or case.get('weights', {})
            
            # Format weights more professionally
            delay_w = weights.get('delay', 0.33)
            rel_w = weights.get('reliability', 0.33)
            res_w = weights.get('resource', 0.34)
            w_str = f"D:{delay_w:.2f} | R:{rel_w:.2f} | C:{res_w:.2f}"
            
            # Set cells with better formatting
            self._set_cell(i, 0, f"#{c_id}", is_bold=True, color="#a855f7")
            self._set_cell(i, 1, str(src), color="#3b82f6")
            self._set_cell(i, 2, str(dst), color="#22c55e")
            self._set_cell(i, 3, f"{bw} Mbps", color="#f59e0b")
            self._set_cell(i, 4, w_str, color="#94a3b8")

    def _set_cell(self, row, col, text, is_bold=False, color=None):
        """Hücre oluşturur ve stil uygular."""
        item = QTableWidgetItem(text)
        
        # Alignment
        if col == 0:  # ID
            item.setTextAlignment(Qt.AlignCenter)
        elif col in [1, 2]:  # Source, Dest
            item.setTextAlignment(Qt.AlignCenter)
        elif col == 3:  # Bandwidth
            item.setTextAlignment(Qt.AlignCenter)
        else:  # Weights
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Font weight
        if is_bold:
            font = QFont()
            font.setBold(True)
            item.setFont(font)
        
        # Color
        if color:
            item.setForeground(QColor(color))
        
        self.table.setItem(row, col, item)

    def _on_export_scenarios(self):
        """Test senaryolarını CSV olarak dışa aktar."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Senaryoları Dışa Aktar", "test_senaryolari.csv", "CSV Files (*.csv)"
        )
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    
                    # Header with statistics
                    writer.writerow(["=== TEST SENARYOLARI ==="])
                    writer.writerow(["Toplam Senaryo", len(self.scenarios)])
                    writer.writerow(["Filtrelenen", len(self.filtered_scenarios)])
                    writer.writerow([])
                    
                    # Column headers
                    writer.writerow([
                        "ID", "Kaynak (S)", "Hedef (D)", "Bant Genişliği (Mbps)",
                        "Gecikme Ağırlığı", "Güvenilirlik Ağırlığı", "Kaynak Ağırlığı"
                    ])
                    
                    # Data rows (filtered scenarios)
                    for scenario in self.filtered_scenarios:
                        c_id = getattr(scenario, 'id', None) or scenario.get('id', '')
                        src = getattr(scenario, 'source', None) or scenario.get('source', '')
                        dst = getattr(scenario, 'destination', None) or scenario.get('destination', '')
                        bw = getattr(scenario, 'bandwidth_requirement', None) or scenario.get('bandwidth_requirement', 0)
                        weights = getattr(scenario, 'weights', {}) or scenario.get('weights', {})
                        
                        writer.writerow([
                            c_id,
                            src,
                            dst,
                            bw,
                            f"{weights.get('delay', 0.33):.2f}",
                            f"{weights.get('reliability', 0.33):.2f}",
                            f"{weights.get('resource', 0.34):.2f}"
                        ])
                
                QMessageBox.information(
                    self, 
                    "Başarılı", 
                    f"Test senaryoları CSV olarak kaydedildi!\n\n"
                    f"Kayıt: {len(self.filtered_scenarios)} senaryo"
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme başarısız: {str(e)}")
