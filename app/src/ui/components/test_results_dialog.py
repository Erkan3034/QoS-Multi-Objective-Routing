

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QTabWidget, QWidget, 
    QFrame, QPushButton, QScrollArea, QFileDialog, QMessageBox,
    QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
import json

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

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header with fullscreen toggle
        header_layout = QHBoxLayout()
        
        header = QLabel("Deney Sonuç Raporu")
        header.setStyleSheet("font-size: 24px; font-weight: bold; color: #38bdf8;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Tam Ekran / Normal Butonu
        self.fullscreen_btn = QPushButton("⛶ Tam Ekran")
        self.fullscreen_btn.setCursor(Qt.PointingHandCursor)
        self.fullscreen_btn.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #e2e8f0;
                padding: 6px 14px;
                border-radius: 6px;
                font-size: 12px;
                border: 1px solid #475569;
            }
            QPushButton:hover {
                background-color: #475569;
                border: 1px solid #38bdf8;
            }
        """)
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        header_layout.addWidget(self.fullscreen_btn)
        
        layout.addLayout(header_layout)

        # 2. Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_summary_tab(), "📊 Özet")
        tabs.addTab(self._create_comparison_table(), "📈 Algoritma Karşılaştırması")
        tabs.addTab(self._create_scenario_details_tab(), "📋 Senaryo Detayları")
        tabs.addTab(self._create_ranking_tab(), "🏆 Ranking")
        tabs.addTab(self._create_charts_tab(), "📊 Grafikler")
        tabs.addTab(self._create_failures_tab(), "⚠️ Başarısızlıklar")
        
        layout.addWidget(tabs)
        
        # 3. Footer
        layout.addLayout(self._create_footer_actions())

    def _create_footer_actions(self):
        """Alt buton grubu (Export & Close)."""
        footer_layout = QHBoxLayout()
        
        # EXPORT BUTTONS
        btn_json = QPushButton("💾 JSON Olarak Kaydet")
        btn_json.setCursor(Qt.PointingHandCursor)
        btn_json.setStyleSheet(self._action_btn_style("#3b82f6"))
        btn_json.clicked.connect(self._on_export_json)
        
        btn_csv = QPushButton("📊 CSV Olarak Kaydet") 
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
                padding: 8px 24px;
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

    def _on_export_json(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "JSON Olarak Kaydet", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.result_data, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Başarılı", "Sonuçlar JSON olarak kaydedildi!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme başarısız: {str(e)}")

    def _on_export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "CSV Olarak Kaydet", "", "CSV Files (*.csv)"
        )
        if filename:
            try:
                import csv
                # utf-8-sig is required for Excel to properly recognize Turkish characters
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    
                    # === BÖLÜM 1: ÖZET İSTATİSTİKLER ===
                    writer.writerow(["=== ÖZET İSTATİSTİKLER ==="])
                    writer.writerow(["Test Sayısı", "Toplam Süre (s)", "Başarısız Test Sayısı", "Zaman Damgası"])
                    timestamp = self.result_data.get("timestamp", "-")
                    if timestamp and len(timestamp) > 19:
                        timestamp = timestamp[:19].replace("T", " ")
                    writer.writerow([
                        self.result_data.get("n_test_cases", 0),
                        self.result_data.get("total_time_sec", 0),
                        self.result_data.get("failure_report", {}).get("total_failures", 0),
                        timestamp
                    ])
                    
                    # En iyi algoritma bilgisi
                    comparison = self.result_data.get("comparison_table", [])
                    if comparison:
                        best = comparison[0]
                        writer.writerow([])
                        writer.writerow(["En İyi Algoritma", best['algorithm']])
                        writer.writerow(["Ortalama Maliyet", f"{best['overall_avg_cost']:.4f}"])
                        writer.writerow(["Başarı Oranı", f"%{best['success_rate']*100:.1f}"])
                    
                    # === BÖLÜM 2: Algoritma Özet Tablosu ===
                    writer.writerow([])
                    writer.writerow(["=== ALGORITMA ÖZET KARŞILAŞTIRMASI ==="])
                    writer.writerow([
                        "Algoritma", "Başarı Oranı", "Bant Genişliği Memnuniyeti", 
                        "Ortalama Maliyet", "Ortalama Süre (ms)", "En İyi Maliyet", "En İyi Seed"
                    ])
                    for row in self.result_data.get("comparison_table", []):
                        writer.writerow([
                            row['algorithm'],
                            f"{row['success_rate']:.4f}",
                            f"{row['bandwidth_satisfaction_rate']:.4f}",
                            f"{row['overall_avg_cost']:.4f}",
                            f"{row['overall_avg_time_ms']:.2f}",
                            f"{row['best_cost']:.4f}",
                            str(row.get('best_seed', '-')) if row.get('best_seed') else '-'
                        ])
                    
                    # === BÖLÜM 3: ALGORİTMA RANKING ===
                    ranking_data = self.result_data.get("ranking_summary", {})
                    if ranking_data:
                        writer.writerow([])
                        writer.writerow(["=== ALGORİTMA RANKING ==="])
                        writer.writerow(["Algoritma", "1. Sıra", "2. Sıra", "3. Sıra", "4. Sıra", "5. Sıra", "Toplam Kazanma"])
                        
                        # Kazanma sayısına göre sırala
                        sorted_ranking = sorted(
                            ranking_data.items(),
                            key=lambda x: x[1].get("1st", 0),
                            reverse=True
                        )
                        for algo_name, ranks in sorted_ranking:
                            writer.writerow([
                                algo_name,
                                ranks.get("1st", 0),
                                ranks.get("2nd", 0),
                                ranks.get("3rd", 0),
                                ranks.get("4th", 0),
                                ranks.get("5th", 0),
                                ranks.get("total_wins", 0)
                            ])
                    
                    # === BÖLÜM 4: Senaryo Bazlı Detaylar ===
                    writer.writerow([])
                    writer.writerow(["=== SENARYO BAZLI DETAYLAR ==="])
                    writer.writerow([
                        "Senaryo", "Profil", "Kaynak", "Hedef", "Bant Genişliği (Mbps)", 
                        "Algoritma", "Ort. Maliyet", "Std Sapma", "Min", "Max", 
                        "Ort. Süre (ms)", "Başarı Oranı", "Best Seed"
                    ])
                    
                    scenario_results = self.result_data.get("scenario_results", {})
                    for scenario_key, scenario in scenario_results.items():
                        for algo_name, algo_data in scenario.get("algorithms", {}).items():
                            avg_cost = algo_data.get('avg_cost')
                            writer.writerow([
                                scenario.get('id', scenario_key),
                                scenario.get('profile_name', 'Dengeli'),
                                scenario.get('source', '-'),
                                scenario.get('destination', '-'),
                                scenario.get('bandwidth', '-'),
                                algo_name,
                                f"{avg_cost:.4f}" if avg_cost else "-",
                                f"{algo_data.get('std_cost', 0):.4f}",
                                f"{algo_data.get('min_cost', 0):.4f}" if algo_data.get('min_cost') else "-",
                                f"{algo_data.get('max_cost', 0):.4f}" if algo_data.get('max_cost') else "-",
                                f"{algo_data.get('avg_time_ms', 0):.2f}",
                                f"{algo_data.get('success_rate', 0)*100:.0f}%",
                                str(algo_data.get('best_seed', '-')) if algo_data.get('best_seed') else '-'
                            ])
                    
                    # === BÖLÜM 5: BAŞARISIZ TESTLER ===
                    failures = self.result_data.get("failure_report", {}).get("details", [])
                    if failures:
                        writer.writerow([])
                        writer.writerow(["=== BAŞARISIZ TESTLER ==="])
                        writer.writerow([
                            "Algoritma", "Test ID", "Kaynak", "Hedef", 
                            "Bant Genişliği (Mbps)", "Neden", "Detay", "Seed"
                        ])
                        for fail in failures:
                            writer.writerow([
                                fail.get('algorithm', '-'),
                                fail.get('test_case_id', '-'),
                                fail.get('source', '-'),
                                fail.get('destination', '-'),
                                fail.get('bandwidth_requirement', '-'),
                                fail.get('failure_reason', '-'),
                                fail.get('details', '-'),
                                fail.get('seed_used', '-')
                            ])
                    
                QMessageBox.information(
                    self, 
                    "Başarılı", 
                    "Sonuçlar CSV olarak kaydedildi!\n\nİçerik:\n"
                    "• Özet İstatistikler\n"
                    "• Algoritma Karşılaştırması\n"
                    "• Algoritma Ranking\n"
                    "• Senaryo Detayları\n"
                    "• Başarısız Testler"
                )
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kaydetme başarısız: {str(e)}")

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
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Algoritma", "Başarı (%)", "Bant Genişliği (%)", 
            "Ort. Maliyet", "Ort. Süre (ms)", "En İyi", "Best Seed"
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
            seed_val = row.get('best_seed')
            self._set_cell(table, i, 6, str(seed_val) if seed_val else "-")
            
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
            
            # Add seed info if available
            seed_val = fail.get('seed_used')
            if seed_val:
                seed_label = QLabel(f"Seed (Reproducibility): {seed_val}")
                seed_label.setStyleSheet("color: #6ee7b7; font-size: 11px; font-family: 'Consolas', monospace;")
            
            vbox.addWidget(title)
            vbox.addWidget(reason)
            vbox.addWidget(info)
            if seed_val:
                vbox.addWidget(seed_label)
            content_layout.addWidget(frame)
            
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        return widget

    def _create_scenario_details_tab(self) -> QWidget:
        """
        Senaryo Detayları Sekmesi
        -------------------------
        Her senaryo için tüm algoritmaların detaylı karşılaştırması.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        scenario_data = self.result_data.get("scenario_results", {})
        
        if not scenario_data:
            lbl = QLabel("Senaryo bazlı veri bulunamadı.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; color: #94a3b8;")
            layout.addWidget(lbl)
            return widget
        
        # === Senaryo Seçici ===
        selector_layout = QHBoxLayout()
        selector_label = QLabel("Senaryo:")
        selector_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #94a3b8;")
        
        self.scenario_combo = QComboBox()
        self.scenario_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 8px 12px;
                min-width: 300px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #38bdf8;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b;
                color: #e2e8f0;
                selection-background-color: #334155;
            }
        """)
        
        # Dropdown'ı doldur
        self._scenario_keys = list(scenario_data.keys())
        for key in self._scenario_keys:
            s = scenario_data[key]
            profile = s.get('profile_name', 'Dengeli')
            display_text = f"#{s['id']} (S:{s['source']} → D:{s['destination']}, B:{s['bandwidth']} Mbps) [{profile}]"
            self.scenario_combo.addItem(display_text)
        
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.scenario_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # === Karşılaştırma Tablosu ===
        self.scenario_table = QTableWidget()
        self.scenario_table.setColumnCount(8)
        self.scenario_table.setHorizontalHeaderLabels([
            "Algoritma", "Ort. Maliyet", "Std Sapma", "En İyi", "En Kötü", 
            "Ort. Süre (ms)", "Başarı", "Best Seed"
        ])
        self.scenario_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scenario_table.verticalHeader().setVisible(False)
        self.scenario_table.setSelectionMode(QTableWidget.NoSelection)
        self.scenario_table.setMinimumHeight(250)
        
        layout.addWidget(self.scenario_table)
        
        # === En İyi Algoritma Bilgisi ===
        self.best_algo_label = QLabel("")
        self.best_algo_label.setStyleSheet("""
            font-size: 14px; 
            color: #fbbf24; 
            padding: 10px;
            background-color: #0f172a;
            border-radius: 6px;
        """)
        layout.addWidget(self.best_algo_label)
        
        # İlk senaryoyu yükle
        self._update_scenario_table(0)
        
        # Senaryo değişince tabloyu güncelle
        self.scenario_combo.currentIndexChanged.connect(self._update_scenario_table)
        
        layout.addStretch()
        return widget
    
    def _update_scenario_table(self, index: int):
        """Seçilen senaryoya göre tabloyu güncelle."""
        if index < 0 or index >= len(self._scenario_keys):
            return
        
        scenario_key = self._scenario_keys[index]
        scenario_data = self.result_data.get("scenario_results", {}).get(scenario_key, {})
        algorithms_data = scenario_data.get("algorithms", {})
        
        # Tabloyu temizle ve doldur
        self.scenario_table.setRowCount(len(algorithms_data))
        
        # Algoritmayı maliyet ortalamasına göre sırala
        sorted_algos = sorted(
            algorithms_data.items(),
            key=lambda x: x[1].get('avg_cost') or float('inf')
        )
        
        best_algo = None
        best_cost = float('inf')
        
        for row_idx, (algo_name, data) in enumerate(sorted_algos):
            avg_cost = data.get('avg_cost')
            std_cost = data.get('std_cost', 0)
            min_cost = data.get('min_cost')
            max_cost = data.get('max_cost')
            avg_time = data.get('avg_time_ms', 0)
            success_rate = data.get('success_rate', 0)
            best_seed = data.get('best_seed')
            
            # En iyi kontrolü
            if avg_cost is not None and avg_cost < best_cost:
                best_cost = avg_cost
                best_algo = algo_name
            
            # Hücreleri doldur
            self._set_cell(self.scenario_table, row_idx, 0, algo_name)
            self._set_cell(self.scenario_table, row_idx, 1, f"{avg_cost:.4f}" if avg_cost else "-")
            self._set_cell(self.scenario_table, row_idx, 2, f"{std_cost:.4f}")
            self._set_cell(self.scenario_table, row_idx, 3, f"{min_cost:.4f}" if min_cost else "-")
            self._set_cell(self.scenario_table, row_idx, 4, f"{max_cost:.4f}" if max_cost else "-")
            self._set_cell(self.scenario_table, row_idx, 5, f"{avg_time:.2f}")
            self._set_cell(self.scenario_table, row_idx, 6, f"%{success_rate*100:.0f}")
            self._set_cell(self.scenario_table, row_idx, 7, str(best_seed) if best_seed else "-")
            
            # İlk satırı (en iyi) vurgula
            if row_idx == 0:
                for col in range(8):
                    item = self.scenario_table.item(row_idx, col)
                    if item:
                        item.setBackground(QColor("#1e3a5f"))
        
        # En iyi algoritma bilgisi
        if best_algo:
            self.best_algo_label.setText(
                f"🏆 Bu senaryo için en iyi: {best_algo} (Min: {best_cost:.4f})"
            )
        else:
            self.best_algo_label.setText("⚠️ Başarılı sonuç bulunamadı")
    
    def _toggle_fullscreen(self):
        """Tam ekran / normal pencere arasında geçiş yap."""
        if self.isMaximized():
            self.showNormal()
            self.fullscreen_btn.setText("⛶ Tam Ekran")
        else:
            self.showMaximized()
            self.fullscreen_btn.setText("⛶ Normal")
    
    def _create_ranking_tab(self) -> QWidget:
        """
        Algoritma Ranking Sekmesi
        -------------------------
        Her senaryoda hangi algoritma kaçıncı oldu?
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        ranking_data = self.result_data.get("ranking_summary", {})
        
        if not ranking_data:
            lbl = QLabel("Ranking verisi bulunamadı.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; color: #94a3b8;")
            layout.addWidget(lbl)
            return widget
        
        # Başlık
        title = QLabel("🏆 Algoritma Sıralama Performansı")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fbbf24;")
        layout.addWidget(title)
        
        desc = QLabel("Her senaryoda algoritmaların kaçıncı sırada bitirdiğini gösterir.")
        desc.setStyleSheet("color: #94a3b8; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        # Ranking tablosu
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Algoritma", "🥇 1.", "🥈 2.", "🥉 3.", "4.", "5.", "Toplam Kazanma"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QTableWidget.NoSelection)
        
        # Kazanma sayısına göre sırala
        sorted_algos = sorted(
            ranking_data.items(),
            key=lambda x: x[1].get("1st", 0),
            reverse=True
        )
        
        table.setRowCount(len(sorted_algos))
        
        for row_idx, (algo_name, ranks) in enumerate(sorted_algos):
            self._set_cell(table, row_idx, 0, algo_name)
            self._set_cell(table, row_idx, 1, str(ranks.get("1st", 0)))
            self._set_cell(table, row_idx, 2, str(ranks.get("2nd", 0)))
            self._set_cell(table, row_idx, 3, str(ranks.get("3rd", 0)))
            self._set_cell(table, row_idx, 4, str(ranks.get("4th", 0)))
            self._set_cell(table, row_idx, 5, str(ranks.get("5th", 0)))
            self._set_cell(table, row_idx, 6, str(ranks.get("total_wins", 0)))
            
            # 1. sırayı vurgula
            if row_idx == 0:
                for col in range(7):
                    item = table.item(row_idx, col)
                    if item:
                        item.setBackground(QColor("#1e3a5f"))
        
        layout.addWidget(table)
        
        # En çok kazanan özeti
        if sorted_algos:
            winner = sorted_algos[0]
            winner_label = QLabel(f"🏆 En Çok Kazanan: {winner[0]} ({winner[1].get('1st', 0)} senaryo)")
            winner_label.setStyleSheet("""
                font-size: 16px; 
                color: #10b981; 
                padding: 15px;
                background-color: #0f172a;
                border-radius: 8px;
                font-weight: bold;
            """)
            layout.addWidget(winner_label)
        
        layout.addStretch()
        return widget
    
    def _create_charts_tab(self) -> QWidget:
        """
        Karşılaştırma Grafikleri Sekmesi
        --------------------------------
        Algoritma performanslarını görselleştirir.
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        comparison_data = self.result_data.get("comparison_table", [])
        
        if not comparison_data:
            lbl = QLabel("Grafik verisi bulunamadı.")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; color: #94a3b8;")
            layout.addWidget(lbl)
            return widget
        
        try:
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            import matplotlib.pyplot as plt
            
            # Figure oluştur (2 subplot: maliyet ve süre)
            fig = Figure(figsize=(10, 6), facecolor='#1e293b')
            canvas = FigureCanvas(fig)
            
            # Veri hazırla
            algorithms = [d['algorithm'] for d in comparison_data]
            avg_costs = [d['overall_avg_cost'] for d in comparison_data]
            avg_times = [d['overall_avg_time_ms'] for d in comparison_data]
            success_rates = [d['success_rate'] * 100 for d in comparison_data]
            
            # Renkler
            colors = ['#38bdf8', '#10b981', '#f59e0b', '#ef4444', '#a855f7']
            
            # Subplot 1: Ortalama Maliyet
            ax1 = fig.add_subplot(121)
            ax1.set_facecolor('#0f172a')
            bars1 = ax1.bar(algorithms, avg_costs, color=colors[:len(algorithms)])
            ax1.set_title('Ortalama Maliyet (Düşük = İyi)', color='white', fontsize=12)
            ax1.set_ylabel('Maliyet', color='white')
            ax1.tick_params(colors='white')
            ax1.spines['bottom'].set_color('#475569')
            ax1.spines['left'].set_color('#475569')
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            
            # Değerleri bar üzerine yaz
            for bar, cost in zip(bars1, avg_costs):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                        f'{cost:.3f}', ha='center', va='bottom', color='white', fontsize=9)
            
            # Subplot 2: Ortalama Süre
            ax2 = fig.add_subplot(122)
            ax2.set_facecolor('#0f172a')
            bars2 = ax2.bar(algorithms, avg_times, color=colors[:len(algorithms)])
            ax2.set_title('Ortalama Çalışma Süresi (ms)', color='white', fontsize=12)
            ax2.set_ylabel('Süre (ms)', color='white')
            ax2.tick_params(colors='white')
            ax2.spines['bottom'].set_color('#475569')
            ax2.spines['left'].set_color('#475569')
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            
            # Değerleri bar üzerine yaz
            for bar, time_val in zip(bars2, avg_times):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                        f'{time_val:.1f}', ha='center', va='bottom', color='white', fontsize=9)
            
            fig.tight_layout(pad=2)
            layout.addWidget(canvas)
            
        except ImportError:
            # Matplotlib yoksa metin tabanlı gösterim
            lbl = QLabel("📊 Grafik gösterimi için matplotlib gerekli.\n\nMetin tabanlı özet:")
            lbl.setStyleSheet("color: #f59e0b; font-size: 14px;")
            layout.addWidget(lbl)
            
            # Metin tabanlı özet
            for d in comparison_data:
                line = QLabel(f"• {d['algorithm']}: Maliyet={d['overall_avg_cost']:.4f}, Süre={d['overall_avg_time_ms']:.1f}ms")
                line.setStyleSheet("color: #e2e8f0;")
                layout.addWidget(line)
        
        layout.addStretch()
        return widget
