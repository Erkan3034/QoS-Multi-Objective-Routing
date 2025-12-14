from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette

class FooterWidget(QWidget):
    """
    Footer bileşeni - Algoritma listesi ve copyright.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setAutoFillBackground(True)
        
        # Arka plan rengi
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("#111827"))
        self.setPalette(palette)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        

        
        # Metin
        text = "BSM307 QoS Routing • GA • ACO • PSO • SA • Q-Learning • SARSA"
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            color: #64748b;
            font-size: 11px;
            font-weight: 500;
        """)
        
        layout.addWidget(label)
