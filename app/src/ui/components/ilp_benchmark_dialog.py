"""
ILP Benchmark Dialog

Bu dialog ILP benchmark sonuçlarını görselleştirir:
- Optimal maliyet karşılaştırması
- Algoritma bazlı optimality gap
- Bar chart görselleştirme
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QFrame, QWidget,
    QFileDialog, QMessageBox, QTabWidget, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from typing import Dict, List
import json

# Matplotlib import
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class ILPBenchmarkDialog(QDialog):
    """ILP benchmark sonuçlarını gösteren gelişmiş pencere."""
    
    def __init__(self, data: Dict, parent=None):
        super().__init__(parent)
        self.data = data
        self.ilp_result = data.get("ilp_result")
        self.comparisons = data.get("comparisons", [])
        self.source = data.get("source", 0)
        self.destination = data.get("destination", 0)
        
        self.setWindowTitle("ILP Benchmark Sonuçları")
        self.setMinimumSize(900, 600)
        self._setup_style()
        self._setup_ui()
    
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
                background: #f59e0b;
                color: white;
            }
        """)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Başlık
        title = QLabel("🔬 ILP Benchmark Sonuçları")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)
        
        # Kaynak-Hedef bilgisi
        route_label = QLabel(f"📍 Kaynak: {self.source} → Hedef: {self.destination}")
        route_label.setStyleSheet("font-size: 14px; color: #94a3b8;")
        layout.addWidget(route_label)
        
        # İstatistik kartları
        stats_layout = self._create_stats_cards()
        layout.addLayout(stats_layout)
        
        # Tab widget
        tabs = QTabWidget()
        
        # Tab 1: Karşılaştırma Tablosu
        comparison_tab = self._create_comparison_table()
        tabs.addTab(comparison_tab, "📊 Algoritma Karşılaştırması")
        
        # Tab 2: Bar Chart
        if MATPLOTLIB_AVAILABLE and self.comparisons:
            chart_tab = self._create_chart_tab()
            tabs.addTab(chart_tab, "📈 Gap Grafiği")
        
        # Tab 3: Sonuç Analizi
        analysis_tab = self._create_analysis_tab()
        tabs.addTab(analysis_tab, "📋 Sonuç Analizi")
        
        layout.addWidget(tabs, 1)
        
        # Footer butonları
        footer = self._create_footer()
        layout.addLayout(footer)
    
    def _create_stats_cards(self):
        layout = QHBoxLayout()
        
        # ILP sonuçları
        ilp_cost = self.ilp_result.optimal_cost if self.ilp_result else 0
        ilp_time = self.ilp_result.computation_time_ms if self.ilp_result else 0
        
        # Optimal bulan algoritma sayısı
        optimal_count = sum(1 for c in self.comparisons if c.get("is_optimal", False))
        
        # Ortalama gap
        gaps = [c.get("optimality_gap_percent", 0) for c in self.comparisons]
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        
        cards_data = [
            ("ILP Optimal Maliyet", f"{ilp_cost:.4f}", "#f59e0b"),
            ("ILP Süresi", f"{ilp_time:.1f} ms", "#8b5cf6"),
            ("Optimal Algoritma", str(optimal_count), "#10b981"),
            ("Ort. Gap", f"{avg_gap:.2f}%", "#3b82f6"),
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
            val_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {color};")
            val_label.setAlignment(Qt.AlignCenter)
            
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
            title_label.setAlignment(Qt.AlignCenter)
            
            card_layout.addWidget(val_label)
            card_layout.addWidget(title_label)
            layout.addWidget(card)
        
        return layout
    
    def _create_comparison_table(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Algoritma", "Maliyet", "ILP Gap", "Optimal?", "Durum"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        
        # Verileri ekle
        sorted_comps = sorted(self.comparisons, key=lambda x: x.get("optimality_gap_percent", 100))
        table.setRowCount(len(sorted_comps))
        
        for i, comp in enumerate(sorted_comps):
            algo_name = comp.get("algorithm", "Unknown")
            algo_cost = comp.get("algorithm_cost", 0)
            gap = comp.get("optimality_gap_percent", 0)
            is_optimal = comp.get("is_optimal", False)
            
            table.setItem(i, 0, QTableWidgetItem(algo_name))
            table.setItem(i, 1, QTableWidgetItem(f"{algo_cost:.4f}"))
            
            gap_item = QTableWidgetItem(f"{gap:.2f}%")
            if gap < 1:
                gap_item.setBackground(QColor("#10b98130"))
            elif gap < 5:
                gap_item.setBackground(QColor("#f59e0b30"))
            else:
                gap_item.setBackground(QColor("#ef444430"))
            table.setItem(i, 2, gap_item)
            
            optimal_item = QTableWidgetItem("✅ Evet" if is_optimal else "❌ Hayır")
            table.setItem(i, 3, optimal_item)
            
            if is_optimal:
                status = "🏆 Optimal"
            elif gap < 5:
                status = "👍 İyi"
            elif gap < 15:
                status = "📊 Orta"
            else:
                status = "⚠️ Düşük"
            table.setItem(i, 4, QTableWidgetItem(status))
        
        layout.addWidget(table)
        return widget
    
    def _create_chart_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        fig = Figure(figsize=(10, 5), facecolor='#1e293b')
        canvas = FigureCanvas(fig)
        
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0f172a')
        
        # Algoritma bazlı gap bar chart
        sorted_comps = sorted(self.comparisons, key=lambda x: x.get("optimality_gap_percent", 100))
        
        algorithms = [c.get("algorithm", "?") for c in sorted_comps]
        gaps = [c.get("optimality_gap_percent", 0) for c in sorted_comps]
        
        # Renkleri gap'e göre belirle
        colors = []
        for g in gaps:
            if g < 1:
                colors.append('#10b981')  # Yeşil
            elif g < 5:
                colors.append('#f59e0b')  # Turuncu
            else:
                colors.append('#ef4444')  # Kırmızı
        
        bars = ax.barh(algorithms, gaps, color=colors, edgecolor='white', linewidth=0.5)
        
        # Değerleri bar'ların yanına yaz
        for bar, gap in zip(bars, gaps):
            width = bar.get_width()
            ax.text(width + 0.2, bar.get_y() + bar.get_height()/2, 
                   f'{gap:.2f}%', va='center', color='#e2e8f0', fontsize=10)
        
        ax.set_xlabel('Optimality Gap (%)', color='#e2e8f0', fontsize=12)
        ax.set_title('Algoritma Karşılaştırması - ILP Gap', 
                    color='#f1f5f9', fontsize=14, fontweight='bold')
        ax.tick_params(colors='#94a3b8')
        ax.grid(True, alpha=0.2, color='#475569', axis='x')
        
        for spine in ax.spines.values():
            spine.set_color('#334155')
        
        # ILP optimal çizgisi
        ax.axvline(x=0, color='#10b981', linestyle='--', linewidth=2, label='ILP Optimal')
        
        fig.tight_layout()
        layout.addWidget(canvas)
        
        return widget
    
    def _create_analysis_tab(self):
        """Sonuç analizi tab'ı - gap değerlerini açıklar."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Analiz başlığı
        header = QLabel("📊 Benchmark Sonuç Analizi")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(header)
        
        # Gap açıklaması
        gap_explanation = QFrame()
        gap_explanation.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        gap_layout = QVBoxLayout(gap_explanation)
        
        gap_title = QLabel("📈 Gap (Optimality Gap) Nedir?")
        gap_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #f59e0b;")
        gap_layout.addWidget(gap_title)
        
        gap_text = QLabel(
            "Gap = ((Algoritma Maliyeti - ILP Maliyeti) / ILP Maliyeti) × 100%\n\n"
            "• Pozitif Gap: Algoritma, ILP'den daha KÖTÜ çözüm buldu\n"
            "• Negatif Gap: Algoritma, ILP'den daha İYİ çözüm buldu\n"
            "• Sıfır Gap: Algoritma, ILP ile aynı çözümü buldu"
        )
        gap_text.setWordWrap(True)
        gap_text.setStyleSheet("color: #cbd5e1; line-height: 1.5;")
        gap_layout.addWidget(gap_text)
        
        layout.addWidget(gap_explanation)
        
        # Dinamik sonuç analizi
        analysis_frame = QFrame()
        analysis_frame.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid #10b981;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        analysis_layout = QVBoxLayout(analysis_frame)
        
        analysis_title = QLabel("🎯 Bu Test Sonuçları:")
        analysis_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #10b981;")
        analysis_layout.addWidget(analysis_title)
        
        # Sonuçları analiz et
        analysis_lines = []
        
        if self.comparisons:
            sorted_comps = sorted(self.comparisons, key=lambda x: x.get("optimality_gap_percent", 0))
            
            # ILP maliyet
            ilp_cost = self.ilp_result.optimal_cost if self.ilp_result else 0
            analysis_lines.append(f"• ILP Referans Maliyet: {ilp_cost:.4f}")
            analysis_lines.append("")
            
            better_than_ilp = [c for c in self.comparisons if c.get("optimality_gap_percent", 0) < 0]
            equal_to_ilp = [c for c in self.comparisons if abs(c.get("optimality_gap_percent", 0)) < 0.01]
            worse_than_ilp = [c for c in self.comparisons if c.get("optimality_gap_percent", 0) > 0]
            
            if better_than_ilp:
                analysis_lines.append("✅ ILP'den DAHA İYİ bulan algoritmalar:")
                for c in sorted(better_than_ilp, key=lambda x: x.get("optimality_gap_percent", 0)):
                    gap = c.get("optimality_gap_percent", 0)
                    analysis_lines.append(f"   • {c['algorithm']}: {abs(gap):.2f}% daha iyi")
                analysis_lines.append("")
            
            if equal_to_ilp:
                analysis_lines.append("🎯 ILP ile AYNI sonucu bulan:")
                for c in equal_to_ilp:
                    analysis_lines.append(f"   • {c['algorithm']}")
                analysis_lines.append("")
            
            if worse_than_ilp:
                analysis_lines.append("⚠️ ILP'den DAHA KÖTÜ bulan algoritmalar:")
                for c in sorted(worse_than_ilp, key=lambda x: x.get("optimality_gap_percent", 0), reverse=True):
                    gap = c.get("optimality_gap_percent", 0)
                    analysis_lines.append(f"   • {c['algorithm']}: {gap:.2f}% daha kötü")
        
        analysis_text = QLabel("\n".join(analysis_lines))
        analysis_text.setWordWrap(True)
        analysis_text.setStyleSheet("color: #e2e8f0; font-family: monospace;")
        analysis_layout.addWidget(analysis_text)
        
        layout.addWidget(analysis_frame)
        
        # Not
        note = QLabel(
            "💡 Not: ILP implementasyonu Dijkstra tabanlı yaklaşık çözüm kullanır. "
            "Meta-sezgisel algoritmalar daha geniş çözüm uzayını keşfederek "
            "bazı durumlarda daha iyi sonuçlar bulabilir."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #64748b; font-size: 11px; font-style: italic;")
        layout.addWidget(note)
        
        layout.addStretch()
        return widget
    
    def _create_footer(self):
        layout = QHBoxLayout()
        
        # Tam ekran butonu
        self.fullscreen_btn = QPushButton("⛶ Tam Ekran")
        self.fullscreen_btn.setStyleSheet(self._btn_style("#3b82f6"))
        self.fullscreen_btn.clicked.connect(self._toggle_fullscreen)
        layout.addWidget(self.fullscreen_btn)
        
        layout.addStretch()
        
        export_btn = QPushButton("📥 JSON Kaydet")
        export_btn.setStyleSheet(self._btn_style("#10b981"))
        export_btn.clicked.connect(self._on_export)
        layout.addWidget(export_btn)
        
        close_btn = QPushButton("Kapat")
        close_btn.setStyleSheet(self._btn_style("#64748b"))
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return layout
    
    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_btn.setText("⛶ Tam Ekran")
        else:
            self.showFullScreen()
            self.fullscreen_btn.setText("⛶ Normal")
    
    def keyPressEvent(self, event):
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
    
    def _on_export(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "JSON Kaydet", "", "JSON Files (*.json)"
        )
        if filepath:
            export_data = {
                "source": self.source,
                "destination": self.destination,
                "ilp_optimal_cost": self.ilp_result.optimal_cost if self.ilp_result else None,
                "ilp_computation_time_ms": self.ilp_result.computation_time_ms if self.ilp_result else None,
                "comparisons": self.comparisons
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Başarılı", "ILP benchmark sonuçları kaydedildi!")


__all__ = ["ILPBenchmarkDialog"]
