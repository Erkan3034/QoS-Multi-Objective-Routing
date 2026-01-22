from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QFrame, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QFont

class HeaderWidget(QWidget):
    """
    Header bileşeni - Logo, başlık ve graf bilgileri gösterir.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)  # Biraz daha yüksek
        self.setAutoFillBackground(True)
        
        # Arka plan rengi
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            HeaderWidget {
                background-color: rgba(15, 23, 42, 0.85); /* Slate-900 85% opacity */
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0) # Margins
        layout.setSpacing(16)
        
        # Logo Icon
        logo_container = QLabel("🕸️")
        logo_container.setAlignment(Qt.AlignCenter)
        logo_container.setFixedSize(48, 48)
        logo_container.setStyleSheet("""
            background-color: #3b82f6; 
            border-radius: 12px;
            font-size: 28px;
        """)
        layout.addWidget(logo_container)
        
        # Başlık ve Alt Başlık (Dikey Layout)
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        title_layout.setAlignment(Qt.AlignVCenter)
        
        title = QLabel("QoS Routing Optimizer")
        title.setStyleSheet("""
            color: #f1f5f9;  /* slate-100 */
            font-family: 'Segoe UI', 'sans-serif';
            font-size: 20px;
            font-weight: 700;
        """)
        
        subtitle = QLabel("")
        subtitle.setStyleSheet("""
            color: #94a3b8; /* slate-400 */
            font-family: 'Segoe UI', 'sans-serif';
            font-size: 13px;
            font-weight: 500;
        """) 
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addWidget(title_container)
        
        layout.addStretch()
        
        # Sağ Taraf İstatistikleri
        self.stats_container = QWidget()
        stats_layout = QHBoxLayout(self.stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(24)
        
        # Düğüm Sayısı label
        self.node_count_label = QLabel("Düğüm: 250")
        self.node_count_label.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 14px;")
        stats_layout.addWidget(self.node_count_label)
        
        # Kenar Sayısı label
        self.edge_count_label = QLabel("Kenar: 12442")
        self.edge_count_label.setStyleSheet("color: #cbd5e1; font-weight: 600; font-size: 14px;")
        stats_layout.addWidget(self.edge_count_label)
        
        # Badge (Bağlı / Bağlı Değil)
        self.status_badge = QLabel("Bağlı")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setFixedSize(60, 26)
        # Default Green style
        self.status_badge.setStyleSheet("""
            background-color: #059669; /* emerald-600 */
            color: white;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
        """)
        stats_layout.addWidget(self.status_badge)
        
        layout.addWidget(self.stats_container)
        
        # Alt çizgi (Separator) - İsteğe bağlı, resimde çok belirgin değil ama hafif var
        # line = QFrame(self)
        # line.setFrameShape(QFrame.HLine)
        # line.setStyleSheet("background-color: #1e293b;") # Çok silik
        # line.setGeometry(0, 79, 3000, 1)

    def update_stats(self, n_nodes: int, n_edges: int, connected: bool):
        """İstatistikleri güncelle."""
        self.node_count_label.setText(f"Düğüm: {n_nodes}")
        self.edge_count_label.setText(f"Kenar: {n_edges}")
        
        if connected:
            self.status_badge.setText("Bağlı")
            self.status_badge.setStyleSheet("""
                background-color: #059669; 
                color: white;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            """)
        else:
            self.status_badge.setText("Kopuk")
            self.status_badge.setStyleSheet("""
                background-color: #dc2626; 
                color: white;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            """)
