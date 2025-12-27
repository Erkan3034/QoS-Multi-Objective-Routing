"""
Hiperparametre Ayar Diyaloğu
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, 
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton, QFormLayout, 
    QScrollArea, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from ...core.config import settings

class HyperparameterDialog(QDialog):
    """
    Algoritma hiperparametrelerini düzenlemek için diyalog penceresi.
    """
    
    def __init__(self, current_params=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gelişmiş Algoritma Ayarları")
        self.setMinimumSize(500, 600)
        self.resize(600, 700)
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a;
                color: #f1f5f9;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 14px;
            }
            QTabWidget::pane {
                border: 1px solid #334155;
                background: #1e293b;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #0f172a;
                color: #94a3b8;
                padding: 10px 20px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1e293b;
                color: #3b82f6;
                font-weight: bold;
                border-bottom: 2px solid #3b82f6;
            }
            QTabBar::tab:hover {
                color: #e2e8f0;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #0f172a;
                color: #f1f5f9;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #3b82f6;
            }
            QGroupBox {
                border: 1px solid #334155;
                border-radius: 8px;
                margin-top: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #94a3b8;
            }
        """)
        
        # Store current params or empty dict
        self.params = current_params.copy() if current_params else {}
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Helper: Header
        header = QLabel("Algoritma Parametreleri")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)
        
        desc = QLabel("Algoritmaların davranışını değiştirmek için aşağıdaki değerleri özelleştirebilirsiniz.\nDikkat: Yanlış ayarlar performansı düşürebilir.")
        desc.setStyleSheet("color: #94a3b8; margin-bottom: 10px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # --- Genetic Algorithm Tab ---
        self.tab_ga = QWidget()
        self.inputs_ga = {}
        ga_layout = QFormLayout(self.tab_ga)
        ga_layout.setSpacing(15)
        ga_layout.setContentsMargins(20, 25, 20, 20)
        
        self._add_spin(ga_layout, "Popülasyon Boyutu", "GA_POPULATION_SIZE", settings.GA_POPULATION_SIZE, 10, 1000, self.inputs_ga)
        self._add_spin(ga_layout, "Jenerasyon Sayısı", "GA_GENERATIONS", settings.GA_GENERATIONS, 10, 5000, self.inputs_ga)
        self._add_double(ga_layout, "Mutasyon Oranı", "GA_MUTATION_RATE", settings.GA_MUTATION_RATE, 0.0, 1.0, 0.01, self.inputs_ga)
        self._add_double(ga_layout, "Çaprazlama Oranı", "GA_CROSSOVER_RATE", settings.GA_CROSSOVER_RATE, 0.0, 1.0, 0.05, self.inputs_ga)
        self._add_double(ga_layout, "Elitizm Oranı", "GA_ELITISM", settings.GA_ELITISM, 0.0, 1.0, 0.01, self.inputs_ga)
        
        self.tabs.addTab(self.tab_ga, "Genetic")
        
        # --- ACO Tab ---
        self.tab_aco = QWidget()
        self.inputs_aco = {}
        aco_layout = QFormLayout(self.tab_aco)
        aco_layout.setSpacing(15)
        aco_layout.setContentsMargins(20, 25, 20, 20)
        
        self._add_spin(aco_layout, "Karınca Sayısı", "ACO_N_ANTS", settings.ACO_N_ANTS, 5, 500, self.inputs_aco)
        self._add_spin(aco_layout, "İterasyon Sayısı", "ACO_N_ITERATIONS", settings.ACO_N_ITERATIONS, 10, 2000, self.inputs_aco)
        self._add_double(aco_layout, "Alpha (Feromon Etkisi)", "ACO_ALPHA", settings.ACO_ALPHA, 0.0, 10.0, 0.1, self.inputs_aco)
        self._add_double(aco_layout, "Beta (Sezgisel Etkisi)", "ACO_BETA", settings.ACO_BETA, 0.0, 10.0, 0.1, self.inputs_aco)
        self._add_double(aco_layout, "Buharlaşma Oranı", "ACO_EVAPORATION_RATE", settings.ACO_EVAPORATION_RATE, 0.0, 1.0, 0.05, self.inputs_aco)
        
        self.tabs.addTab(self.tab_aco, "Ant Colony")
        
        # --- PSO Tab ---
        self.tab_pso = QWidget()
        self.inputs_pso = {}
        pso_layout = QFormLayout(self.tab_pso)
        pso_layout.setSpacing(15)
        pso_layout.setContentsMargins(20, 25, 20, 20)
        
        self._add_spin(pso_layout, "Parçacık Sayısı", "PSO_N_PARTICLES", settings.PSO_N_PARTICLES, 5, 500, self.inputs_pso)
        self._add_spin(pso_layout, "İterasyon Sayısı", "PSO_N_ITERATIONS", settings.PSO_N_ITERATIONS, 10, 2000, self.inputs_pso)
        self._add_double(pso_layout, "Eylemsizlik (W)", "PSO_W", settings.PSO_W, 0.0, 2.0, 0.05, self.inputs_pso)
        self._add_double(pso_layout, "Bilişsel Katsayı (C1)", "PSO_C1", settings.PSO_C1, 0.0, 4.0, 0.1, self.inputs_pso)
        self._add_double(pso_layout, "Sosyal Katsayı (C2)", "PSO_C2", settings.PSO_C2, 0.0, 4.0, 0.1, self.inputs_pso)
        
        self.tabs.addTab(self.tab_pso, "PSO")
        
        # --- Simulated Annealing Tab ---
        self.tab_sa = QWidget()
        self.inputs_sa = {}
        sa_layout = QFormLayout(self.tab_sa)
        sa_layout.setSpacing(15)
        sa_layout.setContentsMargins(20, 25, 20, 20)
        
        self._add_double(sa_layout, "Başlangıç Sıcaklığı", "SA_INITIAL_TEMPERATURE", settings.SA_INITIAL_TEMPERATURE, 1.0, 10000.0, 10.0, self.inputs_sa)
        self._add_double(sa_layout, "Bitiş Sıcaklığı", "SA_FINAL_TEMPERATURE", settings.SA_FINAL_TEMPERATURE, 0.0001, 10.0, 0.0001, self.inputs_sa)
        self._add_double(sa_layout, "Soğuma Oranı", "SA_COOLING_RATE", settings.SA_COOLING_RATE, 0.5, 0.9999, 0.001, self.inputs_sa)
        self._add_spin(sa_layout, "Her Sıcaklıkta İterasyon", "SA_ITERATIONS_PER_TEMP", settings.SA_ITERATIONS_PER_TEMP, 1, 500, self.inputs_sa)
        
        self.tabs.addTab(self.tab_sa, "Simulated Annealing")
        
        # --- RL (Q-Learning / SARSA) Tab ---
        self.tab_rl = QWidget()
        self.inputs_rl = {}
        rl_layout = QFormLayout(self.tab_rl)
        rl_layout.setSpacing(15)
        rl_layout.setContentsMargins(20, 25, 20, 20)
        
        self._add_spin(rl_layout, "Epizot Sayısı", "QL_EPISODES", settings.QL_EPISODES, 100, 50000, self.inputs_rl)
        self._add_double(rl_layout, "Öğrenme Oranı (Alpha)", "QL_LEARNING_RATE", settings.QL_LEARNING_RATE, 0.01, 1.0, 0.01, self.inputs_rl)
        self._add_double(rl_layout, "İndirim Faktörü (Gamma)", "QL_DISCOUNT_FACTOR", settings.QL_DISCOUNT_FACTOR, 0.0, 1.0, 0.01, self.inputs_rl)
        self._add_double(rl_layout, "Epsilon Başlangıç", "QL_EPSILON_START", settings.QL_EPSILON_START, 0.0, 1.0, 0.1, self.inputs_rl)
        self._add_double(rl_layout, "Epsilon Bitiş", "QL_EPSILON_END", settings.QL_EPSILON_END, 0.0, 1.0, 0.001, self.inputs_rl)
        self._add_double(rl_layout, "Epsilon Çürüme", "QL_EPSILON_DECAY", settings.QL_EPSILON_DECAY, 0.8, 0.99999, 0.0001, self.inputs_rl)
        
        self.tabs.addTab(self.tab_rl, "Q-Learning / SARSA")
        
        # Button Box
        btn_box = QHBoxLayout()
        btn_box.setContentsMargins(0, 20, 0, 0)
        
        self.btn_defaults = QPushButton("Varsayılanlara Dön")
        self.btn_defaults.setCursor(Qt.PointingHandCursor)
        self.btn_defaults.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #475569;
                color: #cbd5e1;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: white;
            }
        """)
        self.btn_defaults.clicked.connect(self._reset_defaults)
        btn_box.addWidget(self.btn_defaults)
        
        btn_box.addStretch()
        
        self.btn_cancel = QPushButton("İptal")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                font-weight: 500;
                border: none;
                padding: 8px 16px;
            }
            QPushButton:hover { color: #f1f5f9; }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton("Kaydet ve Uygula")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.btn_save.clicked.connect(self._save_params)
        btn_box.addWidget(self.btn_save)
        
        layout.addLayout(btn_box)

    def _add_spin(self, layout, label, key, default_val, min_val, max_val, storage):
        """Int spin box ekle."""
        row = QHBoxLayout()
        lbl = QLabel(label)
        
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        
        # Set value from current params if exists, else default
        val = self.params.get(key, default_val)
        spin.setValue(int(val))
        
        spin.setFixedWidth(120)
        
        layout.addRow(lbl, spin)
        storage[key] = (spin, default_val)

    def _add_double(self, layout, label, key, default_val, min_val, max_val, step, storage):
        """Double spin box ekle."""
        lbl = QLabel(label)
        
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        
        # Decide precision based on step
        if step < 0.01:
            spin.setDecimals(4)
        elif step < 0.1:
            spin.setDecimals(3)
        else:
            spin.setDecimals(2)
            
        # Set value
        val = self.params.get(key, default_val)
        spin.setValue(float(val))
        
        spin.setFixedWidth(120)
        
        layout.addRow(lbl, spin)
        storage[key] = (spin, default_val)

    def _reset_defaults(self):
        """Tüm girdileri varsayılan değerlerine döndür."""
        reply = QMessageBox.question(self, "Onay", "Tüm ayarlar varsayılan değerlere dönecek. Emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            all_inputs = [self.inputs_ga, self.inputs_aco, self.inputs_pso, self.inputs_sa, self.inputs_rl]
            for inputs in all_inputs:
                for key, (widget, default) in inputs.items():
                    widget.setValue(default)
    
    def _save_params(self):
        """Değerleri topla ve kabul et."""
        all_inputs = [self.inputs_ga, self.inputs_aco, self.inputs_pso, self.inputs_sa, self.inputs_rl]
        
        new_params = {}
        for inputs in all_inputs:
            for key, (widget, _) in inputs.items():
                new_params[key] = widget.value()
        
        self.params = new_params
        self.accept()
        
    def get_params(self):
        return self.params
