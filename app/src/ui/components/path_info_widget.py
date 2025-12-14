from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class PathInfoWidget(QWidget):
    """
    Bulunan yol bilgisi widget'ı.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PathInfoWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        self.setStyleSheet("""
            QWidget#PathInfoWidget {
                background-color: #1e293b; /* slate-800 */
                border: 1px solid #334155;
                border-radius: 12px;
            }
            QLabel {
                color: #f1f5f9;
            }
        """)
        self.setFixedWidth(180) # Smaller width
        self.hide()
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8) # Compact margins
        layout.setSpacing(2)
        
        title = QLabel("Bulunan Yol")
        title.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 10px;")
        layout.addWidget(title)
        
        self.path_label = QLabel("")
        self.path_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #f8fafc;")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)
        
    def update_path(self, path: list):
        """Yol bilgisini güncelle."""
        if not path:
            self.hide()
            return
            
        self.show()
        hops = len(path) - 1
        
        if len(path) > 6:
            # Kısaltılmış gösterim: 0 -> 23 -> ... -> 249
            path_str = f"{path[0]} → {path[1]} → ... → {path[-1]}"
        else:
            path_str = " → ".join(map(str, path))
            
        self.path_label.setText(f"{hops} hop: {path_str}")
        
        # Ensure widget resizes to fit content
        self.adjustSize()
