"""
Graf Görselleştirme Widget - PyQtGraph ile yüksek performanslı render
"""
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor
from typing import Dict, List, Optional, Set
import networkx as nx


class GraphWidget(QWidget):
    """
    Performanslı graf görselleştirme widget'ı.
    
    PyQtGraph kullanarak 250+ düğümlü grafları sorunsuz render eder.
    """
    
    node_clicked = pyqtSignal(int)  # Düğüm tıklandığında sinyal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph: Optional[nx.Graph] = None
        self.positions: Dict[int, tuple] = {}
        self.path: List[int] = []
        self.source: Optional[int] = None
        self.destination: Optional[int] = None
        
        # Node scatter plots
        self.node_scatter = None
        self.path_scatter = None
        self.source_scatter = None
        self.dest_scatter = None
        
        # Edge lines
        self.edge_lines = None
        self.path_lines = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UI kurulumu."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # PyQtGraph plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#0f172a')  # slate-900
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.showGrid(x=False, y=False)
        self.plot_widget.hideAxis('left')
        self.plot_widget.hideAxis('bottom')
        
        # Mouse interaction
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        
        layout.addWidget(self.plot_widget)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.btn_zoom_in = QPushButton("➕")
        self.btn_zoom_in.setFixedSize(32, 32)
        self.btn_zoom_in.clicked.connect(self._zoom_in)
        
        self.btn_zoom_out = QPushButton("➖")
        self.btn_zoom_out.setFixedSize(32, 32)
        self.btn_zoom_out.clicked.connect(self._zoom_out)
        
        self.btn_fit = QPushButton("⬜")
        self.btn_fit.setFixedSize(32, 32)
        self.btn_fit.clicked.connect(self._fit_view)
        self.btn_fit.setToolTip("Sığdır")
        
        self.info_label = QLabel("Graf yüklenmedi")
        self.info_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        
        btn_layout.addWidget(self.btn_zoom_in)
        btn_layout.addWidget(self.btn_zoom_out)
        btn_layout.addWidget(self.btn_fit)
        btn_layout.addStretch()
        btn_layout.addWidget(self.info_label)
        
        layout.addLayout(btn_layout)
        
        # Style buttons
        btn_style = """
            QPushButton {
                background-color: #334155;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #475569;
            }
        """
        self.btn_zoom_in.setStyleSheet(btn_style)
        self.btn_zoom_out.setStyleSheet(btn_style)
        self.btn_fit.setStyleSheet(btn_style)
    
    def set_graph(self, graph: nx.Graph, positions: Dict[int, tuple] = None):
        """Graf verisi ayarla ve çiz."""
        self.graph = graph
        
        if positions:
            self.positions = positions
        else:
            # Spring layout hesapla
            self.positions = nx.spring_layout(
                graph, seed=42, k=2/np.sqrt(graph.number_of_nodes())
            )
        
        self._draw_graph()
        self._fit_view()
        
        self.info_label.setText(
            f"Düğüm: {graph.number_of_nodes()} | Kenar: {graph.number_of_edges()}"
        )
    
    def set_path(self, path: List[int]):
        """Bulunan yolu işaretle."""
        self.path = path
        self._update_path_display()
    
    def set_source_destination(self, source: Optional[int], destination: Optional[int]):
        """Kaynak ve hedef düğümleri ayarla."""
        self.source = source
        self.destination = destination
        self._update_special_nodes()
    
    def _draw_graph(self):
        """Grafı çiz."""
        if self.graph is None:
            return
        
        self.plot_widget.clear()
        
        # Pozisyonları numpy array'e çevir
        n_nodes = self.graph.number_of_nodes()
        pos_array = np.zeros((n_nodes, 2))
        for node, (x, y) in self.positions.items():
            pos_array[node] = [x, y]
        
        # Kenarları çiz
        edge_x = []
        edge_y = []
        for u, v in self.graph.edges():
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            edge_x.extend([x1, x2, None])
            edge_y.extend([y1, y2, None])
        
        self.edge_lines = self.plot_widget.plot(
            edge_x, edge_y,
            pen=pg.mkPen(color=(71, 85, 105, 40), width=0.5),
            connect='finite'
        )
        
        # Düğümleri çiz
        self.node_scatter = pg.ScatterPlotItem(
            pos=pos_array,
            size=8,
            brush=pg.mkBrush(100, 116, 139, 200),
            pen=pg.mkPen(None),
            hoverable=True
        )
        self.plot_widget.addItem(self.node_scatter)
        
        # Path için boş scatter (sonra doldurulacak)
        self.path_scatter = pg.ScatterPlotItem(size=14, brush=pg.mkBrush(245, 158, 11, 255))
        self.plot_widget.addItem(self.path_scatter)
        
        # Source scatter
        self.source_scatter = pg.ScatterPlotItem(size=20, brush=pg.mkBrush(34, 197, 94, 255))
        self.plot_widget.addItem(self.source_scatter)
        
        # Destination scatter
        self.dest_scatter = pg.ScatterPlotItem(size=20, brush=pg.mkBrush(239, 68, 68, 255))
        self.plot_widget.addItem(self.dest_scatter)
        
        # Path lines
        self.path_lines = self.plot_widget.plot(
            [], [],
            pen=pg.mkPen(color=(245, 158, 11, 255), width=4),
            connect='finite'
        )
    
    def _update_path_display(self):
        """Yol görselleştirmesini güncelle."""
        if not self.path or len(self.path) < 2:
            self.path_scatter.setData(pos=[])
            self.path_lines.setData([], [])
            return
        
        # Path düğümlerini işaretle
        path_pos = np.array([self.positions[n] for n in self.path[1:-1]])  # Source/dest hariç
        if len(path_pos) > 0:
            self.path_scatter.setData(pos=path_pos)
        
        # Path kenarlarını çiz
        edge_x = []
        edge_y = []
        for i in range(len(self.path) - 1):
            x1, y1 = self.positions[self.path[i]]
            x2, y2 = self.positions[self.path[i + 1]]
            edge_x.extend([x1, x2, None])
            edge_y.extend([y1, y2, None])
        
        self.path_lines.setData(edge_x, edge_y)
    
    def _update_special_nodes(self):
        """Kaynak ve hedef düğümlerini güncelle."""
        if self.source is not None and self.source in self.positions:
            self.source_scatter.setData(pos=[self.positions[self.source]])
        else:
            self.source_scatter.setData(pos=[])
        
        if self.destination is not None and self.destination in self.positions:
            self.dest_scatter.setData(pos=[self.positions[self.destination]])
        else:
            self.dest_scatter.setData(pos=[])
    
    def _on_mouse_clicked(self, event):
        """Mouse tıklama olayı."""
        if self.graph is None:
            return
        
        pos = event.scenePos()
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        
        # En yakın düğümü bul
        min_dist = float('inf')
        closest_node = None
        
        for node, (x, y) in self.positions.items():
            dist = (mouse_point.x() - x) ** 2 + (mouse_point.y() - y) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_node = node
        
        # Eşik mesafe kontrolü
        if min_dist < 0.01:  # Tıklama mesafesi eşiği
            self.node_clicked.emit(closest_node)
    
    def _zoom_in(self):
        """Yakınlaştır."""
        self.plot_widget.plotItem.vb.scaleBy((0.7, 0.7))
    
    def _zoom_out(self):
        """Uzaklaştır."""
        self.plot_widget.plotItem.vb.scaleBy((1.3, 1.3))
    
    def _fit_view(self):
        """Tümünü göster."""
        self.plot_widget.plotItem.vb.autoRange()
    
    def clear(self):
        """Grafı temizle."""
        self.graph = None
        self.positions = {}
        self.path = []
        self.source = None
        self.destination = None
        self.plot_widget.clear()
        self.info_label.setText("Graf yüklenmedi")

