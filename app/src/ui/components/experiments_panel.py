from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSpinBox, QGraphicsOpacityEffect,
    QSizePolicy, QLineEdit
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize, QParallelAnimationGroup
from PyQt5.QtGui import QIcon

class PresetExperimentCard(QFrame):
    """
    Önceden tanımlı deneyler için genişleyebilir kart.
    """
    run_requested = pyqtSignal(int)  # repeat_count sends
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self._setup_ui()
        
    def _setup_ui(self):
        self.setObjectName("PresetCard")
        self.setStyleSheet("""
            QFrame#PresetCard {
                background-color: #1e293b; 
                border-radius: 16px;
                border: 1px solid #1f2937;
            }
            QFrame#PresetCard:hover {
                border: 1px solid #334155;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # === HEADER (Always Visible) ===
        self.header_frame = QFrame()
        self.header_frame.setCursor(Qt.PointingHandCursor)
        self.header_frame.mousePressEvent = self._toggle_expand
        self.header_frame.setStyleSheet("background: transparent;")
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(15, 12, 15, 12)
        header_layout.setSpacing(10)
        
        # Icon ("play" triangle)
        self.icon_label = QLabel("▷")
        self.icon_label.setStyleSheet("color: #10b981; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.icon_label)
        
        # Title
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        self.title_lbl = QLabel("Önceden Tanımlı Deneyler")
        self.title_lbl.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 14px;")
        title_box.addWidget(self.title_lbl)
        
        self.subtitle_lbl = QLabel("(25 Test)")
        self.subtitle_lbl.setStyleSheet("color: #94a3b8; font-weight: 500; font-size: 12px;")
        title_box.addWidget(self.subtitle_lbl)
        
        header_layout.addLayout(title_box)
        header_layout.addStretch()
        
        # Arrow (Right >)
        self.arrow_lbl = QLabel("›") 
        self.arrow_lbl.setStyleSheet("color: #64748b; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.arrow_lbl)
        
        self.main_layout.addWidget(self.header_frame)
        
        # === CONTENT (Collapsible) ===
        # === CONTENT (Collapsible) ===
        self.content_frame = QFrame()
        self.content_frame.setObjectName("ContentFrame")
        self.content_frame.setStyleSheet("""
            QFrame#ContentFrame {
                background-color: rgba(0, 0, 0, 0.2);
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }
        """)
        self.content_frame.setVisible(False)
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        # Description
        desc_lbl = QLabel(
            "20+ farklı (S, D, B) örneği ile deney\n"
            "çalıştır. Her test 5 kez tekrarlanır ve\n"
            "istatistikler hesaplanır."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        content_layout.addWidget(desc_lbl)
        
        # Controls Row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        lbl_repeat = QLabel("Tekrar Sayısı:")
        lbl_repeat.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 13px;")
        controls_layout.addWidget(lbl_repeat)
        
        self.spin_repeat = QSpinBox()
        self.spin_repeat.setRange(1, 20)
        self.spin_repeat.setValue(5)
        self.spin_repeat.setFixedWidth(60)
        self.spin_repeat.setFixedHeight(30)
        self.spin_repeat.setStyleSheet("""
            QSpinBox {
                background-color: #334155;
                color: white;
                border: 1px solid #475569;
                border-radius: 8px;
                padding: 0 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QSpinBox:focus {
                border: 1px solid #3b82f6;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }
        """)
        controls_layout.addWidget(self.spin_repeat)
        controls_layout.addStretch()
        
        content_layout.addLayout(controls_layout)
        
        # Run Button
        self.btn_run = QPushButton("▷ Deneyleri Çalıştır")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setFixedHeight(38)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #10b981; /* Emerald 500 */
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #059669; /* Emerald 600 */
            }
            QPushButton:pressed {
                background-color: #047857;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.btn_run.clicked.connect(self._on_run_clicked)
        content_layout.addWidget(self.btn_run)
        
        self.main_layout.addWidget(self.content_frame)
        
    def _toggle_expand(self, event=None):
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content_frame.setVisible(True)
            self.arrow_lbl.setText("⌄") # Down arrow
            self.icon_label.setText("▼") # Or some other indicator if needed
             # Adjust styling for expanded state if needed
            self.header_frame.setStyleSheet("background: transparent;")
        else:
            self.content_frame.setVisible(False)
            self.arrow_lbl.setText("›") # Right arrow
            self.icon_label.setText("▷")
            self.header_frame.setStyleSheet("background: transparent; border-bottom: none;")
            
    def _on_run_clicked(self):
        self.run_requested.emit(self.spin_repeat.value())
        
    def set_loading(self, loading: bool):
        self.btn_run.setEnabled(not loading)
        self.spin_repeat.setEnabled(not loading)
        self.header_frame.setEnabled(not loading)


class ScalabilityAnalysisCard(QFrame):
    """
    Ölçeklenebilirlik analizi için genişleyebilir kart.
    """
    run_requested = pyqtSignal(list)  # [50, 100, 150...]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self._setup_ui()
        
    def _setup_ui(self):
        self.setObjectName("ScaleCard")
        self.setStyleSheet("""
            QFrame#ScaleCard {
                background-color: #1e293b; 
                border-radius: 16px;
                border: 1px solid #1f2937;
            }
            QFrame#ScaleCard:hover {
                border: 1px solid #334155;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # === HEADER (Always Visible) ===
        self.header_frame = QFrame()
        self.header_frame.setCursor(Qt.PointingHandCursor)
        self.header_frame.mousePressEvent = self._toggle_expand
        self.header_frame.setStyleSheet("background: transparent;")
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(15, 12, 15, 12)
        header_layout.setSpacing(10)
        
        # Icon ("trend" / arrow)
        self.icon_label = QLabel("↗")
        self.icon_label.setStyleSheet("color: #3b82f6; font-size: 16px; font-weight: bold;")
        header_layout.addWidget(self.icon_label)
        
        # Title
        self.title_lbl = QLabel("Ölçeklenebilirlik Analizi")
        self.title_lbl.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_lbl)
        
        header_layout.addStretch()
        
        # Arrow (Right >)
        self.arrow_lbl = QLabel("›") 
        self.arrow_lbl.setStyleSheet("color: #64748b; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.arrow_lbl)
        
        self.main_layout.addWidget(self.header_frame)
        
        # === CONTENT (Collapsible) ===
        # === CONTENT (Collapsible) ===
        self.content_frame = QFrame()
        self.content_frame.setObjectName("ContentFrame")
        self.content_frame.setStyleSheet("""
            QFrame#ContentFrame {
                background-color: rgba(0, 0, 0, 0.2);
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }
        """)
        self.content_frame.setVisible(False)
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        # Description
        desc_lbl = QLabel(
            "Farklı graf boyutları için algoritma\n"
            "performanslarını ölçer. (Opsiyonel\n"
            "gereksinim)"
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        content_layout.addWidget(desc_lbl)
        
        # Input Row
        input_container = QVBoxLayout()
        input_container.setSpacing(6)
        
        lbl_nodes = QLabel("Düğüm Sayıları (virgülle ayrılmış):")
        lbl_nodes.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 13px;")
        input_container.addWidget(lbl_nodes)
        
        self.input_nodes = QLineEdit("50,100,150,200,250")
        self.input_nodes.setFixedHeight(36)
        self.input_nodes.setStyleSheet("""
            QLineEdit {
                background-color: #334155;
                color: white;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 0 10px;
                font-weight: 500;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        input_container.addWidget(self.input_nodes)
        content_layout.addLayout(input_container)
        
        # Run Button
        self.btn_run = QPushButton("↗ Analizi Çalıştır")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setFixedHeight(38)
        self.btn_run.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; /* Blue 600 */
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1d4ed8; /* Blue 700 */
            }
            QPushButton:pressed {
                background-color: #1e40af;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.btn_run.clicked.connect(self._on_run_clicked)
        content_layout.addWidget(self.btn_run)
        
        self.main_layout.addWidget(self.content_frame)
        
    def _toggle_expand(self, event=None):
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content_frame.setVisible(True)
            self.arrow_lbl.setText("⌄")
            self.header_frame.setStyleSheet("background: transparent;")
        else:
            self.content_frame.setVisible(False)
            self.arrow_lbl.setText("›")
            self.header_frame.setStyleSheet("background: transparent; border-bottom: none;")
            
    def _on_run_clicked(self):
        text = self.input_nodes.text()
        try:
            # Parse nodes
            nodes = [int(x.strip()) for x in text.split(",") if x.strip().isdigit()]
            if not nodes:
                nodes = [50, 100, 150, 200, 250]
            self.run_requested.emit(nodes)
        except ValueError:
            pass # Handle error appropriately or ignore
        
    def set_loading(self, loading: bool):
        self.btn_run.setEnabled(not loading)
        self.input_nodes.setEnabled(not loading)
        self.header_frame.setEnabled(not loading)


class TestScenariosCard(QFrame):
    """
    Test senaryoları için genişleyebilir kart.
    """
    load_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self._setup_ui()
        
    def _setup_ui(self):
        self.setObjectName("ScenariosCard")
        self.setStyleSheet("""
            QFrame#ScenariosCard {
                background-color: #1e293b; 
                border-radius: 16px;
                border: 1px solid #1f2937;
            }
            QFrame#ScenariosCard:hover {
                border: 1px solid #334155;
            }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        # === HEADER (Always Visible) ===
        self.header_frame = QFrame()
        self.header_frame.setCursor(Qt.PointingHandCursor)
        self.header_frame.mousePressEvent = self._toggle_expand
        self.header_frame.setStyleSheet("background: transparent;")
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(15, 12, 15, 12)
        header_layout.setSpacing(10)
        
        # Icon ("stopwatch")
        self.icon_label = QLabel("⏱")
        self.icon_label.setStyleSheet("color: #a855f7; font-size: 18px;") # Purple
        header_layout.addWidget(self.icon_label)
        
        # Title
        self.title_lbl = QLabel("Test Senaryoları (S, D, B)")
        self.title_lbl.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.title_lbl)
        
        header_layout.addStretch()
        
        # Arrow (Right >)
        self.arrow_lbl = QLabel("›") 
        self.arrow_lbl.setStyleSheet("color: #64748b; font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.arrow_lbl)
        
        self.main_layout.addWidget(self.header_frame)
        
        # === CONTENT (Collapsible) ===
        # === CONTENT (Collapsible) ===
        self.content_frame = QFrame()
        self.content_frame.setObjectName("ContentFrame")
        self.content_frame.setStyleSheet("""
            QFrame#ContentFrame {
                background-color: rgba(0, 0, 0, 0.2);
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }
        """)
        self.content_frame.setVisible(False)
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        
        # Description
        desc_lbl = QLabel("25 önceden tanımlanmış (S, D, B)\nkombinasyonu.")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        content_layout.addWidget(desc_lbl)
        
        # Load Button
        self.btn_load = QPushButton("Test Senaryolarını\nYükle")
        self.btn_load.setIcon(QIcon("")) # In case we want icon later, or remove this line
        # Use text with clock icon if desired, or just text. Screenshot shows clock icon inside button left.
        # "🕑 Test Senaryolarını Yükle"
        self.btn_load.setText("🕑   Test Senaryolarını\n       Yükle") 
        # Making it look like the screenshot (multiline text centered possibly, or just icon left)
        # Screenshot: Icon left, Text centered/left.
        # Let's use simple text for now or HTML.
        
        self.btn_load.setCursor(Qt.PointingHandCursor)
        self.btn_load.setFixedHeight(45)
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #a855f7; /* Purple 500 */
                color: white;
                font-weight: bold;
                border-radius: 8px;
                font-size: 14px;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #9333ea; /* Purple 600 */
            }
            QPushButton:pressed {
                background-color: #7e22ce;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.btn_load.clicked.connect(lambda: self.load_requested.emit())
        content_layout.addWidget(self.btn_load)
        
        self.main_layout.addWidget(self.content_frame)
        
    def _toggle_expand(self, event=None):
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.content_frame.setVisible(True)
            self.arrow_lbl.setText("⌄")
            self.header_frame.setStyleSheet("background: transparent;")
        else:
            self.content_frame.setVisible(False)
            self.arrow_lbl.setText("›")
            self.header_frame.setStyleSheet("background: transparent; border-bottom: none;")
            
    def set_loading(self, loading: bool):
        self.btn_load.setEnabled(not loading)
        self.header_frame.setEnabled(not loading)


class ExperimentsPanel(QWidget):
    """
    Deney paneli widget'ı.
    """
    run_experiments_requested = pyqtSignal(int, int)
    run_scalability_requested = pyqtSignal(list)
    load_scenarios_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(320)
        self._setup_ui()
        
    def _setup_ui(self):
        self.setObjectName("ExperimentsPanel")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Card Styling
        self.setStyleSheet("""
            QWidget#ExperimentsPanel {
                background-color: #111827;
                border-radius: 16px;
                border: 1px solid #1f2937;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # === HEADER ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        icon_label = QLabel("⚗") # Beaker icon substitute
        icon_label.setStyleSheet("color: #0ea5e9; font-size: 20px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel("Deney Düzeneği")
        title_label.setStyleSheet("color: #0ea5e9; font-weight: bold; font-size: 16px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # === BUTTONS ===
        # 1. Preset Experiments (Collapsible Card)
        self.preset_card = PresetExperimentCard()
        # Initial request: 25 tests, value from spinbox
        self.preset_card.run_requested.connect(lambda count: self.run_experiments_requested.emit(25, count))
        layout.addWidget(self.preset_card)
        
        # 2. Scalability Analysis (Collapsible Card)
        self.scale_card = ScalabilityAnalysisCard()
        self.scale_card.run_requested.connect(self.run_scalability_requested.emit)
        layout.addWidget(self.scale_card)
        
        # 3. Test Scenarios (Collapsible Card)
        self.scenarios_card = TestScenariosCard()
        self.scenarios_card.load_requested.connect(self.load_scenarios_requested.emit)
        layout.addWidget(self.scenarios_card)
        
        # === REQUIREMENTS BOX ===
        req_box = QFrame()
        req_box.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border-radius: 8px;
            }
        """)
        req_layout = QVBoxLayout(req_box)
        req_layout.setContentsMargins(20, 20, 20, 20)
        req_layout.setSpacing(12)
        
        # Header Row
        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        header_row.setContentsMargins(0, 0, 0, 5)
        
        # Use a specific icon or styled label matching the image (Green circled check)
        # Using a unicode char or styled label for now. Image shows a green circle with check.
        icon_lbl = QLabel("✓") 
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(24, 24)
        icon_lbl.setStyleSheet("""
            QLabel {
                color: #10b981; 
                border: 2px solid #10b981; 
                border-radius: 12px; 
                font-weight: bold; 
                font-size: 14px;
                background: transparent;
            }
        """)
        header_row.addWidget(icon_lbl)
        
        req_title = QLabel("Test Gereksinimleri:")
        req_title.setStyleSheet("color: #cbd5e1; font-weight: bold; font-size: 13px;")
        header_row.addWidget(req_title)
        header_row.addStretch()
        
        req_layout.addLayout(header_row)
        
        requirements = [
            "20+ farklı (S, D, B) örneği ✓",
            "5 tekrar + istatistik ✓",
            "Başarısız örnekler + gerekçe ✓",
            "Çalışma süresi ✓",
            "Ölçeklenebilirlik (opsiyonel) ✓"
        ]
        
        # Indented list container
        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(34, 0, 0, 0) # Identation matching icon width + spacing
        list_layout.setSpacing(8)
        
        for req in requirements:
            # Bullet point style dot
            item_row = QHBoxLayout()
            item_row.setSpacing(8)
            
            dot = QLabel("•")
            dot.setStyleSheet("color: #64748b; font-size: 14px;")
            dot.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            
            lbl = QLabel(req)
            lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
            
            item_row.addWidget(dot)
            item_row.addWidget(lbl)
            item_row.addStretch()
            
            list_layout.addLayout(item_row)
            
        req_layout.addLayout(list_layout)
        
        layout.addWidget(req_box)
        layout.addStretch()

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
        pass # Optional: update progress bar if added

    def set_finished(self, summary):
        pass # Optional: show summary dialog
