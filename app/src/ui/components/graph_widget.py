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
        pos_array = np.zeros((n_nodes, 2), dtype=np.float64)
        for node, (x, y) in self.positions.items():
            pos_array[node] = [float(x), float(y)]
        
        # Kenarları çiz - np.nan kullanarak ayrı segmentler oluştur
        n_edges = self.graph.number_of_edges()
        if n_edges > 0:
            # Her kenar için 3 nokta: başlangıç, bitiş, nan (ayırıcı)
            edge_x = np.zeros(n_edges * 3, dtype=np.float64)
            edge_y = np.zeros(n_edges * 3, dtype=np.float64)
            
            for i, (u, v) in enumerate(self.graph.edges()):
                x1, y1 = self.positions[u]
                x2, y2 = self.positions[v]
                idx = i * 3
                edge_x[idx] = float(x1)
                edge_x[idx + 1] = float(x2)
                edge_x[idx + 2] = np.nan  # Segment ayırıcı
                edge_y[idx] = float(y1)
                edge_y[idx + 1] = float(y2)
                edge_y[idx + 2] = np.nan
            
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
        
        # Path lines - başlangıçta çizme, sadece placeholder oluştur
        self.path_lines = None
    
    def _update_path_display(self):
        """Yol görselleştirmesini güncelle."""
        # Önceki path lines'ı kaldır
        if self.path_lines is not None:
            self.plot_widget.removeItem(self.path_lines)
            self.path_lines = None
        
        if not self.path or len(self.path) < 2:
            # Boş durumda scatter'ı temizle
            if self.path_scatter is not None:
                self.path_scatter.setData(pos=np.zeros((0, 2), dtype=np.float64))
            return
        
        # Path düğümlerini işaretle (source/dest hariç)
        path_nodes = self.path[1:-1]
        if len(path_nodes) > 0 and self.path_scatter is not None:
            path_pos = np.array([[float(self.positions[n][0]), float(self.positions[n][1])] 
                                  for n in path_nodes], dtype=np.float64)
            self.path_scatter.setData(pos=path_pos)
        elif self.path_scatter is not None:
            self.path_scatter.setData(pos=np.zeros((0, 2), dtype=np.float64))
        
        # Path kenarlarını çiz
        n_path_edges = len(self.path) - 1
        if n_path_edges > 0:
            edge_x = np.zeros(n_path_edges * 3, dtype=np.float64)
            edge_y = np.zeros(n_path_edges * 3, dtype=np.float64)
            
            for i in range(n_path_edges):
                x1, y1 = self.positions[self.path[i]]
                x2, y2 = self.positions[self.path[i + 1]]
                idx = i * 3
                edge_x[idx] = float(x1)
                edge_x[idx + 1] = float(x2)
                edge_x[idx + 2] = np.nan
                edge_y[idx] = float(y1)
                edge_y[idx + 1] = float(y2)
                edge_y[idx + 2] = np.nan
            
            self.path_lines = self.plot_widget.plot(
                edge_x, edge_y,
                pen=pg.mkPen(color=(245, 158, 11, 255), width=4),
                connect='finite'
            )
    
    def _update_special_nodes(self):
        """Kaynak ve hedef düğümlerini güncelle."""
        empty_pos = np.zeros((0, 2), dtype=np.float64)
        
        if self.source is not None and self.source in self.positions:
            x, y = self.positions[self.source]
            pos = np.array([[float(x), float(y)]], dtype=np.float64)
            if self.source_scatter is not None:
                self.source_scatter.setData(pos=pos)
        else:
            if self.source_scatter is not None:
                self.source_scatter.setData(pos=empty_pos)
        
        if self.destination is not None and self.destination in self.positions:
            x, y = self.positions[self.destination]
            pos = np.array([[float(x), float(y)]], dtype=np.float64)
            if self.dest_scatter is not None:
                self.dest_scatter.setData(pos=pos)
        else:
            if self.dest_scatter is not None:
                self.dest_scatter.setData(pos=empty_pos)
    
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
        if self.graph is not None and self.graph.number_of_nodes() > 0:
            self.plot_widget.plotItem.vb.autoRange()
    
    def clear(self):
        """Grafı temizle."""
        self.graph = None
        self.positions = {}
        self.path = []
        self.source = None
        self.destination = None
        self.plot_widget.clear()
        self.node_scatter = None
        self.path_scatter = None
        self.source_scatter = None
        self.dest_scatter = None
        self.edge_lines = None
        self.path_lines = None
        self.info_label.setText("Graf yüklenmedi")
