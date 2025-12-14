from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLayout, QStyle, QStyleOption
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter

class LegendWidget(QWidget):
    """
    Graf açıklaması (Legend).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LegendWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            QWidget#LegendWidget {
                background-color: transparent;
                border: none;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        self._setup_ui()

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8) # Increased padding for robustness
        layout.setSpacing(16) # Increased spacing
        layout.setSizeConstraint(QLayout.SetFixedSize) # Force widget to fit content
        
        # Kaynak (Circle with S)
        self._add_item(layout, "#22c55e", "Kaynak", symbol="S")
        
        # Hedef (Circle with D)  
        self._add_item(layout, "#ef4444", "Hedef", symbol="D")
        
        # Yol (Line)
        self._add_item(layout, "#f59e0b", "Yol", shape="line")
        
        # Diğer (Circle)
        self._add_item(layout, "#475569", "Diğer")
        
        self.adjustSize()
        
    def _add_item(self, layout, color, text, symbol=None, shape="circle"):
        item = QWidget()
        l = QHBoxLayout(item)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)
        l.setAlignment(Qt.AlignVCenter) # Strict horizontal alignment
        
        # Icon
        icon = QLabel()
        
        if shape == "line":
            icon.setFixedSize(16, 4) # Reduced width
            icon.setStyleSheet(f"""
                background-color: {color};
                border-radius: 2px;
            """)
        else:
            # Circle
            icon.setFixedSize(14, 14) # Reduced size
            if symbol:
                icon.setText(symbol)
                icon.setAlignment(Qt.AlignCenter)
                icon.setStyleSheet(f"""
                    background-color: {color};
                    border-radius: 7px;
                    color: white;
                    font-size: 9px;
                    font-weight: bold;
                """)
            else:
                icon.setStyleSheet(f"""
                    background-color: {color};
                    border-radius: 7px;
                """)
                
        l.addWidget(icon)
        
        # Text
        lbl = QLabel(text)
        l.addWidget(lbl)
        
        layout.addWidget(item)
