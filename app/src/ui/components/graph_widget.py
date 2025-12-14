"""
Graf Görselleştirme Widget - PyQtGraph ile yüksek performanslı render
"""
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QToolTip, QFrame
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QColor, QCursor, QFont, QIcon
from typing import Dict, List, Optional, Set
import networkx as nx
import os

class PathParticle:
    """Yol üzerinde hareket eden parçacık."""
    def __init__(self, path_nodes: List[int], positions: Dict[int, tuple], speed=0.01, offset=0.0):
        self.path_nodes = path_nodes
        self.positions = positions
        self.position = offset
        self.speed = speed
    
    def update(self):
        self.position += self.speed
        if self.position >= len(self.path_nodes) - 1:
            self.position = 0.0
        return self.get_coordinates()
        
    def get_coordinates(self):
        idx = int(self.position)
        next_idx = idx + 1
        if next_idx >= len(self.path_nodes):
            next_idx = 0 # Should not happen with reset logic but safety first
            
        u = self.path_nodes[idx]
        v = self.path_nodes[next_idx]
        
        pos_u = np.array(self.positions[u])
        pos_v = np.array(self.positions[v])
        
        t = self.position - idx
        current_pos = pos_u + (pos_v - pos_u) * t
        return current_pos[0], current_pos[1]

class GraphWidget(QWidget):
    """
    Performanslı graf görselleştirme widget'ı.
    """
    
    node_clicked = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph: Optional[nx.Graph] = None
        self.positions: Dict[int, tuple] = {}
        self.path: List[int] = []
        self.source: Optional[int] = None
        self.destination: Optional[int] = None
        
        # Visual items
        self.node_scatter = None
        self.source_glow = None
        self.dest_glow = None
        self.intermediate_glow = None
        self.path_scatter = None
        self.source_scatter = None
        self.dest_scatter = None
        self.intermediate_scatter = None
        self.path_lines = None
        self.edge_lines = None
        
        # Labels
        self.text_items = []
        self.node_labels = []
        self.labels_visible = False
        
        # Animation
        self.particles: List[PathParticle] = []
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_animation)
        
        # Edge hover
        self.current_hovered_edge = None
        self.edge_tooltip = None
        self.edge_highlight_line = None
        
        self._setup_ui()
        self.clear() # Set initial state
    
    def _setup_ui(self):
        self.setObjectName("GraphWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget#GraphWidget {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 16px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1) # Small margin to show border/radius
        # Note: If we want "padding" inside the card as per image, we can increase this
        # But image shows graph taking mostly full space, maybe just rounded headers? 
        # Actually image shows the nodes floating on the dark background. 
        # A small margin ensures the plot content (which is rect) doesn't clip the rounded corners ugly.
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#111827') # Match parent bg
        self.plot_widget.setFrameShape(QFrame.NoFrame) # Remove internal border
        
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.showGrid(x=False, y=False)
        self.plot_widget.hideAxis('left')
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.disableAutoRange()
        
        # Mouse interaction
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)
        
        layout.addWidget(self.plot_widget)
        
        # Controls Container (Floating) - Top Right Vertical
        self.controls_container = QWidget(self)
        self.controls_container.setStyleSheet("background: transparent;")
        controls_layout = QVBoxLayout(self.controls_container) # Changed to Vertical
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Buttons
        # Buttons
        self.btn_plus = self._create_btn("icon_plus.svg", self._zoom_in, "Yakınlaştır")
        self.btn_minus = self._create_btn("icon_minus.svg", self._zoom_out, "Uzaklaştır")
        self.btn_expand = self._create_btn("icon_expand.svg", self._fit_view, "Sığdır")
        self.btn_contract = self._create_btn("icon_contract.svg", self._reset_view, "Merkeze Odakla")
        self.btn_tag = self._create_btn("icon_tag.svg", self.toggle_labels, "Etiketleri Göster/Gizle") # Tag
        
        controls_layout.addWidget(self.btn_plus)
        controls_layout.addWidget(self.btn_minus)
        controls_layout.addWidget(self.btn_expand)
        controls_layout.addWidget(self.btn_contract)
        controls_layout.addWidget(self.btn_tag)
        controls_layout.addStretch()
        
        self.controls_container.adjustSize()
        
        self._setup_placeholder()

    def _setup_placeholder(self):
        """Grafik boşken gösterilecek placeholder."""
        self.placeholder = QWidget(self)
        self.placeholder.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(self.placeholder)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Icon
        icon_label = QLabel("⚡")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 64px;
            color: #475569; /* slate-600 */
            background-color: transparent;
            padding: 0px;
        """)
        layout.addWidget(icon_label, 0, Qt.AlignCenter)
        
        # Text
        text_label = QLabel("Graf oluşturmak için \"Graf Oluştur\" butonuna tıklayın")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("color: #64748b; font-size: 16px; font-weight: 500;")
        layout.addWidget(text_label)
        
        self.placeholder.hide()

    def _reset_view(self):
        """Reset zoom to default 1:1 scale (roughly) or center."""
        # Just fit view for now, or could set specific range
        self._fit_view()

    def _create_btn(self, icon_name, callback, tooltip):
        btn = QPushButton()
        btn.setFixedSize(32, 32)
        btn.clicked.connect(callback)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        
        # Load Icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", icon_name)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(18, 18))
        else:
            btn.setText("?")
            
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b; /* slate-800 */
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #334155;
                border-color: #475569;
            }
            QPushButton:pressed {
                background-color: #0f172a;
            }
        """)
        return btn

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position controls on the top right side
        if hasattr(self, 'controls_container'):
            self.controls_container.move(
                self.width() - self.controls_container.width() - 20,
                20
            )
        
        if hasattr(self, 'placeholder'):
            self.placeholder.resize(self.size())

    def set_graph(self, graph: nx.Graph, positions: Dict[int, tuple] = None):
        if hasattr(self, 'placeholder'):
            self.placeholder.hide()
            self.plot_widget.show()
            self.controls_container.show()
            
        self.graph = graph
        
        if positions:
            self.positions = positions
        else:
            self.positions = nx.spring_layout(
                graph, seed=42, k=2/np.sqrt(graph.number_of_nodes())
            )
        
        self._draw_graph()
        self._fit_view()

    def set_path(self, path: List[int]):
        self.path = path
        self._update_path_display()
        self._init_particles()

    def set_source_destination(self, source: Optional[int], destination: Optional[int]):
        self.source = source
        self.destination = destination
        self._update_special_nodes()

    def _draw_graph(self):
        if self.graph is None:
            return
        
        self.plot_widget.clear()
        self.text_items = []
        
        # Prepare data
        n_nodes = self.graph.number_of_nodes()
        pos_array = np.zeros((n_nodes, 2))
        node_data = []
        for node, (x, y) in self.positions.items():
            pos_array[node] = [x, y]
            node_data.append({'id': node})
        
        # Edges (Background)
        edge_x = []
        edge_y = []
        for u, v in self.graph.edges():
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            edge_x.extend([x1, x2, np.nan])
            edge_y.extend([y1, y2, np.nan])
        
        # Convert to numpy arrays to ensure float dtype
        edge_x = np.array(edge_x, dtype=float)
        edge_y = np.array(edge_y, dtype=float)
        
        self.edge_lines = self.plot_widget.plot(
            edge_x, edge_y,
            pen=pg.mkPen(color=(71, 85, 105, 50), width=0.8), # slate-600 low alpha
            connect='finite'
        )
        
        # Glow Items (Behind everything else)
        # Source Glow
        self.source_glow = pg.ScatterPlotItem(
            size=50,
            brush=pg.mkBrush(34, 197, 94, 80), # green-500 low alpha
            pen=pg.mkPen(None),
            pxMode=True
        )
        self.plot_widget.addItem(self.source_glow)
        
        # Dest Glow
        self.dest_glow = pg.ScatterPlotItem(
            size=50,
            brush=pg.mkBrush(239, 68, 68, 80), # red-500 low alpha
            pen=pg.mkPen(None),
            pxMode=True
        )
        self.plot_widget.addItem(self.dest_glow)
        
        # Intermediate Glow
        self.intermediate_glow = pg.ScatterPlotItem(
            size=50, 
            brush=pg.mkBrush(245, 158, 11, 80), # amber-500 low alpha
            pen=pg.mkPen(None),
            pxMode=True
        )
        self.plot_widget.addItem(self.intermediate_glow)

        # Nodes
        self.node_scatter = pg.ScatterPlotItem(
            pos=pos_array,
            size=10,
            brush=pg.mkBrush(100, 116, 139, 200), # slate-500
            pen=pg.mkPen(None),
            hoverable=True,
            data=node_data
        )
        self.node_scatter.sigHovered.connect(self._on_node_hover)
        self.plot_widget.addItem(self.node_scatter)
        
        # Path Lines (Orange Glow)
        self.path_lines = self.plot_widget.plot(
            [], [],
            pen=pg.mkPen(color=(245, 158, 11, 255), width=4), # amber-500
            connect='finite'
        )
        # Path Glow Effect (Simulated by wider transparent line)
        self.path_glow = self.plot_widget.plot(
            [], [],
            pen=pg.mkPen(color=(245, 158, 11, 100), width=8), 
            connect='finite'
        )
        
        # Intermediate Nodes Scatter (Yellow)
        self.intermediate_scatter = pg.ScatterPlotItem(
            size=36, # Same as Source/Dest
            brush=pg.mkBrush(245, 158, 11, 255), # amber-500
            pen=pg.mkPen('w', width=2), # Match border width of S/D (2)
            pxMode=True
        )
        self.plot_widget.addItem(self.intermediate_scatter)
        
        # Source & Dest Scatters (Large)
        self.source_scatter = pg.ScatterPlotItem(
            size=36,
            brush=pg.mkBrush(34, 197, 94, 255), # green-500
            pen=pg.mkPen('w', width=2),
            pxMode=True
        )
        self.plot_widget.addItem(self.source_scatter)
        
        self.dest_scatter = pg.ScatterPlotItem(
            size=36, 
            brush=pg.mkBrush(239, 68, 68, 255), # red-500
            pen=pg.mkPen('w', width=2),
            pxMode=True
        )
        self.plot_widget.addItem(self.dest_scatter)
        
        # Particles
        self.particle_scatter = pg.ScatterPlotItem(
            size=8,
            brush=pg.mkBrush(255, 255, 255, 255),
            pen=pg.mkPen(None),
            pxMode=True
        )
        self.plot_widget.addItem(self.particle_scatter)
        
        # Restore labels if they were visible
        if self.labels_visible:
            self._update_node_labels()

    def _update_path_display(self):
        if not self.path or len(self.path) < 2:
            self.path_lines.setData([], [])
            self.path_glow.setData([], [])
            self.particle_scatter.setData(pos=[])
            self.timer.stop()
            return
        
        # Path edges
        edge_x = []
        edge_y = []
        for i in range(len(self.path) - 1):
            x1, y1 = self.positions[self.path[i]]
            x2, y2 = self.positions[self.path[i + 1]]
            edge_x.extend([x1, x2, np.nan])
            edge_y.extend([y1, y2, np.nan])
        
        # Convert to numpy arrays
        edge_x = np.array(edge_x, dtype=float)
        edge_y = np.array(edge_y, dtype=float)
        
        self.path_lines.setData(edge_x, edge_y)
        self.path_lines.setData(edge_x, edge_y)
        self.path_glow.setData(edge_x, edge_y)

        # Update Intermediate Nodes
        int_pos = []
        if len(self.path) > 2:
            # Intermediate nodes are between first and last
            intermediate_nodes = self.path[1:-1]
            for node in intermediate_nodes:
                 if node in self.positions:
                     int_pos.append(list(self.positions[node]))
        
        if int_pos:
            self.intermediate_scatter.setData(pos=np.array(int_pos))
            self.intermediate_glow.setData(pos=np.array(int_pos))
        else:
            self.intermediate_scatter.setData(pos=[])
            self.intermediate_glow.setData(pos=[])
        
    def _init_particles(self):
        self.particles = []
        if not self.path:
            return
            
        # Create particles
        for i in range(3):
            offset = i * (len(self.path) / 3)
            self.particles.append(PathParticle(self.path, self.positions, offset=offset))
            
        self.timer.start(30)

    def _update_animation(self):
        if not self.particles:
            return
        positions = []
        for p in self.particles:
            x, y = p.update()
            positions.append([x, y])
        self.particle_scatter.setData(pos=np.array(positions))

    def _update_special_nodes(self):
        # Clear previous text items
        for item in self.text_items:
            self.plot_widget.removeItem(item)
        self.text_items = []
        
        # Update Source
        if self.source is not None and self.source in self.positions:
            pos = self.positions[self.source]
            self.source_scatter.setData(pos=[pos])
            self.source_glow.setData(pos=[pos])
            
            # Text 'S'
            text_s = pg.TextItem("S", anchor=(0.5, 0.5), color='white')
            font = QFont()
            font.setBold(True)
            font.setPointSize(12)
            text_s.setFont(font)
            text_s.setPos(pos[0], pos[1])
            self.plot_widget.addItem(text_s)
            self.text_items.append(text_s)
            
            # Label ID above
            text_id = pg.TextItem(str(self.source), anchor=(0.5, 1.5), color='#f1f5f9')
            text_id.setPos(pos[0], pos[1])
            self.plot_widget.addItem(text_id)
            self.text_items.append(text_id)
        else:
            self.source_scatter.setData(pos=[])
            self.source_glow.setData(pos=[])
        
        # Update Dest
        if self.destination is not None and self.destination in self.positions:
            pos = self.positions[self.destination]
            self.dest_scatter.setData(pos=[pos])
            self.dest_glow.setData(pos=[pos])
            
            # Text 'D'
            text_d = pg.TextItem("D", anchor=(0.5, 0.5), color='white')
            font = QFont()
            font.setBold(True)
            font.setPointSize(12)
            text_d.setFont(font)
            text_d.setPos(pos[0], pos[1])
            self.plot_widget.addItem(text_d)
            self.text_items.append(text_d)
            
            # Label ID above
            text_id = pg.TextItem(str(self.destination), anchor=(0.5, 1.5), color='#f1f5f9')
            text_id.setPos(pos[0], pos[1])
            self.plot_widget.addItem(text_id)
            self.text_items.append(text_id)
        else:
            self.dest_scatter.setData(pos=[])
            self.dest_glow.setData(pos=[])

    def _on_node_hover(self, item, points, ev):
        if len(points) > 0:
            pt = points[0]
            node_id = pt.data()['id']
            # Simple interaction, can be expanded
            
    def _on_mouse_clicked(self, event):
        if self.graph is None:
            return
        pos = event.scenePos()
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        
        min_dist = float('inf')
        closest_node = None
        
        for node, (x, y) in self.positions.items():
            dist = (mouse_point.x() - x) ** 2 + (mouse_point.y() - y) ** 2
            if dist < min_dist:
                min_dist = dist
                closest_node = node
        
        if min_dist < 0.01:
            self.node_clicked.emit(closest_node)
    
    def _on_mouse_moved(self, pos):
        """Mouse hareket event'i - edge hover için."""
        if self.graph is None:
            return
        
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        self._check_edge_hover(mouse_point)
    
    def _check_edge_hover(self, mouse_point):
        """Mouse pozisyonuna en yakın edge'i bul ve tooltip göster."""
        if self.graph is None:
            return
        
        min_dist = float('inf')
        closest_edge = None
        
        # Check distance to all edges
        for u, v in self.graph.edges():
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            
            # Calculate distance from point to line segment
            dist = self._point_to_line_distance(
                mouse_point.x(), mouse_point.y(),
                x1, y1, x2, y2
            )
            
            if dist < min_dist:
                min_dist = dist
                closest_edge = (u, v)
        
        # Show tooltip if close enough (threshold in view coordinates)
        hover_threshold = 0.02
        if min_dist < hover_threshold and closest_edge:
            if self.current_hovered_edge != closest_edge:
                self.current_hovered_edge = closest_edge
                self._show_edge_tooltip(closest_edge, mouse_point)
        else:
            if self.current_hovered_edge is not None:
                self._hide_edge_tooltip()
                self.current_hovered_edge = None
    
    def _point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """Bir noktanın bir doğru parçasına olan uzaklığını hesapla."""
        # Vector from line start to end
        dx = x2 - x1
        dy = y2 - y1
        
        # If line is a point, return distance to that point
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        # Vector from line start to point
        px_dx = px - x1
        py_dy = py - y1
        
        # Project point onto line
        t = max(0, min(1, (px_dx * dx + py_dy * dy) / (dx * dx + dy * dy)))
        
        # Closest point on line segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance from point to closest point on line
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
    
    def _show_edge_tooltip(self, edge, mouse_point):
        """Edge bilgilerini tooltip olarak göster."""
        u, v = edge
        edge_data = self.graph.edges[u, v]
        
        delay = edge_data.get('delay', 0.0)
        reliability = edge_data.get('reliability', 1.0)
        bandwidth = edge_data.get('bandwidth', 0.0)
        
        tooltip_text = (
            f"Kenar: {u} → {v}\n"
            f"Gecikme: {delay:.2f} ms\n"
            f"Güvenilirlik: {reliability:.4f}\n"
            f"Bant Genişliği: {bandwidth:.2f} Mbps"
        )
        
        # Remove old tooltip if exists
        if self.edge_tooltip is not None:
            self.plot_widget.removeItem(self.edge_tooltip)
        
        # Create new tooltip
        self.edge_tooltip = pg.TextItem(
            tooltip_text,
            anchor=(0, 1),
            color='#f1f5f9',
            border='#334155',
            fill='#1e293b'
        )
        font = QFont()
        font.setPointSize(9)
        self.edge_tooltip.setFont(font)
        # Position tooltip near mouse but offset slightly
        self.edge_tooltip.setPos(mouse_point.x() + 0.05, mouse_point.y() - 0.05)
        self.plot_widget.addItem(self.edge_tooltip)
        
        # Highlight the edge
        self._highlight_edge(edge, True)
    
    def _hide_edge_tooltip(self):
        """Edge tooltip'i gizle."""
        if self.edge_tooltip is not None:
            self.plot_widget.removeItem(self.edge_tooltip)
            self.edge_tooltip = None
        
        # Remove edge highlight
        self._highlight_edge(self.current_hovered_edge, False)
    
    def _highlight_edge(self, edge, highlight):
        """Edge'i vurgula (hover durumunda)."""
        if edge is None:
            return
        
        u, v = edge
        x1, y1 = self.positions[u]
        x2, y2 = self.positions[v]
        
        if highlight:
            # Remove old highlight if exists
            if self.edge_highlight_line is not None:
                self.plot_widget.removeItem(self.edge_highlight_line)
            
            # Create highlight line
            self.edge_highlight_line = self.plot_widget.plot(
                [x1, x2], [y1, y2],
                pen=pg.mkPen(color=(59, 130, 246, 200), width=3),  # blue-500 with alpha
                connect='finite'
            )
        else:
            # Remove highlight
            if self.edge_highlight_line is not None:
                self.plot_widget.removeItem(self.edge_highlight_line)
                self.edge_highlight_line = None

    def _zoom_in(self):
        self.plot_widget.plotItem.vb.scaleBy((0.7, 0.7))
    
    def _zoom_out(self):
        self.plot_widget.plotItem.vb.scaleBy((1.3, 1.3))
    
    def _fit_view(self):
        if self.graph is None or self.graph.number_of_nodes() == 0:
            return
        try:
            self.plot_widget.plotItem.vb.autoRange()
        except Exception:
            pass
        
    def toggle_labels(self):
        self.labels_visible = not self.labels_visible
        self._update_node_labels()
        
    def _update_node_labels(self):
        # Clear existing labels
        for item in self.node_labels:
            self.plot_widget.removeItem(item)
        self.node_labels = []
        
        if not self.labels_visible or self.graph is None:
            return
            
        for node, (x, y) in self.positions.items():
            # Skip if source or dest (they have their own labels)
            if node == self.source or node == self.destination:
                continue
                
            text = pg.TextItem(
                str(node), 
                anchor=(0.5, 0.5),
                color='#e2e8f0' # slate-200
            )
            # Center it on the node
            text.setPos(x, y)
            self.plot_widget.addItem(text)
            self.node_labels.append(text)
            
    def clear(self):
        self.graph = None
        self.positions = {}
        self.path = []
        self.source = None
        self.destination = None
        self.current_hovered_edge = None
        self.plot_widget.clear()
        self.timer.stop()
        
        if hasattr(self, 'placeholder'):
            self.placeholder.show()
            self.plot_widget.hide()
            self.controls_container.hide()
