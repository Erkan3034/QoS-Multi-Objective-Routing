"""
Kontrol Paneli Widget - Graf ve optimizasyon ayarları
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QSpinBox, QDoubleSpinBox, QComboBox, QPushButton, QSlider,
    QProgressBar, QFrame, QGridLayout, QSpacerItem, QSizePolicy, QLineEdit,
    QScrollArea
)
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QColor, QPalette, QIcon
from typing import Dict, List, Tuple
import os


class ControlPanel(QWidget):
    """Kontrol paneli widget'ı."""
    
    # Sinyaller
    generate_graph_requested = pyqtSignal(int, float, int)  # n_nodes, prob, seed
    load_csv_requested = pyqtSignal()  # CSV yükleme isteği
    optimize_requested = pyqtSignal(str, int, int, dict, float)  # algorithm, source, dest, weights, bandwidth_demand
    compare_requested = pyqtSignal(int, int, dict)  # source, dest, weights
    reset_requested = pyqtSignal()
    demand_selected = pyqtSignal(int, int, int)  # source, dest, demand_mbps
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Use minimum width instead of fixed to allow flexibility
        self.setMinimumWidth(260)
        self.setMaximumWidth(300)
        self._demands: List[Tuple[int, int, int]] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """UI kurulumu."""
        # Main Layout (Root)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 8)  # Bottom margin to ensure reset button is fully visible
        main_layout.setSpacing(8)  # Spacing between scroll area and reset button
        
        # Semi-transparent background for panel legibility
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget#ControlPanel {
                background-color: rgba(15, 23, 42, 0.90); /* Slate-900 with 90% opacity */
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.setObjectName("ControlPanel")
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #0f172a;
                width: 6px;
                margin: 0;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                min-height: 30px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #64748b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Content Widget
        content_widget = QWidget()
        content_widget.setObjectName("content_widget")
        content_widget.setStyleSheet("#content_widget { background: transparent; }")
        
        # Content Layout
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(16)  # Increased spacing between sections for better breathing room
        layout.setContentsMargins(0, 0, 4, 0)  # Right margin for scrollbar, no bottom margin (reset button is outside)
        
        # === GRAF OLUŞTURMA ===
        graph_group = QGroupBox()
        graph_group.setStyleSheet(self._group_style())
        graph_layout = QVBoxLayout(graph_group)
        graph_layout.setSpacing(0) 
        graph_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        graph_layout.addWidget(self._create_header_label("Graf Oluşturma"))
        
        # Content Wrapper
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setSpacing(8)
        content_layout.setContentsMargins(12, 12, 12, 12)

        # CSV'den yükle butonu (önerilen)
        self.btn_load_csv = QPushButton("📁 Proje Verisini Yükle (CSV)")
        self.btn_load_csv.setFixedHeight(34)
        self.btn_load_csv.setCursor(Qt.PointingHandCursor)
        self.btn_load_csv.setStyleSheet(self._button_style("#10b981"))  # Yeşil
        self.btn_load_csv.clicked.connect(self._on_load_csv_clicked)
        self.btn_load_csv.setToolTip("Verilen CSV dosyalarından graf verisini yükler")
        content_layout.addWidget(self.btn_load_csv)
        
        # Ayırıcı
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #334155; max-height: 1px;")
        content_layout.addWidget(separator)
        
        # Veya rastgele oluştur label
        random_label = QLabel("— veya Rastgele Oluştur —")
        random_label.setAlignment(Qt.AlignCenter)
        random_label.setStyleSheet("color: #64748b; font-size: 11px;")
        content_layout.addWidget(random_label)

        # Node sayısı
        node_layout = QVBoxLayout()
        node_layout.setSpacing(6)
        lbl_nodes = QLabel("Düğüm Sayısı (n)")
        lbl_nodes.setStyleSheet("color: #94a3b8; font-weight: 500;")
        node_layout.addWidget(lbl_nodes)
        
        self.spin_nodes = QSpinBox()
        self.spin_nodes.setRange(10, 500)
        self.spin_nodes.setValue(250)
        self.spin_nodes.setFixedHeight(30) 
        self.spin_nodes.setStyleSheet(self._input_style())
        node_layout.addWidget(self.spin_nodes)
        content_layout.addLayout(node_layout)
        
        # Bağlantı olasılığı
        prob_layout = QVBoxLayout()
        prob_layout.setSpacing(6)
        prob_header = QHBoxLayout()
        lbl_prob = QLabel("Bağlantı Olasılığı (p)")
        lbl_prob.setStyleSheet("color: #94a3b8; font-weight: 500;")
        prob_header.addWidget(lbl_prob)
        
        self.label_prob = QLabel("0.40")
        self.label_prob.setStyleSheet("color: #e2e8f0; font-weight: bold;")
        prob_header.addWidget(self.label_prob, 0, Qt.AlignRight)
        prob_layout.addLayout(prob_header)
        
        self.slider_prob = QSlider(Qt.Horizontal)
        self.slider_prob.setRange(1, 90)
        self.slider_prob.setValue(40)
        self.slider_prob.valueChanged.connect(self._on_prob_changed)
        self.slider_prob.setStyleSheet(self._slider_style("#3b82f6"))
        prob_layout.addWidget(self.slider_prob)
        content_layout.addLayout(prob_layout)
        
        # Seed
        seed_layout = QVBoxLayout()
        seed_layout.setSpacing(6)
        lbl_seed = QLabel("Seed (opsiyonel)")
        lbl_seed.setStyleSheet("color: #94a3b8; font-weight: 500;")
        seed_layout.addWidget(lbl_seed)
        
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 99999)
        self.spin_seed.setValue(42)
        self.spin_seed.setFixedHeight(30) 
        self.spin_seed.setStyleSheet(self._input_style())
        seed_layout.addWidget(self.spin_seed)
        content_layout.addLayout(seed_layout)
        
        # Generate button
        self.btn_generate = QPushButton("Graf Oluştur")
        self.btn_generate.setFixedHeight(34) 
        self.btn_generate.setCursor(Qt.PointingHandCursor)
        self.btn_generate.setStyleSheet(self._button_style("#2563eb"))
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        # Add icon manually if needed or via text
        content_layout.addWidget(self.btn_generate)
        
        graph_layout.addWidget(content_wrapper)
        layout.addWidget(graph_group)
        
        # === OPTİMİZASYON ===
        opt_group = QGroupBox()
        opt_group.setStyleSheet(self._group_style())
        opt_layout = QVBoxLayout(opt_group)
        opt_layout.setSpacing(0) 
        opt_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        opt_layout.addWidget(self._create_header_label("Optimizasyon"))
        
        # Content Wrapper
        opt_content = QWidget()
        opt_content_layout = QVBoxLayout(opt_content)
        opt_content_layout.setSpacing(8)
        opt_content_layout.setContentsMargins(12, 12, 12, 12)
        
        # Source & Dest Row
        sd_container = QWidget()
        sd_layout = QHBoxLayout(sd_container)
        sd_layout.setContentsMargins(0, 0, 0, 0)
        sd_layout.setSpacing(10)
        
        # Source Column
        src_layout = QVBoxLayout()
        src_layout.setSpacing(4)
        lbl_src = QLabel("Kaynak (S)")
        lbl_src.setStyleSheet("color: #94a3b8; font-weight: 500; font-size: 11px;")
        src_layout.addWidget(lbl_src)
        
        self.spin_source = QSpinBox()
        self.spin_source.setRange(0, 249)
        self.spin_source.setValue(2)
        self.spin_source.setFixedHeight(32) 
        self.spin_source.setStyleSheet(self._input_style())
        src_layout.addWidget(self.spin_source)
        sd_layout.addLayout(src_layout)
        
        # Swap Icon (Optional, visual only)
        lbl_arrow = QLabel("→")
        lbl_arrow.setStyleSheet("color: #64748b; font-size: 20px; font-weight: bold; margin-top: 15px;")
        lbl_arrow.setAlignment(Qt.AlignCenter)
        sd_layout.addWidget(lbl_arrow)
        
        # Dest Column
        dest_layout = QVBoxLayout()
        dest_layout.setSpacing(4)
        lbl_dest = QLabel("Hedef (D)")
        lbl_dest.setStyleSheet("color: #94a3b8; font-weight: 500; font-size: 11px;")
        dest_layout.addWidget(lbl_dest)
        
        self.spin_dest = QSpinBox()
        self.spin_dest.setRange(0, 249)
        self.spin_dest.setValue(248)
        self.spin_dest.setFixedHeight(32) 
        self.spin_dest.setStyleSheet(self._input_style())
        dest_layout.addWidget(self.spin_dest)
        sd_layout.addLayout(dest_layout)
        
        opt_content_layout.addWidget(sd_container)
        
        # Talep seçici (CSV yüklendiğinde aktif)
        demand_layout = QVBoxLayout()
        demand_layout.setSpacing(6)
        self.label_demands = QLabel("📋 Talep Çiftleri:")
        self.label_demands.setStyleSheet("color: #fbbf24; font-weight: bold;")
        demand_layout.addWidget(self.label_demands)
        
        self.combo_demands = QComboBox()
        self.combo_demands.setFixedHeight(30)
        self.combo_demands.setStyleSheet(self._input_style())
        self.combo_demands.currentIndexChanged.connect(self._on_demand_selected)
        self.combo_demands.setToolTip("Verilen kaynak-hedef çiftlerinden birini seçin")
        demand_layout.addWidget(self.combo_demands)
        
        # Başlangıçta gizle
        self.label_demands.hide()
        self.combo_demands.hide()
        
        opt_content_layout.addLayout(demand_layout)
        
        # Manuel seçim ayırıcı
        self.manual_separator = QFrame()
        self.manual_separator.setFrameShape(QFrame.HLine)
        self.manual_separator.setStyleSheet("background-color: #334155; max-height: 1px;")
        self.manual_label = QLabel("— veya Manuel Seçim —")
        self.manual_label.setAlignment(Qt.AlignCenter)
        self.manual_label.setStyleSheet("color: #64748b; font-size: 11px;")
        self.manual_separator.hide()
        self.manual_label.hide()
        opt_content_layout.addWidget(self.manual_separator)
        opt_content_layout.addWidget(self.manual_label)
        
        # Ağırlıklar
        lbl_weights = QLabel("Ağırlıklar (W)")
        lbl_weights.setStyleSheet("color: #94a3b8; font-weight: 500;")
        opt_content_layout.addWidget(lbl_weights)
        
        weights_layout = QVBoxLayout()
        weights_layout.setSpacing(10)
        
        self.slider_delay, self.label_delay = self._create_weight_row("Gecikme", 33, "#3b82f6")
        weights_layout.addLayout(self.slider_delay)
        
        self.slider_rel, self.label_rel = self._create_weight_row("Güvenilirlik", 33, "#22c55e")
        weights_layout.addLayout(self.slider_rel)
        
        self.slider_res, self.label_res = self._create_weight_row("Kaynak", 34, "#f59e0b")
        weights_layout.addLayout(self.slider_res)
        
        opt_content_layout.addLayout(weights_layout)
        
        # Algorithm selection
        lbl_algo = QLabel("Algoritma")
        lbl_algo.setStyleSheet("color: #94a3b8; font-weight: 500;")
        opt_content_layout.addWidget(lbl_algo)
        
        self.algo_buttons = {}
        algo_container = QWidget()
        algo_grid = QGridLayout(algo_container)
        algo_grid.setContentsMargins(0, 0, 0, 0)
        algo_grid.setVerticalSpacing(8) # Increased spacing
        algo_grid.setHorizontalSpacing(8)
        
        algorithms = [
            ("Genetic", "ga", "genetic.svg"), 
            ("Ant", "aco", "ant.svg"),
            ("Particle", "pso", "particle.svg"), 
            ("Simulated", "sa", "simulated.svg"),
            ("Q-Learning", "qlearning", "qlearning.svg"), 
            ("SARSA", "sarsa", "sarsa.svg")
        ]
        
        icons_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "icons")

        for i, (text, key, icon_file) in enumerate(algorithms):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setFixedHeight(32) # Adequate height
            btn.setCursor(Qt.PointingHandCursor)
            
            # Load Icon
            icon_path = os.path.join(icons_path, icon_file)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(18, 18))
            
            btn.setStyleSheet(self._algo_button_style())
            btn.clicked.connect(lambda checked, k=key: self._on_algo_selected(k))
            algo_grid.addWidget(btn, i // 2, i % 2) # Keep grid for now, but scroll makes it safe
            self.algo_buttons[key] = btn
            
        self.selected_algo = "sa"
        self.algo_buttons["sa"].setChecked(True)
        
        opt_content_layout.addWidget(algo_container)
        
        # Optimize button
        self.btn_optimize = QPushButton("Optimize Et")
        self.btn_optimize.setFixedHeight(34) 
        self.btn_optimize.setCursor(Qt.PointingHandCursor)
        self.btn_optimize.setStyleSheet(self._button_style("#a855f7"))
        self.btn_optimize.clicked.connect(self._on_optimize_clicked)
        opt_content_layout.addWidget(self.btn_optimize)
        
        # Compare button
        self.btn_compare = QPushButton("Tüm Algoritmaları Karşılaştır")
        self.btn_compare.setFixedHeight(34) 
        self.btn_compare.setCursor(Qt.PointingHandCursor)
        self.btn_compare.setStyleSheet(self._button_style("#ec4899"))
        self.btn_compare.clicked.connect(self._on_compare_clicked)
        opt_content_layout.addWidget(self.btn_compare)
        
        opt_layout.addWidget(opt_content)
        layout.addWidget(opt_group)
        
        # Progress Bar (Hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #334155;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #3b82f6; 
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        
        # Content Layout - Add stretch before reset button to push it down
        # (Reset button will be moved outside scroll area below)
        layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll, 1)  # Stretch factor 1 to fill available space
        
        # Reset Button - OUTSIDE scroll area so it's always visible
        # This ensures the button is never cut off and always accessible
        self.btn_reset = QPushButton("Projeyi Sıfırla")
        self.btn_reset.setFlat(True)
        self.btn_reset.setMinimumHeight(44)  # Minimum height to ensure full visibility
        self.btn_reset.setFixedHeight(44)  # Fixed height for consistency
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                color: #ef4444; 
                font-weight: bold;
                border: 1px solid #ef4444;
                border-radius: 8px;
                padding: 10px 12px;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.15);
                border-color: #f87171;
            }
            QPushButton:pressed {
                background-color: rgba(239, 68, 68, 0.25);
            }
        """)
        self.btn_reset.clicked.connect(lambda: self.reset_requested.emit())
        # Add button with no stretch factor and ensure it's at the bottom
        main_layout.addWidget(self.btn_reset, 0, Qt.AlignBottom)  # Align to bottom, no stretch
    
    def _create_weight_row(self, label, val, color):
        """Ağırlık satırı slider + label."""
        row = QHBoxLayout()
        row.setSpacing(12)
        
        lbl = QLabel(label)
        lbl.setFixedWidth(70)
        lbl.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 500;")
        row.addWidget(lbl)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(val)
        slider.setStyleSheet(self._slider_style(color))
        slider.valueChanged.connect(self._on_weight_changed)
        row.addWidget(slider)
        
        val_lbl = QLabel(f"{val}%")
        val_lbl.setFixedWidth(36)
        val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        val_lbl.setStyleSheet("color: #e2e8f0; font-size: 14px; font-weight: bold;")
        row.addWidget(val_lbl)
        
        return row, val_lbl

    def _create_header_label(self, text):
        """Card header label."""
        lbl = QLabel(text)
        lbl.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif;
            font-weight: bold;
            font-size: 15px;
            color: #f1f5f9;
            padding-bottom: 8px;
            border-bottom: 1px solid #1e293b;
            margin-bottom: 8px;
        """)
        return lbl

    def _group_style(self):
        return """
            QGroupBox {
                border: 1px solid #1e293b;
                border-radius: 12px;
                background-color: #111827; /* Darker background */
            }
        """

        # but title positioning matters.
    
    def _input_style(self) -> str:
        return """
            QSpinBox, QDoubleSpinBox {
                background-color: #1f293b; 
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 14px;
                font-weight: 500;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #3b82f6;
                background-color: #1e293b;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button,
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                width: 0;
                height: 0;
            }
        """
    
    def _slider_style(self, color) -> str:
        return f"""
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background: #334155;
                margin: 0;
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {color};
                border: 2px solid #0f172a;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {color};
                border-radius: 2px;
            }}
        """
    
    def _button_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 14px;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
            QPushButton:disabled {{
                background-color: #334155;
                color: #64748b;
            }}
        """
        
    def _algo_button_style(self) -> str:
        return """
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
                padding-left: 8px;
            }
            QPushButton:hover {
                border-color: #475569;
                color: #e2e8f0;
                background-color: #1e293b;
            }
            QPushButton:checked {
                background-color: #a855f7;
                border-color: #a855f7;
                color: white;
                font-weight: 600;
            }
        """


    def _on_weight_changed(self):
        """Ağırlık değiştiğinde normalize et."""
        delay = self.slider_delay.itemAt(1).widget().value()
        rel = self.slider_rel.itemAt(1).widget().value()
        res = self.slider_res.itemAt(1).widget().value()
        
        total = delay + rel + res
        if total > 0:
            self.label_delay.setText(f"{int(delay * 100 / total)}%")
            self.label_rel.setText(f"{int(rel * 100 / total)}%")
            self.label_res.setText(f"{int(res * 100 / total)}%")
    
    def _on_prob_changed(self):
        val = self.slider_prob.value() / 100.0
        self.label_prob.setText(f"{val:.2f}")

    def _get_weights(self) -> Dict[str, float]:
        """Normalize edilmiş ağırlıkları döndür."""
        delay = self.slider_delay.itemAt(1).widget().value()
        rel = self.slider_rel.itemAt(1).widget().value()
        res = self.slider_res.itemAt(1).widget().value()
        total = delay + rel + res
        
        if total == 0:
            return {"delay": 0.33, "reliability": 0.33, "resource": 0.34}
        
        return {
            "delay": delay / total,
            "reliability": rel / total,
            "resource": res / total
        }
    
    def _on_algo_selected(self, selected_key: str):
        """Algoritma seçildiğinde diğerlerini kapat."""
        self.selected_algo = selected_key
        for key, btn in self.algo_buttons.items():
            if key != selected_key:
                btn.setChecked(False)
            else:
                btn.setChecked(True)
    
    def _get_algorithm_key(self) -> str:
        """Seçili algoritma anahtarını döndür."""
        if hasattr(self, 'selected_algo'):
            return self.selected_algo
        return "ga"
    
    def _on_generate_clicked(self):
        """Graf oluştur butonuna tıklandı."""
        # Slider is 1-90, representing 0.01-0.90
        prob = self.slider_prob.value() / 100.0
        self.generate_graph_requested.emit(
            self.spin_nodes.value(),
            prob,
            self.spin_seed.value()
        )
    
    def _on_optimize_clicked(self):
        """Optimize butonuna tıklandı."""
        # Get demand if applicable
        demand = 0.0
        if self.combo_demands.isVisible():
            idx = self.combo_demands.currentIndex()
            if idx >= 0 and idx < len(self._demands):
                # _demands is list of (src, dst, demand)
                # Check if current source/dest match selected demand
                # Even if they don't, if the user explicitly selected a demand, 
                # we might want to respect it, or just use what's in the list.
                # However, if user changes source manually, demand might not be relevant.
                # Logic: If source/dest match the selected demand entry, use that demand.
                d_src, d_dst, d_val = self._demands[idx]
                if d_src == self.spin_source.value() and d_dst == self.spin_dest.value():
                    demand = float(d_val)
        
        self.optimize_requested.emit(
            self._get_algorithm_key(),
            self.spin_source.value(),
            self.spin_dest.value(),
            self._get_weights(),
            demand
        )

    
    def _on_compare_clicked(self):
        """Karşılaştır butonuna tıklandı."""
        self.compare_requested.emit(
            self.spin_source.value(),
            self.spin_dest.value(),
            self._get_weights()
        )
    
    def set_node_range(self, max_node: int):
        """Düğüm ID aralığını ayarla."""
        self.spin_source.setRange(0, max_node - 1)
        self.spin_dest.setRange(0, max_node - 1)
        self.spin_dest.setValue(max_node - 1)
    
    def set_loading(self, loading: bool):
        """Yükleniyor durumunu ayarla."""
        self.btn_generate.setEnabled(not loading)
        if hasattr(self, 'btn_load_csv'):
            self.btn_load_csv.setEnabled(not loading)
        self.btn_optimize.setEnabled(not loading)
        self.btn_compare.setEnabled(not loading)
        if hasattr(self, 'btn_reset'):
            self.btn_reset.setEnabled(not loading)
        
        if loading:
            self.progress_bar.setRange(0, 0)  # Indeterminate
            self.progress_bar.show()
        else:
            self.progress_bar.hide()
    
    def set_source(self, node: int):
        """Kaynak düğümü ayarla."""
        self.spin_source.setValue(node)
    
    def set_destination(self, node: int):
        """Hedef düğümü ayarla."""
        self.spin_dest.setValue(node)
    
    def set_demands(self, demands: List[Tuple[int, int, int]]):
        """
        Talep çiftlerini ayarla ve göster.
        
        Args:
            demands: [(source, destination, demand_mbps), ...] listesi
        """
        self._demands = demands
        self.combo_demands.clear()
        
        if demands:
            for src, dst, demand in demands:
                self.combo_demands.addItem(f"#{len(self.combo_demands) + 1}: {src} → {dst} ({demand} Mbps)")
            
            # Talep seçiciyi göster
            self.label_demands.show()
            self.combo_demands.show()
            self.manual_separator.show()
            self.manual_label.show()
            
            # İlk talebi seç
            self.combo_demands.setCurrentIndex(0)
        else:
            self.hide_demands()
    
    def hide_demands(self):
        """Talep seçiciyi gizle."""
        self.label_demands.hide()
        self.combo_demands.hide()
        self.manual_separator.hide()
        self.manual_label.hide()
        self._demands = []
    
    def _on_load_csv_clicked(self):
        """CSV'den yükle butonuna tıklandı."""
        self.load_csv_requested.emit()
    
    def _on_demand_selected(self, index: int):
        """Talep çifti seçildiğinde."""
        if index >= 0 and index < len(self._demands):
            src, dst, demand = self._demands[index]
            self.spin_source.setValue(src)
            self.spin_dest.setValue(dst)
            self.demand_selected.emit(src, dst, demand)

    def reset_defaults(self):
        """Tüm giriş alanlarını varsayılan değerlere sıfırla."""
        # Graph generation defaults
        self.spin_nodes.setValue(250)
        self.slider_prob.setValue(40) # 0.40
        self._on_prob_changed() # Force label update
        self.spin_seed.setValue(42)
        
        # Optimization defaults
        # IMPORTANT: Set range first, otherwise setValue(249) might be clamped if previous max was lower
        self.set_node_range(250) 
        
        self.spin_source.setValue(0)
        self.spin_dest.setValue(249)
        
        # Reset weights to ~33% each (Total 100)
        self.slider_delay.itemAt(1).widget().setValue(33)
        self.slider_rel.itemAt(1).widget().setValue(33)
        self.slider_res.itemAt(1).widget().setValue(34)
        # Force label update in case values didn't change but labels were wrong (unlikely but safe)
        self._on_weight_changed()
        
        # Algorithm defaults
        self._on_algo_selected("ga")  # Genetic



