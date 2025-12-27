""" Graf Görselleştirme Widget - PyQtGraph ile yüksek performanslı render """
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QToolTip, QFrame
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QColor, QCursor, QFont, QIcon
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx
import os

try:
    import pyqtgraph.opengl as gl
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False


class PathParticle:
    """Yol üzerinde hareket eden parçacık."""
    def __init__(self, path_nodes: List[int], positions: Dict[int, tuple], speed=0.03, offset=0.0):
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
            return self.positions[self.path_nodes[0]]
        
        u = self.path_nodes[idx]
        v = self.path_nodes[next_idx]
        pos_u = np.array(self.positions[u])
        pos_v = np.array(self.positions[v])
        t = self.position - idx
        current_pos = pos_u + (pos_v - pos_u) * t
        return tuple(current_pos)


class SafeScatterPlotItem(pg.ScatterPlotItem):
    """Subclass to fix bug where PlotItem tries to call setFftMode on all items."""
    def setFftMode(self, mode):
        pass


class GraphWidget(QWidget):
    """Performanslı graf görselleştirme widget'ı."""
    node_clicked = pyqtSignal(int)
    edge_broken = pyqtSignal(int, int)  # u, v - broken edge
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_3d_mode = False
        self.graph: Optional[nx.Graph] = None
        self.positions: Dict[int, tuple] = {}  # 2D positions
        self.positions_3d: Dict[int, tuple] = {}  # 3D positions
        self.path: List[int] = []
        self.path_color: str = '#f59e0b'
        self.source: Optional[int] = None
        self.destination: Optional[int] = None
        
        # Visual items (2D)
        self.node_scatter = None
        self.source_glow = None
        self.dest_glow = None
        self.intermediate_glow = None
        self.path_scatter = None
        self.source_scatter = None
        self.dest_scatter = None
        self.intermediate_scatter = None
        self.path_lines = None
        self.path_glow = None
        self.edge_lines = None
        
        # Visual items (3D)
        self.view_3d = None
        self.node_scatter_3d = None
        self.edge_lines_3d = []  # List of edge items
        self.path_lines_3d = None
        self.path_glow_3d = None
        self.particle_scatter_3d = None
        self.source_scatter_3d = None
        self.dest_scatter_3d = None
        self.intermediate_scatter_3d = None
        self.broken_edge_lines_3d = []
        
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
        
        # Broken edges tracking
        self.broken_edges: Set[Tuple[int, int]] = set()
        self.broken_edge_lines = []
        
        self._setup_ui()
        self.clear()
    
    def _setup_ui(self):
        self.setObjectName("GraphWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Stacked Layout
        from PyQt5.QtWidgets import QStackedLayout
        self.stack = QStackedLayout()
        layout.addLayout(self.stack)
        
        # 1. 2D Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        self.plot_widget.setAttribute(Qt.WA_TranslucentBackground, True)
        self.plot_widget.setStyleSheet("background: transparent;")
        self.plot_widget.setFrameShape(QFrame.NoFrame)
        self.stack.addWidget(self.plot_widget)
        
        # 2. 3D GL View Widget
        if OPENGL_AVAILABLE:
            self.view_3d = gl.GLViewWidget()
            # Darker blue-gray background for better contrast
            self.view_3d.setBackgroundColor(QColor(15, 20, 30, 255))
            self.view_3d.setCameraPosition(distance=40, elevation=30, azimuth=45)
            
            # Grid with subtle color - draw behind everything
            g = gl.GLGridItem()
            g.scale(3, 3, 1)
            g.setDepthValue(100)  # High value = draw behind
            self.view_3d.addItem(g)
            
            self.container_3d = QWidget()
            l3d = QVBoxLayout(self.container_3d)
            l3d.setContentsMargins(0, 0, 0, 0)
            l3d.addWidget(self.view_3d)
            
            # Close 3D Button
            self.btn_close_3d = QPushButton("2D", self.container_3d)
            self.btn_close_3d.setCursor(Qt.PointingHandCursor)
            self.btn_close_3d.setStyleSheet("""
                QPushButton {
                    background-color: rgba(15, 23, 42, 0.8);
                    color: white;
                    font-weight: bold;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: rgba(30, 41, 59, 0.9);
                }
            """)
            self.btn_close_3d.clicked.connect(lambda: self._toggle_3d_mode(False))
            self.btn_close_3d.move(20, 20)
            
            self.stack.addWidget(self.container_3d)
        
        # Background image
        bg_path = os.path.join(os.path.dirname(__file__), "..", "resources", "images", "graph_bg.png")
        bg_path = os.path.abspath(bg_path).replace("\\", "/")
        
        self.setStyleSheet(f"""
            QWidget#GraphWidget {{
                border-image: url("{bg_path}") 0 0 0 0 stretch stretch;
                border: 1px solid #1f2937;
                border-radius: 16px;
            }}
        """)
        
        from PyQt5.QtWidgets import QSizePolicy
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.08)
        self.plot_widget.hideAxis('left')
        self.plot_widget.hideAxis('bottom')
        self.plot_widget.disableAutoRange()
        
        # Mouse interaction
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_clicked)
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)
        
        # Controls Container
        self.controls_container = QWidget(self)
        self.controls_container.setStyleSheet("background: transparent;")
        controls_layout = QVBoxLayout(self.controls_container)
        controls_layout.setSpacing(8)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Buttons
        self.btn_plus = self._create_btn("icon_plus.svg", self._zoom_in, "Yakınlaştır")
        self.btn_minus = self._create_btn("icon_minus.svg", self._zoom_out, "Uzaklaştır")
        self.btn_expand = self._create_btn("icon_expand.svg", self._fit_view, "Sığdır")
        self.btn_contract = self._create_btn("icon_contract.svg", self._reset_view, "Merkeze Odakla")
        self.btn_tag = self._create_btn("icon_tag.svg", self.toggle_labels, "Etiketleri Göster/Gizle")
        
        if OPENGL_AVAILABLE:
            self.btn_3d = QPushButton("3D")
            self.btn_3d.setFixedSize(32, 32)
            self.btn_3d.setCursor(Qt.PointingHandCursor)
            self.btn_3d.setToolTip("2D/3D Görünüm Değiştir")
            self.btn_3d.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #334155;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #334155;
                }
                QPushButton:checked {
                    background-color: #3b82f6;
                    border-color: #60a5fa;
                }
            """)
            self.btn_3d.setCheckable(True)
            self.btn_3d.clicked.connect(lambda: self._toggle_3d_mode(self.btn_3d.isChecked()))
            controls_layout.addWidget(self.btn_3d)
        
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
        
        icon_label = QLabel("⚡")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("""
            font-size: 64px;
            color: #475569;
            background-color: transparent;
            padding: 0px;
        """)
        layout.addWidget(icon_label, 0, Qt.AlignCenter)
        
        text_label = QLabel("Graf oluşturmak için \"Graf Oluştur\" butonuna tıklayın")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("color: #64748b; font-size: 16px; font-weight: 500;")
        layout.addWidget(text_label)
        
        self.placeholder.hide()
    
    def _reset_view(self):
        """Reset zoom to default scale."""
        self._fit_view()
    
    def _create_btn(self, icon_name, callback, tooltip):
        btn = QPushButton()
        btn.setFixedSize(32, 32)
        btn.clicked.connect(callback)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.PointingHandCursor)
        
        icon_path = os.path.join(os.path.dirname(__file__), "..", "resources", "icons", icon_name)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(18, 18))
        else:
            btn.setText("?")
        
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
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
        if hasattr(self, 'controls_container'):
            self.controls_container.move(
                self.width() - self.controls_container.width() - 20,
                20
            )
        if hasattr(self, 'placeholder'):
            self.placeholder.resize(self.size())
        
        # 3D close button position update
        if hasattr(self, 'btn_close_3d') and self.is_3d_mode:
            self.btn_close_3d.move(20, 20)
    
    def set_graph(self, graph: nx.Graph, positions: Dict[int, tuple] = None):
        if hasattr(self, 'placeholder'):
            self.placeholder.hide()
        self.plot_widget.show()
        self.controls_container.show()
        
        self.graph = graph
        self.broken_edges.clear()
        
        for line in self.broken_edge_lines:
            try:
                self.plot_widget.removeItem(line)
            except:
                pass
        self.broken_edge_lines.clear()
        
        # Generate both 2D and 3D positions
        if positions:
            self.positions = positions
        else:
            self.positions = nx.spring_layout(
                graph, seed=42, k=2/np.sqrt(graph.number_of_nodes())
            )
        
        # Generate 3D positions
        self._generate_3d_positions()
        
        self._draw_graph()
        self._fit_view()
    
    def _generate_3d_positions(self):
        """Generate 3D positions for the graph."""
        if self.graph is None:
            return
        
        pos_3d = nx.spring_layout(
            self.graph, seed=42, dim=3, 
            k=2.5/np.sqrt(self.graph.number_of_nodes())
        )
        
        # Normalize Z to be above zero
        z_values = [coords[2] for coords in pos_3d.values()]
        min_z = min(z_values) if z_values else -1.0
        
        for node in pos_3d:
            x, y, z = pos_3d[node]
            new_z = (z - min_z) + 0.5
            pos_3d[node] = (x, y, new_z)
        
        self.positions_3d = pos_3d
    
    def _toggle_3d_mode(self, checked):
        """Toggle between 2D and 3D visualization."""
        if not OPENGL_AVAILABLE or self.graph is None:
            return
        
        self.is_3d_mode = checked
        
        # Sync button state without triggering signals
        if hasattr(self, 'btn_3d'):
            self.btn_3d.blockSignals(True)
            self.btn_3d.setChecked(checked)
            self.btn_3d.blockSignals(False)
        
        if self.is_3d_mode:
            self.stack.setCurrentIndex(1)
            
            # Ensure 3D positions exist
            if not self.positions_3d:
                self._generate_3d_positions()
            
            self._draw_graph_3d()
            self._update_path_display_3d()
            
            # Reinitialize particles for 3D
            if self.path and len(self.path) >= 2:
                self._init_particles()
        else:
            self.stack.setCurrentIndex(0)
            
            # Reinitialize particles for 2D
            if self.path and len(self.path) >= 2:
                self._init_particles()
    
    def _clear_3d_view(self):
        """Clear all items from 3D view except grid."""
        if not self.view_3d:
            return
        
        items_to_remove = []
        for item in self.view_3d.items:
            if not isinstance(item, gl.GLGridItem):
                items_to_remove.append(item)
        
        for item in items_to_remove:
            self.view_3d.removeItem(item)
        
        # Clear references
        self.node_scatter_3d = None
        self.edge_lines_3d = []  # Now a list
        self.path_lines_3d = None
        self.path_glow_3d = None
        self.particle_scatter_3d = None
        self.source_scatter_3d = None
        self.dest_scatter_3d = None
        self.intermediate_scatter_3d = None
        self.broken_edge_lines_3d = []
    
    def _draw_graph_3d(self):
        """Render graph in 3D view."""
        if not self.view_3d or self.graph is None:
            return
        
        self._clear_3d_view()
        
        # Ensure 3D positions exist
        if not self.positions_3d:
            self._generate_3d_positions()
        
        # Prepare node data - Real World Simulation
        # Size and Color based on Degree Centrality (Network Tier)
        degrees = dict(self.graph.degree())
        max_degree = max(degrees.values()) if degrees else 1
        min_degree = min(degrees.values()) if degrees else 1
        
        pos_list = []
        color_list = []
        size_list = []
        
        for node in self.graph.nodes():
            if node not in self.positions_3d:
                continue
                
            # Position
            pos_list.append(self.positions_3d[node])
            
            # Degree-based calculations
            deg = degrees.get(node, 0)
            norm_deg = (deg - min_degree) / (max_degree - min_degree) if max_degree > min_degree else 0.5
            
            # Size: Base 8 + up to 25 based on importance
            size = 8 + (norm_deg * 25)
            size_list.append(size)
            
            # Color: Gradient from Green (Edge) to Blue/Cyan (Core)
            # Edge (Low deg): [34, 197, 94] (Green)
            # Core (High deg): [59, 130, 246] (Blue)
            r = 34 + (59 - 34) * norm_deg
            g = 197 + (130 - 197) * norm_deg
            b = 94 + (246 - 94) * norm_deg
            
            # Add some transparency to inner nodes to see structure
            alpha = 0.8 + (0.2 * norm_deg) # Core nodes more opaque
            
            color_list.append([r/255.0, g/255.0, b/255.0, alpha])

        pos_array = np.array(pos_list)
        pos_array *= 10
        
        self.node_scatter_3d = gl.GLScatterPlotItem(
            pos=pos_array,
            color=np.array(color_list),
            size=np.array(size_list),
            pxMode=True
        )
        self.node_scatter_3d.setGLOptions('translucent')  # Allow alpha
        self.node_scatter_3d.setDepthValue(40)
        self.view_3d.addItem(self.node_scatter_3d)
        
        # Edges (non-broken) - BATCHED for performance
        scale = np.array([10, 10, 10])
        edge_pts = []
        
        for u, v in self.graph.edges():
            if (u, v) in self.broken_edges or (v, u) in self.broken_edges:
                continue
            
            p1 = np.array(self.positions_3d[u]) * scale
            p2 = np.array(self.positions_3d[v]) * scale
            edge_pts.append(p1)
            edge_pts.append(p2)
        
        if edge_pts:
            edge_pts = np.array(edge_pts)
            # Fiber Optic Look: Thinner, more transparent, white/cyan tint
            edge_lines = gl.GLLinePlotItem(
                pos=edge_pts,
                color=(0.7, 0.8, 0.9, 0.15),  # Very transparent blueish-white (Fiber)
                width=1.5,
                mode='lines',
                antialias=True
            )
            edge_lines.setGLOptions('additive') # Glowing effect
            self.view_3d.addItem(edge_lines)
            self.edge_lines_3d = [edge_lines]
        
        # Draw broken edges in 3D
        for u, v in self.broken_edges:
            self._draw_broken_edge_3d(u, v)
        
        # Draw Source/Dest in 3D
        if self.source is not None and self.source in self.positions_3d:
            p = np.array(self.positions_3d[self.source]) * 10
            self.source_scatter_3d = gl.GLScatterPlotItem(
                pos=np.array([p]),
                color=(0.2, 1.0, 0.4, 1.0),  # Bright green
                size=35,  # Larger
                pxMode=True
            )
            self.source_scatter_3d.setGLOptions('opaque')
            self.source_scatter_3d.setDepthValue(5)  # Very front
            self.view_3d.addItem(self.source_scatter_3d)
        
        if self.destination is not None and self.destination in self.positions_3d:
            p = np.array(self.positions_3d[self.destination]) * 10
            self.dest_scatter_3d = gl.GLScatterPlotItem(
                pos=np.array([p]),
                color=(1.0, 0.3, 0.3, 1.0),  # Bright red
                size=35,  # Larger
                pxMode=True
            )
            self.dest_scatter_3d.setGLOptions('opaque')
            self.dest_scatter_3d.setDepthValue(5)  # Very front
            self.view_3d.addItem(self.dest_scatter_3d)
    
    def _draw_broken_edge_3d(self, u: int, v: int):
        """Draw a broken edge in 3D as red dashed line."""
        if u not in self.positions_3d or v not in self.positions_3d:
            return
        
        scale = np.array([10, 10, 10])
        p1 = np.array(self.positions_3d[u]) * scale
        p2 = np.array(self.positions_3d[v]) * scale
        
        # Create dashed line effect with multiple segments
        pts = []
        num_segments = 10
        for i in range(num_segments):
            if i % 2 == 0:  # Only draw every other segment
                t1 = i / num_segments
                t2 = (i + 0.5) / num_segments
                pts.append(p1 + (p2 - p1) * t1)
                pts.append(p1 + (p2 - p1) * t2)
        
        if pts:
            broken_line = gl.GLLinePlotItem(
                pos=np.array(pts),
                color=(1.0, 0.2, 0.2, 1.0),  # Bright red, full opacity
                width=3.0,  # Thicker
                mode='lines',
                antialias=True
            )
            broken_line.setGLOptions('opaque')
            broken_line.setDepthValue(45)  # Between edges and nodes
            self.view_3d.addItem(broken_line)
            self.broken_edge_lines_3d.append(broken_line)
    
    def _update_path_display_3d(self):
        """Render path in 3D."""
        if not self.view_3d or not self.path or len(self.path) < 2:
            return
        
        # Remove old path items
        if self.path_lines_3d:
            try:
                self.view_3d.removeItem(self.path_lines_3d)
            except:
                pass
        if self.path_glow_3d:
            try:
                self.view_3d.removeItem(self.path_glow_3d)
            except:
                pass
        if self.intermediate_scatter_3d:
            try:
                self.view_3d.removeItem(self.intermediate_scatter_3d)
            except:
                pass
        
        # Ensure 3D positions exist
        if not self.positions_3d:
            return
        
        # Path Lines
        pts = []
        scale = np.array([10, 10, 10])
        for i in range(len(self.path) - 1):
            u = self.path[i]
            v = self.path[i+1]
            if u in self.positions_3d and v in self.positions_3d:
                pts.append(np.array(self.positions_3d[u]) * scale)
                pts.append(np.array(self.positions_3d[v]) * scale)
        
        if pts:
            c = QColor(self.path_color)
            color = (c.redF(), c.greenF(), c.blueF(), 1.0)
            self.path_lines_3d = gl.GLLinePlotItem(
                pos=np.array(pts),
                color=color,
                width=5.0,  # Thicker path
                mode='lines',
                antialias=True
            )
            self.path_lines_3d.setGLOptions('opaque')
            self.path_lines_3d.setDepthValue(10)  # In front of everything
            self.view_3d.addItem(self.path_lines_3d)
            
            # Glow effect - wider, semi-transparent
            glow_color = (c.redF(), c.greenF(), c.blueF(), 0.5)
            self.path_glow_3d = gl.GLLinePlotItem(
                pos=np.array(pts),
                color=glow_color,
                width=10.0,
                mode='lines',
                antialias=True
            )
            self.path_glow_3d.setGLOptions('additive')
            self.path_glow_3d.setDepthValue(15)  # Behind main path
            self.view_3d.addItem(self.path_glow_3d)
        
        # Intermediate nodes
        if len(self.path) > 2:
            int_pts = [np.array(self.positions_3d[n])*scale for n in self.path[1:-1] 
                      if n in self.positions_3d]
            if int_pts:
                c = QColor(self.path_color)
                color = (c.redF(), c.greenF(), c.blueF(), 1.0)
                self.intermediate_scatter_3d = gl.GLScatterPlotItem(
                    pos=np.array(int_pts),
                    color=color,
                    size=25,  # Larger
                    pxMode=True
                )
                self.intermediate_scatter_3d.setGLOptions('opaque')
                self.intermediate_scatter_3d.setDepthValue(8)  # In front
                self.view_3d.addItem(self.intermediate_scatter_3d)
    
    def set_path(self, path: List[int], color: str = '#f59e0b'):
        self.path = path
        self.path_color = color
        self._update_path_display()
        if self.is_3d_mode and OPENGL_AVAILABLE:
            self._update_path_display_3d()
        self._init_particles()
    
    def set_source_destination(self, source: Optional[int], destination: Optional[int]):
        self.source = source
        self.destination = destination
        self._update_special_nodes()
        
        # Update in 3D if in 3D mode
        if self.is_3d_mode and OPENGL_AVAILABLE:
            self._draw_graph_3d()
    
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
        
        # Edges (non-broken)
        edge_x = []
        edge_y = []
        for u, v in self.graph.edges():
            if (u, v) in self.broken_edges or (v, u) in self.broken_edges:
                continue
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            edge_x.extend([x1, x2, np.nan])
            edge_y.extend([y1, y2, np.nan])
        
        edge_x = np.array(edge_x, dtype=float)
        edge_y = np.array(edge_y, dtype=float)
        
        if len(edge_x) > 0:
            # Subtle fiber-like edges
            self.edge_lines = self.plot_widget.plot(
                edge_x, edge_y,
                pen=pg.mkPen(color=(100, 116, 139, 40), width=1.0),
                connect='finite'
            )
        else:
            self.edge_lines = None
        
        # Draw broken edges
        for u, v in self.broken_edges:
            self._draw_broken_edge(u, v)
        
        # Glow Items
        self.source_glow = SafeScatterPlotItem(
            size=50, brush=pg.mkBrush(34, 197, 94, 80),
            pen=pg.mkPen(None), pxMode=True
        )
        self.plot_widget.addItem(self.source_glow)
        
        self.dest_glow = SafeScatterPlotItem(
            size=50, brush=pg.mkBrush(239, 68, 68, 80),
            pen=pg.mkPen(None), pxMode=True
        )
        self.plot_widget.addItem(self.dest_glow)
        
        self.intermediate_glow = SafeScatterPlotItem(
            size=50, brush=pg.mkBrush(245, 158, 11, 80),
            pen=pg.mkPen(None), pxMode=True
        )
        self.plot_widget.addItem(self.intermediate_glow)
        
        # Nodes - Real World Simulation Styling (2D)
        degrees = dict(self.graph.degree())
        max_degree = max(degrees.values()) if degrees else 1
        min_degree = min(degrees.values()) if degrees else 1
        
        brushes = []
        sizes = []
        
        for node in self.positions.keys():
            # Degree centrality logic
            deg = degrees.get(node, 0)
            norm_deg = (deg - min_degree) / (max_degree - min_degree) if max_degree > min_degree else 0.5
            
            # Size: Base 10 + up to 15 based on importance
            size = 10 + (norm_deg * 15)
            sizes.append(size)
            
            # Color: Gradient from Green (Edge) to Blue (Core)
            r = int(34 + (59 - 34) * norm_deg)
            g = int(197 + (130 - 197) * norm_deg)
            b = int(94 + (246 - 94) * norm_deg)
            alpha = int(200 + (55 * norm_deg))
            
            brushes.append(pg.mkBrush(r, g, b, alpha))

        self.node_scatter = SafeScatterPlotItem(
            pos=pos_array, 
            size=sizes,
            brush=brushes,
            pen=pg.mkPen((15, 23, 42, 200), width=1), # Dark contour
            hoverable=True, 
            data=node_data
        )
        self.node_scatter.sigHovered.connect(self._on_node_hover)
        self.plot_widget.addItem(self.node_scatter)
        
        # Path items
        self.path_lines = self.plot_widget.plot(
            [], [], pen=pg.mkPen(color=(245, 158, 11, 255), width=4),
            connect='finite'
        )
        
        self.path_glow = self.plot_widget.plot(
            [], [], pen=pg.mkPen(color=(245, 158, 11, 100), width=8),
            connect='finite'
        )
        
        self.intermediate_scatter = SafeScatterPlotItem(
            size=28, brush=pg.mkBrush(245, 158, 11, 255),
            pen=pg.mkPen('w', width=2), pxMode=True
        )
        self.plot_widget.addItem(self.intermediate_scatter)
        
        self.source_scatter = SafeScatterPlotItem(
            size=45, brush=pg.mkBrush(34, 197, 94, 255),
            pen=pg.mkPen('w', width=3), pxMode=True
        )
        self.plot_widget.addItem(self.source_scatter)
        
        self.dest_scatter = SafeScatterPlotItem(
            size=45, brush=pg.mkBrush(239, 68, 68, 255),
            pen=pg.mkPen('w', width=3), pxMode=True
        )
        self.plot_widget.addItem(self.dest_scatter)
        
        self.particle_scatter = SafeScatterPlotItem(
            size=8, brush=pg.mkBrush(255, 255, 255, 255),
            pen=pg.mkPen(None), pxMode=True
        )
        self.plot_widget.addItem(self.particle_scatter)
        
        if self.labels_visible:
            self._update_node_labels()
    
    def _update_path_display(self):
        if not self.path or len(self.path) < 2:
            if self.path_lines:
                self.path_lines.setData([], [])
            if self.path_glow:
                self.path_glow.setData([], [])
            if self.particle_scatter:
                self.particle_scatter.setData(pos=[])
            self.timer.stop()
            return
        
        c = QColor(self.path_color)
        pen_color = (c.red(), c.green(), c.blue(), 255)
        glow_color = (c.red(), c.green(), c.blue(), 100)
        
        self.path_lines.setPen(pg.mkPen(
            color=pen_color, width=3, style=Qt.DashLine
        ))
        self.path_glow.setPen(pg.mkPen(color=glow_color, width=8))
        
        # Path edges
        edge_x = []
        edge_y = []
        for i in range(len(self.path) - 1):
            x1, y1 = self.positions[self.path[i]]
            x2, y2 = self.positions[self.path[i + 1]]
            edge_x.extend([x1, x2, np.nan])
            edge_y.extend([y1, y2, np.nan])
        
        edge_x = np.array(edge_x, dtype=float)
        edge_y = np.array(edge_y, dtype=float)
        
        self.path_lines.setData(edge_x, edge_y)
        self.path_glow.setData(edge_x, edge_y)
        
        # Update intermediate nodes
        self.intermediate_scatter.setBrush(pg.mkBrush(self.path_color))
        
        int_pos = []
        if len(self.path) > 2:
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
        if not self.path or len(self.path) < 2:
            return
        
        num_particles = min(20, max(5, len(self.path) * 2))
        
        # Determine positions
        if self.is_3d_mode and self.positions_3d:
            scale = np.array([10, 10, 10])
            scaled_pos = {k: tuple(np.array(v)*scale) for k, v in self.positions_3d.items()}
            positions = scaled_pos
        else:
            positions = self.positions
        
        for i in range(num_particles):
            offset = i * (len(self.path) / num_particles)
            self.particles.append(PathParticle(self.path, positions, offset=offset, speed=0.03))
        
        # Initialize 3D particle scatter
        if self.is_3d_mode and self.view_3d:
            if self.particle_scatter_3d:
                try:
                    self.view_3d.removeItem(self.particle_scatter_3d)
                except:
                    pass
            
            self.particle_scatter_3d = gl.GLScatterPlotItem(
                pos=np.zeros((1, 3)),
                color=(1.0, 1.0, 0.8, 1.0),  # Bright yellow-white
                size=15,  # Larger particles
                pxMode=True
            )
            self.particle_scatter_3d.setGLOptions('opaque')
            self.particle_scatter_3d.setDepthValue(3)  # Very front
            self.view_3d.addItem(self.particle_scatter_3d)
        
        self.timer.start(20)
    
    def _update_animation(self):
        if not self.particles:
            return
        
        positions = []
        for p in self.particles:
            coords = p.update()
            if coords:
                positions.append(coords)
        
        if not positions:
            return
        
        if self.is_3d_mode and self.view_3d and self.particle_scatter_3d:
            if len(positions[0]) == 3:
                try:
                    self.particle_scatter_3d.setData(pos=np.array(positions))
                except:
                    pass
        else:
            if len(positions[0]) == 2:
                try:
                    self.particle_scatter.setData(pos=np.array(positions))
                except:
                    pass
    
    def _update_special_nodes(self):
        for item in self.text_items:
            self.plot_widget.removeItem(item)
        self.text_items = []
        
        # Update Source
        if self.source is not None and self.source in self.positions:
            pos = self.positions[self.source]
            self.source_scatter.setData(pos=[pos])
            self.source_glow.setData(pos=[pos])
            
            text_s = pg.TextItem("S", anchor=(0.5, 0.5), color='white')
            font = QFont()
            font.setBold(True)
            font.setPointSize(12)
            text_s.setFont(font)
            text_s.setPos(pos[0], pos[1])
            self.plot_widget.addItem(text_s)
            self.text_items.append(text_s)
            
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
            
            text_d = pg.TextItem("D", anchor=(0.5, 0.5), color='white')
            font = QFont()
            font.setBold(True)
            font.setPointSize(12)
            text_d.setFont(font)
            text_d.setPos(pos[0], pos[1])
            self.plot_widget.addItem(text_d)
            self.text_items.append(text_d)
            
            text_id = pg.TextItem(str(self.destination), anchor=(0.5, 1.5), color='#f1f5f9')
            text_id.setPos(pos[0], pos[1])
            self.plot_widget.addItem(text_id)
            self.text_items.append(text_id)
        else:
            self.dest_scatter.setData(pos=[])
            self.dest_glow.setData(pos=[])
    
    def _handle_edge_break(self, mouse_point):
        if self.graph is None:
            return
        
        min_dist = float('inf')
        closest_edge = None
        
        all_edges = list(self.graph.edges())
        for u, v in list(self.broken_edges):
            if u in self.positions and v in self.positions:
                all_edges.append((u, v))
        
        for u, v in all_edges:
            if u not in self.positions or v not in self.positions:
                continue
            
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            
            dist = self._point_to_line_distance(
                mouse_point.x(), mouse_point.y(), x1, y1, x2, y2
            )
            
            if dist < min_dist:
                min_dist = dist
                closest_edge = (u, v)
        
        view_range = self.plot_widget.plotItem.vb.viewRange()
        x_range = view_range[0][1] - view_range[0][0]
        threshold = x_range * 0.02
        
        if min_dist < threshold and closest_edge:
            u, v = closest_edge
            if (u, v) not in self.broken_edges and (v, u) not in self.broken_edges:
                self._break_edge(u, v)
    
    def _break_edge(self, u: int, v: int):
        if (u, v) in self.broken_edges or (v, u) in self.broken_edges:
            return
        
        self.broken_edges.add((u, v))
        
        if self.graph.has_edge(u, v):
            self.graph.remove_edge(u, v)
        
        self._draw_broken_edge(u, v)
        
        # Draw in 3D if in 3D mode
        if self.is_3d_mode and self.view_3d:
            self._draw_broken_edge_3d(u, v)
        
        self.edge_broken.emit(u, v)
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔴 Link {u}-{v} broken! Rerouting traffic...")
    
    def _draw_broken_edge(self, u: int, v: int):
        if u not in self.positions or v not in self.positions:
            return
        
        x1, y1 = self.positions[u]
        x2, y2 = self.positions[v]
        
        broken_line = self.plot_widget.plot(
            [x1, x2], [y1, y2],
            pen=pg.mkPen(
                color=(239, 68, 68, 200),
                width=2.0,
                style=Qt.DashLine
            ),
            connect='finite'
        )
        self.broken_edge_lines.append(broken_line)
    
    def _on_node_hover(self, item, points, ev):
        if len(points) > 0:
            pt = points[0]
            node_id = pt.data()['id']
    
    def _on_mouse_clicked(self, event):
        if self.graph is None:
            return
        
        if event.button() != Qt.RightButton:
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
        else:
            pos = event.scenePos()
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            self._handle_edge_break(mouse_point)
    
    def _on_mouse_moved(self, pos):
        if self.graph is None:
            return
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        self._check_edge_hover(mouse_point)
    
    def _check_edge_hover(self, mouse_point):
        if self.graph is None:
            return
        
        min_dist = float('inf')
        closest_edge = None
        
        for u, v in self.graph.edges():
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            
            dist = self._point_to_line_distance(
                mouse_point.x(), mouse_point.y(), x1, y1, x2, y2
            )
            
            if dist < min_dist:
                min_dist = dist
                closest_edge = (u, v)
        
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
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        px_dx = px - x1
        py_dy = py - y1
        
        t = max(0, min(1, (px_dx * dx + py_dy * dy) / (dx * dx + dy * dy)))
        
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
    
    def _show_edge_tooltip(self, edge, mouse_point):
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
        
        if self.edge_tooltip is not None:
            self.plot_widget.removeItem(self.edge_tooltip)
        
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
        
        self.edge_tooltip.setPos(mouse_point.x() + 0.05, mouse_point.y() - 0.05)
        self.plot_widget.addItem(self.edge_tooltip)
        
        self._highlight_edge(edge, True)
    
    def _hide_edge_tooltip(self):
        if self.edge_tooltip is not None:
            self.plot_widget.removeItem(self.edge_tooltip)
            self.edge_tooltip = None
        
        self._highlight_edge(self.current_hovered_edge, False)
    
    def _highlight_edge(self, edge, highlight):
        if edge is None:
            return
        
        u, v = edge
        x1, y1 = self.positions[u]
        x2, y2 = self.positions[v]
        
        if highlight:
            if self.edge_highlight_line is not None:
                self.plot_widget.removeItem(self.edge_highlight_line)
            
            self.edge_highlight_line = self.plot_widget.plot(
                [x1, x2], [y1, y2],
                pen=pg.mkPen(color=(59, 130, 246, 200), width=3),
                connect='finite'
            )
        else:
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
        for item in self.node_labels:
            self.plot_widget.removeItem(item)
        self.node_labels = []
        
        if not self.labels_visible or self.graph is None:
            return
        
        for node, (x, y) in self.positions.items():
            if node == self.source or node == self.destination:
                continue
            
            text = pg.TextItem(str(node), anchor=(0.5, 0.5), color='#e2e8f0')
            text.setPos(x, y)
            self.plot_widget.addItem(text)
            self.node_labels.append(text)
    
    def clear(self):
        self.graph = None
        self.positions = {}
        self.positions_3d = {}
        self.path = []
        self.source = None
        self.destination = None
        self.current_hovered_edge = None
        
        self.broken_edges.clear()
        self.broken_edge_lines.clear()
        self.broken_edge_lines_3d = []
        
        self.plot_widget.clear()
        if self.view_3d:
            self._clear_3d_view()
        
        self.timer.stop()
        
        if hasattr(self, 'placeholder'):
            self.placeholder.show()
            self.plot_widget.hide()
            self.controls_container.hide()
    
    def reset_broken_edges(self):
        for u, v in list(self.broken_edges):
            if not self.graph.has_edge(u, v):
                self.graph.add_edge(u, v)
        
        self.broken_edges.clear()
        
        for line in self.broken_edge_lines:
            try:
                self.plot_widget.removeItem(line)
            except:
                pass
        self.broken_edge_lines.clear()
        
        # Clear 3D broken edges
        for line in self.broken_edge_lines_3d:
            try:
                self.view_3d.removeItem(line)
            except:
                pass
        self.broken_edge_lines_3d = []
        
        if self.graph is not None:
            if self.is_3d_mode and OPENGL_AVAILABLE:
                self._draw_graph_3d()
            else:
                self._draw_graph()