from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSpinBox, QGraphicsOpacityEffect,
    QSizePolicy, QLineEdit, QComboBox, QToolButton, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize, QParallelAnimationGroup
from PyQt5.QtGui import QIcon
from dataclasses import dataclass, field
from typing import List

try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

@dataclass
class ComparisonResult:
    algo_name: str
    cost: float
    time: float
    weighted_cost: float = 0.0
    path: List[int] = field(default_factory=list)

class AlgorithmComparisonDialog(QDialog):
    """
    İki algoritmayı kıyaslayan pencere (Dialog).
    """
    compare_requested = pyqtSignal(str, str)
    show_path_requested = pyqtSignal(list, str) # path, color_hex
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Algoritma Kıyaslama Aracı")
        self.setFixedSize(850, 600) # Increased height for buttons
        self.setStyleSheet("background-color: #0f172a;")
        self.path1 = []
        self.path2 = []
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🤖 Algoritma Karşılaştırma")
        title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Info Label (Source -> Dest)
        self.info_label = QLabel("Kıyaslama için algoritmaları seçip başlatın.")
        self.info_label.setStyleSheet("color: #94a3b8; font-size: 13px; font-style: italic;")
        self.info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Selection Area
        sel_container_layout = QHBoxLayout()
        
        # Algoritmalar
        self.algo_options = [
            ("Genetik Algoritma", "ga"),
            ("Karınca Kolonisi", "aco"),
            ("Parçacık Sürü (PSO)", "pso"),
            ("Benzetim Tavlama (SA)", "sa"),
            ("Q-Learning", "qlearning"),
            ("SARSA", "sarsa")
        ]
        
        self.combo1 = self._create_combo()
        self.combo2 = self._create_combo()
        self.combo1.setCurrentIndex(0) # Genetic
        self.combo2.setCurrentIndex(1) # ACO
        
        sel_container_layout.addWidget(self.combo1)
        
        vs_lbl = QLabel("VS")
        vs_lbl.setStyleSheet("color: #64748b; font-weight: bold;")
        sel_container_layout.addWidget(vs_lbl)
        
        sel_container_layout.addWidget(self.combo2)
        
        layout.addLayout(sel_container_layout)
        
        # Run Button
        self.btn_run = QPushButton("⚡ Analizi Başlat")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setFixedHeight(40)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; color: white; font-weight: bold;
                border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        self.btn_run.clicked.connect(self._on_compare_clicked)
        layout.addWidget(self.btn_run)
        
        # Chart Container
        self.chart_container = QFrame()
        self.chart_container.setStyleSheet("background-color: #1e293b; border-radius: 12px;")
        chart_layout = QVBoxLayout(self.chart_container)
        
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(8, 4), facecolor='#1e293b')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background: transparent;")
            chart_layout.addWidget(self.canvas)
        else:
            lbl = QLabel("Matplotlib yok")
            lbl.setStyleSheet("color: white;")
            chart_layout.addWidget(lbl)
            
        layout.addWidget(self.chart_container)
        
        # Path Visualization Buttons
        path_btn_layout = QHBoxLayout()
        
        self.btn_show_path1 = QPushButton("Sol Grafikteki Yolu Göster (Mavi)")
        self.btn_show_path1.setCursor(Qt.PointingHandCursor)
        self.btn_show_path1.clicked.connect(lambda: self.show_path_requested.emit(self.path1, '#3b82f6'))
        self.btn_show_path1.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; color: white; font-weight: bold;
                border-radius: 6px; padding: 8px;
            }
            QPushButton:hover { background-color: #2563eb; }
            QPushButton:disabled { background-color: #334155; color: #64748b; }
        """)
        self.btn_show_path1.setEnabled(False)
        
        self.btn_show_path2 = QPushButton("Sağ Grafikteki Yolu Göster (Turuncu)")
        self.btn_show_path2.setCursor(Qt.PointingHandCursor)
        self.btn_show_path2.clicked.connect(lambda: self.show_path_requested.emit(self.path2, '#f59e0b'))
        self.btn_show_path2.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b; color: white; font-weight: bold;
                border-radius: 6px; padding: 8px;
            }
            QPushButton:hover { background-color: #d97706; }
            QPushButton:disabled { background-color: #334155; color: #64748b; }
        """)
        self.btn_show_path2.setEnabled(False)
        
        path_btn_layout.addWidget(self.btn_show_path1)
        path_btn_layout.addWidget(self.btn_show_path2)
        
        layout.addLayout(path_btn_layout)
        
    def _create_combo(self):
        cb = QComboBox()
        for name, key in self.algo_options:
            cb.addItem(name, key)
        cb.setFixedHeight(35)
        cb.setStyleSheet("""
            QComboBox {
                background-color: #334155; color: white; border: 1px solid #475569;
                border-radius: 6px; padding: 0 10px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow {
                image: none; border-top: 5px solid #94a3b8; margin-right: 8px;
                border-left: 5px solid transparent; border-right: 5px solid transparent;
            }
            QComboBox QAbstractItemView {
                background-color: #1e293b; color: white; selection-background-color: #3b82f6;
            }
        """)
        return cb
        
    def _on_compare_clicked(self):
        algo1 = self.combo1.currentData()
        algo2 = self.combo2.currentData()
        self.compare_requested.emit(algo1, algo2)
        self.btn_run.setText("Hesaplanıyor...")
        self.btn_run.setEnabled(False)
        self.info_label.setText("Hesaplanıyor, lütfen bekleyin...")
        self.btn_show_path1.setEnabled(False)
        self.btn_show_path2.setEnabled(False)
        
    def update_results(self, r1: ComparisonResult, r2: ComparisonResult, source: int, dest: int):
        self.btn_run.setText("⚡ Analizi Başlat")
        self.btn_run.setEnabled(True)
        self.info_label.setText(f"Kıyaslanan Güzergah: Düğüm {source} ➔ Düğüm {dest}")
        
        # Store paths
        self.path1 = r1.path
        self.path2 = r2.path
        
        # Update buttons
        self.btn_show_path1.setText(f"{r1.algo_name} Yolunu Göster")
        self.btn_show_path2.setText(f"{r2.algo_name} Yolunu Göster")
        self.btn_show_path1.setEnabled(True)
        self.btn_show_path2.setEnabled(True)
        
        if not MATPLOTLIB_AVAILABLE: return
        
        self.figure.clear()
        
        # Subplot 1: Weighted Cost
        ax1 = self.figure.add_subplot(121, facecolor='#1e293b')
        
        labels = [r1.algo_name, r2.algo_name]
        costs = [r1.weighted_cost if r1.weighted_cost > 0 else r1.cost, 
                 r2.weighted_cost if r2.weighted_cost > 0 else r2.cost]
        colors_cost = ['#3b82f6', '#f59e0b']
        
        bars1 = ax1.bar(labels, costs, color=colors_cost, width=0.4)
        
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.4f}',
                    ha='center', va='bottom', color='white', fontsize=9)
        
        ax1.set_title("Ağırlıklı Maliyet (Daha düşük iyi)", color='#e2e8f0', pad=10)
        ax1.tick_params(axis='x', colors='#cbd5e1', labelsize=9)
        ax1.tick_params(axis='y', colors='#64748b', labelsize=8)
        
        # Subplot 2: Execution Time
        ax2 = self.figure.add_subplot(122, facecolor='#1e293b')
        times = [r1.time, r2.time]
        colors_time = ['#10b981', '#ec4899']
        
        bars2 = ax2.bar(labels, times, color=colors_time, width=0.4)
        
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}ms',
                    ha='center', va='bottom', color='white', fontsize=9)
                    
        ax2.set_title("Çalışma Süresi (ms)", color='#e2e8f0', pad=10)
        ax2.tick_params(axis='x', colors='#cbd5e1', labelsize=9)
        ax2.tick_params(axis='y', colors='#64748b', labelsize=8)
        
        for ax in [ax1, ax2]:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_color('#334155')
            ax.spines['left'].set_visible(False)
            ax.grid(axis='y', alpha=0.1, linestyle='--')
        
        self.figure.tight_layout()
        self.canvas.draw()


class AlgorithmComparisonCard(QFrame):
    """
    Kıyaslama aracını açan küçük kart (Launcher).
    """
    open_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #334155;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Icon
        icon = QLabel("⚖️")
        icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(icon)
        
        # Texts
        text_layout = QVBoxLayout()
        title = QLabel("Algoritma Kıyaslama")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        desc = QLabel("İki algoritmayı detaylı karşılaştırın.")
        desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        text_layout.addWidget(title)
        text_layout.addWidget(desc)
        layout.addLayout(text_layout)
        
        layout.addStretch()
        
        # Button
        btn = QPushButton("Aracı Aç")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6; color: white; font-weight: bold;
                border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { background-color: #2563eb; }
        """)
        btn.clicked.connect(self.open_requested.emit)
        layout.addWidget(btn)

class PresetExperimentCard(QFrame):
    """Hazır 25 testlik deneyi çalıştıran kart."""
    run_requested = pyqtSignal(int) # n_repeats
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #334155;
            }
        """)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header area
        h_layout = QHBoxLayout()
        icon = QLabel("🧪")
        icon.setStyleSheet("font-size: 16px;")
        title = QLabel("Toplu Deney (25 Test)")
        title.setStyleSheet("color: white; font-weight: bold;")
        h_layout.addWidget(icon)
        h_layout.addWidget(title)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        # Content
        desc = QLabel("Önceden belirlenmiş 25 test seti üzerinde tüm algoritmaları çalıştırır.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(desc)
        
        # Repeats input
        row = QHBoxLayout()
        lbl = QLabel("Tekrar:")
        lbl.setStyleSheet("color: #cbd5e1;")
        
        self.spin_repeats = QSpinBox()
        self.spin_repeats.setRange(1, 20)
        self.spin_repeats.setValue(5)
        self.spin_repeats.setPrefix("x")
        self.spin_repeats.setStyleSheet("""
            QSpinBox {
                background-color: #0f172a; color: white; border: 1px solid #475569;
                border-radius: 4px; padding: 2px;
            }
        """)
        
        self.btn_run = QPushButton("Başlat")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #10b981; color: white; font-weight: bold;
                border-radius: 6px; padding: 6px 12px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_run.clicked.connect(lambda: self.run_requested.emit(self.spin_repeats.value()))
        
        row.addWidget(lbl)
        row.addWidget(self.spin_repeats)
        row.addStretch()
        row.addWidget(self.btn_run)
        layout.addLayout(row)
        
    def set_loading(self, loading: bool):
        self.btn_run.setEnabled(not loading)
        self.btn_run.setText("Çalışıyor..." if loading else "Başlat")

class ScalabilityAnalysisCard(QFrame):
    """Ölçeklenebilirlik analizi kartı."""
    run_requested = pyqtSignal(list) # node_counts list
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #334155;
            }
        """)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        h_layout = QHBoxLayout()
        icon = QLabel("📈")
        icon.setStyleSheet("font-size: 16px;")
        title = QLabel("Ölçeklenebilirlik")
        title.setStyleSheet("color: white; font-weight: bold;")
        h_layout.addWidget(icon)
        h_layout.addWidget(title)
        h_layout.addStretch()
        layout.addLayout(h_layout)
        
        desc = QLabel("Düğüm sayısı arttıkça performans değişimini analiz et (20-50 düğüm).")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(desc)
        
        self.btn_run = QPushButton("Analiz Et")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6; color: white; font-weight: bold;
                border-radius: 6px; padding: 6px;
            }
            QPushButton:hover { background-color: #7c3aed; }
        """)
        # Default scenario: 20, 30, 40, 50 nodes
        self.btn_run.clicked.connect(lambda: self.run_requested.emit([20, 30, 40, 50]))
        layout.addWidget(self.btn_run)
        
    def set_loading(self, loading: bool):
        self.btn_run.setEnabled(not loading)
        self.btn_run.setText("Analiz Ediliyor..." if loading else "Analiz Et")

class TestScenariosCard(QFrame):
    """Test senaryoları yükleme kartı."""
    load_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #334155;
            }
        """)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        icon = QLabel("📂")
        icon.setStyleSheet("font-size: 16px;")
        
        info_layout = QVBoxLayout()
        title = QLabel("Test Senaryoları")
        title.setStyleSheet("color: white; font-weight: bold;")
        desc = QLabel("JSON dosyasından yükle")
        desc.setStyleSheet("color: #94a3b8; font-size: 10px;")
        info_layout.addWidget(title)
        info_layout.addWidget(desc)
        
        self.btn_load = QPushButton("Yükle")
        self.btn_load.setCursor(Qt.PointingHandCursor)
        self.btn_load.setFixedSize(60, 30)
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #475569; color: white; font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #64748b; }
        """)
        self.btn_load.clicked.connect(self.load_requested.emit)
        
        layout.addWidget(icon)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(self.btn_load)
        
    def set_loading(self, loading: bool):
        self.btn_load.setEnabled(not loading)


class ExperimentsPanel(QWidget):
    """
    Deney paneli widget'ı.
    """
    run_experiments_requested = pyqtSignal(int, int)
    run_scalability_requested = pyqtSignal(list)
    load_scenarios_requested = pyqtSignal()
    compare_two_requested = pyqtSignal(str, str)
    show_path_requested = pyqtSignal(list, str)
    # New signals for advanced features
    run_pareto_requested = pyqtSignal()  # Pareto optimality analysis
    run_ilp_benchmark_requested = pyqtSignal()  # ILP benchmark comparison
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.comparison_dialog = None
        self._setup_ui()
        
    def _setup_ui(self):
        self.setObjectName("ExperimentsPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            QWidget#ExperimentsPanel {
                background-color: rgba(15, 23, 42, 0.90); /* Slate-900 90% opacity */
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 1. ALGORITHM COMPARISON CARD (Launcher)
        self.compare_card = AlgorithmComparisonCard()
        self.compare_card.open_requested.connect(self._open_comparison_dialog)
        main_layout.addWidget(self.compare_card)
        
        # 2. EXPERIMENTS SECTION (Collapsible)
        # Header
        self.exp_header = QFrame()
        self.exp_header.setCursor(Qt.PointingHandCursor)
        self.exp_header.mousePressEvent = self._toggle_experiments
        self.exp_header.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #1e293b;
            }
        """)
        header_layout = QHBoxLayout(self.exp_header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        icon_label = QLabel("⚗") 
        icon_label.setStyleSheet("color: #0ea5e9; font-size: 20px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("Deney Düzeneği")
        title_label.setStyleSheet("color: #0ea5e9; font-weight: bold; font-size: 16px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.exp_arrow = QLabel("⌄") # Initially expanded
        self.exp_arrow.setStyleSheet("color: #64748b; font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.exp_arrow)
        
        main_layout.addWidget(self.exp_header)
        
        # Experiments Content Container
        self.experiments_container = QWidget()
        exp_layout = QVBoxLayout(self.experiments_container)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        exp_layout.setSpacing(12)
        
        # -- Existing Cards --
        self.preset_card = PresetExperimentCard()
        self.preset_card.run_requested.connect(lambda count: self.run_experiments_requested.emit(25, count))
        exp_layout.addWidget(self.preset_card)
        
        self.scale_card = ScalabilityAnalysisCard()
        self.scale_card.run_requested.connect(self.run_scalability_requested.emit)
        exp_layout.addWidget(self.scale_card)
        
        self.scenarios_card = TestScenariosCard()
        self.scenarios_card.load_requested.connect(self.load_scenarios_requested.emit)
        exp_layout.addWidget(self.scenarios_card)
        
        # -- BONUS FEATURES: Advanced Analysis Cards --
        # Pareto Analysis Card
        self.pareto_card = QFrame()
        self.pareto_card.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #10b981;
            }
        """)
        pareto_layout = QVBoxLayout(self.pareto_card)
        pareto_layout.setContentsMargins(15, 15, 15, 15)
        
        pareto_h = QHBoxLayout()
        pareto_icon = QLabel("🎯")
        pareto_icon.setStyleSheet("font-size: 16px;")
        pareto_title = QLabel("Pareto Optimalite")
        pareto_title.setStyleSheet("color: #10b981; font-weight: bold;")
        pareto_badge = QLabel("EK PUAN")
        pareto_badge.setStyleSheet("background: #10b981; color: white; padding: 2px 6px; border-radius: 4px; font-size: 9px;")
        pareto_h.addWidget(pareto_icon)
        pareto_h.addWidget(pareto_title)
        pareto_h.addStretch()
        pareto_h.addWidget(pareto_badge)
        pareto_layout.addLayout(pareto_h)
        
        pareto_desc = QLabel("Çok amaçlı optimizasyonda Pareto sınırı analizi")
        pareto_desc.setWordWrap(True)
        pareto_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        pareto_layout.addWidget(pareto_desc)
        
        self.btn_pareto = QPushButton("🔍 Analiz Başlat")
        self.btn_pareto.setCursor(Qt.PointingHandCursor)
        self.btn_pareto.setStyleSheet("""
            QPushButton {
                background-color: #10b981; color: white; font-weight: bold;
                border-radius: 6px; padding: 6px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_pareto.clicked.connect(self.run_pareto_requested.emit)
        pareto_layout.addWidget(self.btn_pareto)
        
        exp_layout.addWidget(self.pareto_card)
        
        # ILP Benchmark Card
        self.ilp_card = QFrame()
        self.ilp_card.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #f59e0b;
            }
        """)
        ilp_layout = QVBoxLayout(self.ilp_card)
        ilp_layout.setContentsMargins(15, 15, 15, 15)
        
        ilp_h = QHBoxLayout()
        ilp_icon = QLabel("🔬")
        ilp_icon.setStyleSheet("font-size: 16px;")
        ilp_title = QLabel("ILP Karşılaştırma")
        ilp_title.setStyleSheet("color: #f59e0b; font-weight: bold;")
        ilp_badge = QLabel("EK PUAN")
        ilp_badge.setStyleSheet("background: #f59e0b; color: white; padding: 2px 6px; border-radius: 4px; font-size: 9px;")
        ilp_h.addWidget(ilp_icon)
        ilp_h.addWidget(ilp_title)
        ilp_h.addStretch()
        ilp_h.addWidget(ilp_badge)
        ilp_layout.addLayout(ilp_h)
        
        ilp_desc = QLabel("Meta-sezgisel sonuçları optimal ILP çözümüyle kıyasla")
        ilp_desc.setWordWrap(True)
        ilp_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        ilp_layout.addWidget(ilp_desc)
        
        self.btn_ilp = QPushButton("📊 Benchmark Başlat")
        self.btn_ilp.setCursor(Qt.PointingHandCursor)
        self.btn_ilp.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b; color: white; font-weight: bold;
                border-radius: 6px; padding: 6px;
            }
            QPushButton:hover { background-color: #d97706; }
        """)
        self.btn_ilp.clicked.connect(self.run_ilp_benchmark_requested.emit)
        ilp_layout.addWidget(self.btn_ilp)
        
        exp_layout.addWidget(self.ilp_card)
        
        # -- Requirements Box --
        self.req_box = QFrame()
        self.req_box.setStyleSheet("background-color: #1e293b; border-radius: 8px;")
        req_layout = QVBoxLayout(self.req_box)
        req_layout.setContentsMargins(15, 15, 15, 15)
        req_layout.setSpacing(10)
        
        h_row = QHBoxLayout()
        icon_ok = QLabel("✓")
        icon_ok.setAlignment(Qt.AlignCenter)
        icon_ok.setFixedSize(24, 24)
        icon_ok.setStyleSheet("color: #10b981; border: 2px solid #10b981; border-radius: 12px; font-weight: bold;")
        h_row.addWidget(icon_ok)
        
        lbl_title = QLabel("Test Gereksinimleri:")
        lbl_title.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 13px;")
        h_row.addWidget(lbl_title)
        
        h_row.addStretch()
        req_layout.addLayout(h_row)
        
        requirements = [
            "20+ farklı (S, D, B) örneği ✓",
            "5 tekrar + istatistik ✓",
            "Başarısız örnekler + gerekçe ✓",
            "Çalışma süresi ✓",
            "Ölçeklenebilirlik (opsiyonel) ✓"
        ]
        
        for req in requirements:
             r_row = QHBoxLayout()
             dot = QLabel("•")
             dot.setStyleSheet("color: #64748b;")
             r_row.addWidget(dot)
             lbl = QLabel(req)
             lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
             r_row.addWidget(lbl)
             r_row.addStretch()
             req_layout.addLayout(r_row)

        exp_layout.addWidget(self.req_box)
        
        main_layout.addWidget(self.experiments_container)
        main_layout.addStretch()
        
        self.is_experiments_expanded = True

    def _toggle_experiments(self, event=None):
        self.is_experiments_expanded = not self.is_experiments_expanded
        self.experiments_container.setVisible(self.is_experiments_expanded)
        self.exp_arrow.setText("⌄" if self.is_experiments_expanded else "›")

    def _open_comparison_dialog(self):
        """Kıyaslama penceresini aç."""
        if self.comparison_dialog is None:
            self.comparison_dialog = AlgorithmComparisonDialog(self)
            self.comparison_dialog.compare_requested.connect(self.compare_two_requested.emit)
            self.comparison_dialog.show_path_requested.connect(self.show_path_requested.emit)
        
        self.comparison_dialog.show()
        self.comparison_dialog.raise_()
        self.comparison_dialog.activateWindow()

    def update_comparison_results(self, algo1_name, cost1, time1, path1, algo2_name, cost2, time2, path2, source: int, dest: int):
        """Kıyaslama sonuçlarını açık olan pencereye gönder."""
        if self.comparison_dialog and self.comparison_dialog.isVisible():
            r1 = ComparisonResult(algo1_name, 0, time1, weighted_cost=cost1, path=path1)
            r2 = ComparisonResult(algo2_name, 0, time2, weighted_cost=cost2, path=path2)
            self.comparison_dialog.update_results(r1, r2, source, dest)
            
    def _create_action_button(self, icon, text, bg_color):
        btn = QPushButton()
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border: none;
                border-radius: 8px;
                padding: 12px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: #475569;
            }}
        """)
        
        l = QHBoxLayout(btn)
        l.setContentsMargins(5, 5, 5, 5)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("color: #94a3b8; font-size: 16px;")
        l.addWidget(icon_lbl)
        
        text_lbl = QLabel(text)
        text_lbl.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 13px;")
        l.addWidget(text_lbl)
        
        l.addStretch()
        
        arrow_lbl = QLabel("›")
        arrow_lbl.setStyleSheet("color: #64748b; font-size: 18px; font-weight: bold;")
        l.addWidget(arrow_lbl)
        
        return btn

    def set_loading(self, loading: bool):
        self.preset_card.set_loading(loading)
        self.scale_card.set_loading(loading)
        self.scenarios_card.set_loading(loading)

    def set_progress(self, current, total):
        pass

    def set_finished(self, summary):
        pass
