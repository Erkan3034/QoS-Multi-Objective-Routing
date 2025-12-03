#!/usr/bin/env python3
"""
QoS Multi-Objective Routing - PyQt5 Desktop Application

Kullanım:
    python main.py

Gereksinimler:
    pip install -r requirements.txt
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

from src.ui.main_window import MainWindow


def setup_dark_palette(app: QApplication):
    """Karanlık tema ayarla."""
    palette = QPalette()
    
    # Renkler
    palette.setColor(QPalette.Window, QColor(15, 23, 42))  # slate-900
    palette.setColor(QPalette.WindowText, QColor(226, 232, 240))  # slate-200
    palette.setColor(QPalette.Base, QColor(30, 41, 59))  # slate-800
    palette.setColor(QPalette.AlternateBase, QColor(51, 65, 85))  # slate-700
    palette.setColor(QPalette.ToolTipBase, QColor(30, 41, 59))
    palette.setColor(QPalette.ToolTipText, QColor(226, 232, 240))
    palette.setColor(QPalette.Text, QColor(226, 232, 240))
    palette.setColor(QPalette.Button, QColor(51, 65, 85))
    palette.setColor(QPalette.ButtonText, QColor(226, 232, 240))
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, QColor(59, 130, 246))  # blue-500
    palette.setColor(QPalette.Highlight, QColor(59, 130, 246))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    app.setPalette(palette)


def main():
    """Ana giriş noktası."""
    # High DPI desteği
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("QoS Routing Desktop")
    app.setOrganizationName("BSM307")
    
    # Font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Karanlık tema
    setup_dark_palette(app)
    
    # Ana pencere
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

