"""
Kontrol Paneli Widget - Graf ve optimizasyon ayarları
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QSpinBox, QDoubleSpinBox, QComboBox, QPushButton, QSlider,
    QProgressBar, QFrame
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict


class ControlPanel(QWidget):
    """Kontrol paneli widget'ı."""
    
    # Sinyaller
    generate_graph_requested = pyqtSignal(int, float, int)  # n_nodes, prob, seed
    optimize_requested = pyqtSignal(str, int, int, dict)  # algorithm, source, dest, weights
    compare_requested = pyqtSignal(int, int, dict)  # source, dest, weights
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(280)
        self._setup_ui()
    
    def _setup_ui(self):
        """UI kurulumu."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # === GRAF OLUŞTURMA ===
        graph_group = QGroupBox("📊 Graf Oluşturma")
        graph_group.setStyleSheet(self._group_style())
        graph_layout = QVBoxLayout(graph_group)
        
        # Node sayısı
        node_layout = QHBoxLayout()
        node_layout.addWidget(QLabel("Düğüm (n):"))
        self.spin_nodes = QSpinBox()
        self.spin_nodes.setRange(10, 500)
        self.spin_nodes.setValue(250)
        self.spin_nodes.setStyleSheet(self._input_style())
        node_layout.addWidget(self.spin_nodes)
        graph_layout.addLayout(node_layout)
        
        # Bağlantı olasılığı
        prob_layout = QHBoxLayout()
        prob_layout.addWidget(QLabel("Olasılık (p):"))
        self.spin_prob = QDoubleSpinBox()
        self.spin_prob.setRange(0.1, 0.9)
        self.spin_prob.setValue(0.4)
        self.spin_prob.setSingleStep(0.05)
        self.spin_prob.setStyleSheet(self._input_style())
        prob_layout.addWidget(self.spin_prob)
        graph_layout.addLayout(prob_layout)
        
        # Seed
        seed_layout = QHBoxLayout()
        seed_layout.addWidget(QLabel("Seed:"))
        self.spin_seed = QSpinBox()
        self.spin_seed.setRange(0, 99999)
        self.spin_seed.setValue(42)
        self.spin_seed.setStyleSheet(self._input_style())
        seed_layout.addWidget(self.spin_seed)
        graph_layout.addLayout(seed_layout)
        
        # Generate button
        self.btn_generate = QPushButton("🔄 Graf Oluştur")
        self.btn_generate.setStyleSheet(self._button_style("#3b82f6"))
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        graph_layout.addWidget(self.btn_generate)
        
        layout.addWidget(graph_group)
        
        # === OPTİMİZASYON ===
        opt_group = QGroupBox("⚙️ Optimizasyon")
        opt_group.setStyleSheet(self._group_style())
        opt_layout = QVBoxLayout(opt_group)
        
        # Source
        src_layout = QHBoxLayout()
        src_layout.addWidget(QLabel("Kaynak (S):"))
        self.spin_source = QSpinBox()
        self.spin_source.setRange(0, 249)
        self.spin_source.setValue(0)
        self.spin_source.setStyleSheet(self._input_style())
        src_layout.addWidget(self.spin_source)
        opt_layout.addLayout(src_layout)
        
        # Destination
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Hedef (D):"))
        self.spin_dest = QSpinBox()
        self.spin_dest.setRange(0, 249)
        self.spin_dest.setValue(249)
        self.spin_dest.setStyleSheet(self._input_style())
        dest_layout.addWidget(self.spin_dest)
        opt_layout.addLayout(dest_layout)
        
        # Separator
        opt_layout.addWidget(self._create_separator())
        
        # Ağırlıklar
        opt_layout.addWidget(QLabel("Ağırlıklar (W):"))
        
        # Delay weight
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Gecikme:"))
        self.slider_delay = QSlider(Qt.Horizontal)
        self.slider_delay.setRange(0, 100)
        self.slider_delay.setValue(33)
        self.slider_delay.valueChanged.connect(self._on_weight_changed)
        self.label_delay = QLabel("33%")
        self.label_delay.setFixedWidth(35)
        delay_layout.addWidget(self.slider_delay)
        delay_layout.addWidget(self.label_delay)
        opt_layout.addLayout(delay_layout)
        
        # Reliability weight
        rel_layout = QHBoxLayout()
        rel_layout.addWidget(QLabel("Güvenilirlik:"))
        self.slider_rel = QSlider(Qt.Horizontal)
        self.slider_rel.setRange(0, 100)
        self.slider_rel.setValue(33)
        self.slider_rel.valueChanged.connect(self._on_weight_changed)
        self.label_rel = QLabel("33%")
        self.label_rel.setFixedWidth(35)
        rel_layout.addWidget(self.slider_rel)
        rel_layout.addWidget(self.label_rel)
        opt_layout.addLayout(rel_layout)
        
        # Resource weight
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel("Kaynak:"))
        self.slider_res = QSlider(Qt.Horizontal)
        self.slider_res.setRange(0, 100)
        self.slider_res.setValue(34)
        self.slider_res.valueChanged.connect(self._on_weight_changed)
        self.label_res = QLabel("34%")
        self.label_res.setFixedWidth(35)
        res_layout.addWidget(self.slider_res)
        res_layout.addWidget(self.label_res)
        opt_layout.addLayout(res_layout)
        
        # Separator
        opt_layout.addWidget(self._create_separator())
        
        # Algorithm selection
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel("Algoritma:"))
        self.combo_algorithm = QComboBox()
        self.combo_algorithm.addItems([
            "Genetic Algorithm",
            "Ant Colony (ACO)",
            "Particle Swarm (PSO)",
            "Simulated Annealing",
            "Q-Learning",
            "SARSA"
        ])
        self.combo_algorithm.setStyleSheet(self._input_style())
        algo_layout.addWidget(self.combo_algorithm)
        opt_layout.addLayout(algo_layout)
        
        # Optimize button
        self.btn_optimize = QPushButton("▶️ Optimize Et")
        self.btn_optimize.setStyleSheet(self._button_style("#8b5cf6"))
        self.btn_optimize.clicked.connect(self._on_optimize_clicked)
        opt_layout.addWidget(self.btn_optimize)
        
        # Compare button
        self.btn_compare = QPushButton("📊 Tümünü Karşılaştır")
        self.btn_compare.setStyleSheet(self._button_style("#ec4899"))
        self.btn_compare.clicked.connect(self._on_compare_clicked)
        opt_layout.addWidget(self.btn_compare)
        
        layout.addWidget(opt_group)
        
        # === PROGRESS ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #334155;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #8b5cf6;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
    
    def _create_separator(self) -> QFrame:
        """Ayırıcı çizgi oluştur."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #334155;")
        line.setFixedHeight(1)
        return line
    
    def _group_style(self) -> str:
        return """
            QGroupBox {
                font-weight: bold;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #94a3b8;
                font-size: 12px;
            }
        """
    
    def _input_style(self) -> str:
        return """
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #1e293b;
                color: white;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 80px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #3b82f6;
            }
        """
    
    def _button_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
            QPushButton:pressed {{
                background-color: {color}aa;
            }}
            QPushButton:disabled {{
                background-color: #475569;
            }}
        """
    
    def _on_weight_changed(self):
        """Ağırlık değiştiğinde normalize et."""
        delay = self.slider_delay.value()
        rel = self.slider_rel.value()
        res = self.slider_res.value()
        
        total = delay + rel + res
        if total > 0:
            self.label_delay.setText(f"{delay * 100 // total}%")
            self.label_rel.setText(f"{rel * 100 // total}%")
            self.label_res.setText(f"{res * 100 // total}%")
    
    def _get_weights(self) -> Dict[str, float]:
        """Normalize edilmiş ağırlıkları döndür."""
        delay = self.slider_delay.value()
        rel = self.slider_rel.value()
        res = self.slider_res.value()
        total = delay + rel + res
        
        if total == 0:
            return {"delay": 0.33, "reliability": 0.33, "resource": 0.34}
        
        return {
            "delay": delay / total,
            "reliability": rel / total,
            "resource": res / total
        }
    
    def _get_algorithm_key(self) -> str:
        """Seçili algoritma anahtarını döndür."""
        idx = self.combo_algorithm.currentIndex()
        keys = ["ga", "aco", "pso", "sa", "qlearning", "sarsa"]
        return keys[idx]
    
    def _on_generate_clicked(self):
        """Graf oluştur butonuna tıklandı."""
        self.generate_graph_requested.emit(
            self.spin_nodes.value(),
            self.spin_prob.value(),
            self.spin_seed.value()
        )
    
    def _on_optimize_clicked(self):
        """Optimize butonuna tıklandı."""
        self.optimize_requested.emit(
            self._get_algorithm_key(),
            self.spin_source.value(),
            self.spin_dest.value(),
            self._get_weights()
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
        self.btn_optimize.setEnabled(not loading)
        self.btn_compare.setEnabled(not loading)
        
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

