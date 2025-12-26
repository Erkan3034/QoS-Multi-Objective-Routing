"""
Graf Görselleştirme Widget - PyQtGraph ile yüksek performanslı render
"""
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QToolTip, QFrame
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QPoint, QSize
from PyQt5.QtGui import QColor, QCursor, QFont, QIcon
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx
import os

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
    # ========================================================================
    # [CHAOS MONKEY FEATURE] Interactive Link Break
    # ========================================================================
    # Bu signal, kullanıcı bir edge'e sağ tıkladığında ve edge kırıldığında
    # emit edilir. MainWindow bu signal'i dinleyerek otomatik olarak
    # yeniden yönlendirme (re-optimization) tetikler.
    # Parametreler: (u, v) - kırılan edge'in node ID'leri
    # ========================================================================
    edge_broken = pyqtSignal(int, int)  # u, v - broken edge
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph: Optional[nx.Graph] = None
        self.positions: Dict[int, tuple] = {}
        self.path: List[int] = []
        self.path_color: str = '#f59e0b'  # Default amber-500
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
        
        # ====================================================================
        # [CHAOS MONKEY FEATURE] Broken Edges Tracking
        # ====================================================================
        # Kullanıcı sağ tıklayarak kırdığı edge'leri takip eder.
        # - broken_edges: Kırılmış edge'lerin (u, v) tuple'larını tutar
        # - broken_edge_lines: PyQtGraph'ın çizdiği görsel item'ları tutar
        #   (clear() metodunda temizlenmesi için)
        # 
        # ÖNEMLİ: Edge kırıldığında NetworkX graph'tan da kaldırılır,
        # ancak görsel olarak kırmızı kesikli çizgi olarak gösterilir.
        # Bu sayede kullanıcı hangi linklerin kırıldığını görebilir.
        # ====================================================================
        self.broken_edges: Set[Tuple[int, int]] = set()
        self.broken_edge_lines = []  # Visual representation of broken edges
        
        self._setup_ui()
        self.clear() # Set initial state
    
    def _setup_ui(self):
        self.setObjectName("GraphWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Initial stylesheet empty - set in the block below to combine with gradient
        self.setStyleSheet("")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1) # Small margin to show border/radius
        # Note: If we want "padding" inside the card as per image, we can increase this
        # But image shows graph taking mostly full space, maybe just rounded headers? 
        # Actually image shows the nodes floating on the dark background. 
        # A small margin ensures the plot content (which is rect) doesn't clip the rounded corners ugly.
        layout.setContentsMargins(6, 6, 6, 6)
        
        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None) # Make plot background transparent to show gradient below
        self.plot_widget.setAttribute(Qt.WA_TranslucentBackground, True) # Force translucency
        self.plot_widget.setStyleSheet("background: transparent;") # CSS transparency
        self.plot_widget.setFrameShape(QFrame.NoFrame) # Remove internal border
        
        # Determine path to background image
        import os
        # Correction: One level up from 'components' is 'ui', where 'resources' resides.
        bg_path = os.path.join(os.path.dirname(__file__), "..", "resources", "images", "graph_bg.png")
        bg_path = os.path.abspath(bg_path).replace("\\", "/")
        
        # Set gradient/image on the parent GraphWidget via stylesheet
        # Using border-image to stretch content
    
        self.setStyleSheet(f"""
            QWidget#GraphWidget {{
                border-image: url("{bg_path}") 0 0 0 0 stretch stretch;
                border: 1px solid #1f2937;
                border-radius: 16px;
            }}
        """)
        
        # Set size policy for proper expansion
        from PyQt5.QtWidgets import QSizePolicy
        self.plot_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.plot_widget.setAspectLocked(True)
        # Enable grid for "Tactical Map" look - subtle
        self.plot_widget.showGrid(x=True, y=True, alpha=0.08) 
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
        
        # Reset broken edges when new graph is loaded
        self.broken_edges.clear()
        for line in self.broken_edge_lines:
            try:
                self.plot_widget.removeItem(line)
            except:
                pass
        self.broken_edge_lines.clear()
        
        if positions:
            self.positions = positions
        else:
            self.positions = nx.spring_layout(
                graph, seed=42, k=2/np.sqrt(graph.number_of_nodes())
            )
        
        self._draw_graph()
        self._fit_view()

    def set_path(self, path: List[int], color: str = '#f59e0b'):
        self.path = path
        self.path_color = color
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
        
        # ====================================================================
        # [CHAOS MONKEY FEATURE] Edges (Background) - only draw non-broken edges
        # ====================================================================
        # Normal edge'ler çizilirken, broken_edges set'indeki edge'ler atlanır.
        # Broken edge'ler daha sonra _draw_broken_edge() ile ayrı olarak
        # kırmızı kesikli çizgi olarak çizilir.
        # ====================================================================
        edge_x = []
        edge_y = []
        for u, v in self.graph.edges():
            # Skip broken edges (they're drawn separately)
            if (u, v) in self.broken_edges or (v, u) in self.broken_edges:
                continue
            x1, y1 = self.positions[u]
            x2, y2 = self.positions[v]
            edge_x.extend([x1, x2, np.nan])
            edge_y.extend([y1, y2, np.nan])
        
        # Convert to numpy arrays to ensure float dtype
        edge_x = np.array(edge_x, dtype=float)
        edge_y = np.array(edge_y, dtype=float)
        
        if len(edge_x) > 0:
            self.edge_lines = self.plot_widget.plot(
                edge_x, edge_y,
                pen=pg.mkPen(color=(71, 85, 105, 50), width=0.8), # slate-600 low alpha
                connect='finite'
            )
        else:
            self.edge_lines = None
        
        # ====================================================================
        # [CHAOS MONKEY FEATURE] Draw broken edges (red dashed)
        # ====================================================================
        # Tüm kırılmış edge'ler kırmızı kesikli çizgi olarak çizilir.
        # Bu, kullanıcıya hangi linklerin kırıldığını görsel olarak gösterir.
        # ====================================================================
        # Draw broken edges (red dashed) - redraw all broken edges
        for u, v in self.broken_edges:
            self._draw_broken_edge(u, v)
        
        # Draw broken edges (red dashed)
        for u, v in self.broken_edges:
            self._draw_broken_edge(u, v)
        
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
        
        # Intermediate Nodes Scatter (Path Nodes)
        # User requested "green dots style" but smaller. keeping path_color for consistency but styling them up.
        self.intermediate_scatter = pg.ScatterPlotItem(
            size=28, # Smaller than S/D (45) but larger than normal nodes (10)
            brush=pg.mkBrush(245, 158, 11, 255), # Default amber, changes with set_path
            pen=pg.mkPen('w', width=2),
            pxMode=True
        )
        self.plot_widget.addItem(self.intermediate_scatter)
        
        # Source & Dest Scatters (Large Pointers - Circle)
        self.source_scatter = pg.ScatterPlotItem(
            size=45, # Large to act as "Pointer"
            brush=pg.mkBrush(34, 197, 94, 255), # green-500
            pen=pg.mkPen('w', width=3), # Thicker white border
            pxMode=True
        )
        self.plot_widget.addItem(self.source_scatter)
        
        self.dest_scatter = pg.ScatterPlotItem(
            size=45, # Large to act as "Pointer"
            brush=pg.mkBrush(239, 68, 68, 255), # red-500
            pen=pg.mkPen('w', width=3), # Thicker white border
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
        
        # Convert hex/str color to QColor with alpha
        c = QColor(self.path_color)
        pen_color = (c.red(), c.green(), c.blue(), 255)
        glow_color = (c.red(), c.green(), c.blue(), 100)
        
        self.path_lines.setPen(pg.mkPen(
            color=pen_color, 
            width=3,
            style=Qt.DashLine # Dashed line for "simulated" look
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
        
        # Convert to numpy arrays
        edge_x = np.array(edge_x, dtype=float)
        edge_y = np.array(edge_y, dtype=float)
        
        self.path_lines.setData(edge_x, edge_y)
        self.path_lines.setData(edge_x, edge_y)
        self.path_glow.setData(edge_x, edge_y)

        # Update Intermediate Nodes Color
        self.intermediate_scatter.setBrush(pg.mkBrush(self.path_color))

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
        if not self.path or len(self.path) < 2:
            return
            
        # Create particles - Density based on path length
        # More particles for a "flow" effect
        num_particles = min(20, max(5, len(self.path) * 2))
        
        for i in range(num_particles):
            offset = i * (len(self.path) / num_particles)
            self.particles.append(PathParticle(self.path, self.positions, offset=offset, speed=0.03))
            
        self.timer.start(20) # Faster updates for smoother animation

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

    def _handle_edge_break(self, mouse_point):
        """
        [CHAOS MONKEY FEATURE] Sağ tıklama ile edge'i kır.
        
        Bu metod, kullanıcının mouse pozisyonuna en yakın edge'i bulur
        ve eğer threshold içindeyse edge'i kırar.
        
        Args:
            mouse_point: QPointF - Mouse'un view koordinatlarındaki pozisyonu
        
        İşlem Akışı:
        1. Tüm edge'leri (normal + broken) kontrol et
        2. Her edge için mouse noktasına olan mesafeyi hesapla
        3. En yakın edge'i bul
        4. Eğer threshold içindeyse ve henüz kırılmamışsa -> _break_edge() çağır
        
        Threshold: View genişliğinin %2'si (zoom seviyesine göre adaptif)
        """
        if self.graph is None:
            return
        
        min_dist = float('inf')
        closest_edge = None
        
        # Find closest edge to click point (including broken edges for visual feedback)
        all_edges = list(self.graph.edges())
        # Also check broken edges that might still be in positions
        for u, v in list(self.broken_edges):
            if u in self.positions and v in self.positions:
                all_edges.append((u, v))
        
        for u, v in all_edges:
            # Skip if already broken (we'll handle it separately)
            if (u, v) in self.broken_edges or (v, u) in self.broken_edges:
                # But still check distance for visual feedback
                pass
            
            if u not in self.positions or v not in self.positions:
                continue
            
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
        
        # Threshold for edge selection (adjust based on zoom level)
        view_range = self.plot_widget.plotItem.vb.viewRange()
        x_range = view_range[0][1] - view_range[0][0]
        threshold = x_range * 0.02  # 2% of view width
        
        if min_dist < threshold and closest_edge:
            u, v = closest_edge
            # Only break if not already broken
            if (u, v) not in self.broken_edges and (v, u) not in self.broken_edges:
                self._break_edge(u, v)
    
    def _break_edge(self, u: int, v: int):
        """
        [CHAOS MONKEY FEATURE] Edge'i kır ve görsel olarak işaretle.
        
        Bu metod:
        1. Edge'i broken_edges set'ine ekler
        2. NetworkX graph'tan edge'i kaldırır (algoritmalar artık bu edge'i kullanamaz)
        3. Görsel olarak kırmızı kesikli çizgi çizer
        4. edge_broken signal'ini emit eder (MainWindow otomatik re-optimization yapar)
        
        Args:
            u, v: Edge'in node ID'leri
        
        ÖNEMLİ NOTLAR:
        - Edge hem (u, v) hem de (v, u) formatında kontrol edilir (yönlü olmayan graf)
        - Graph'tan kaldırılan edge artık pathfinding algoritmaları tarafından kullanılamaz
        - Görsel temsil korunur (kullanıcı hangi linklerin kırıldığını görebilir)
        """
        # Check if already broken
        if (u, v) in self.broken_edges or (v, u) in self.broken_edges:
            return
        
        # Add to broken edges set
        self.broken_edges.add((u, v))
        
        # Remove from graph (but keep visual representation)
        if self.graph.has_edge(u, v):
            self.graph.remove_edge(u, v)
        
        # Visual update: Draw broken edge as red dashed line
        self._draw_broken_edge(u, v)
        
        # Emit signal for auto-rerouting
        # MainWindow._on_edge_broken() bu signal'i dinler ve otomatik olarak
        # mevcut kaynak/hedef için yeniden optimizasyon yapar
        self.edge_broken.emit(u, v)
        
        # Log message
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔴 Link {u}-{v} broken! Rerouting traffic...")
    
    def _draw_broken_edge(self, u: int, v: int):
        """
        [CHAOS MONKEY FEATURE] Kırılmış edge'i kırmızı kesikli çizgi olarak çiz.
        
        Görsel Geri Bildirim:
        - Renk: Kırmızı (239, 68, 68) - Kullanıcıya link'in kırıldığını gösterir
        - Stil: Kesikli çizgi (DashLine) - Normal edge'lerden ayırt edilebilir
        - Kalınlık: 2.0px - Dikkat çekici
        
        Çizilen line item broken_edge_lines listesine eklenir,
        böylece clear() çağrıldığında temizlenebilir.
        """
        if u not in self.positions or v not in self.positions:
            return
        
        x1, y1 = self.positions[u]
        x2, y2 = self.positions[v]
        
        # Create red dashed line
        broken_line = self.plot_widget.plot(
            [x1, x2], [y1, y2],
            pen=pg.mkPen(
                color=(239, 68, 68, 200),  # red-500 with high alpha
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
            # Simple interaction, can be expanded
            
    def _on_mouse_clicked(self, event):
        if self.graph is None:
            return
        
        # Check if right mouse button (button 3 in PyQtGraph)
        if event.button() != Qt.RightButton:
            # Left click - node selection (existing behavior)
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
            # ================================================================
            # [CHAOS MONKEY FEATURE] Right-click: Edge Break
            # ================================================================
            # Kullanıcı bir edge'e sağ tıkladığında, o edge kırılır.
            # Mouse pozisyonu view koordinatlarına çevrilir ve
            # _handle_edge_break() metodu en yakın edge'i bulup kırar.
            # ================================================================
            pos = event.scenePos()
            mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
            self._handle_edge_break(mouse_point)
    
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
        """
        Widget'ı temizle ve tüm state'i sıfırla.
        
        [CHAOS MONKEY FEATURE] Broken edges de burada temizlenir.
        Yeni bir graf yüklendiğinde veya reset yapıldığında,
        önceki broken edge'ler sıfırlanır.
        """
        self.graph = None
        self.positions = {}
        self.path = []
        self.source = None
        self.destination = None
        self.current_hovered_edge = None
        # [CHAOS MONKEY] Clear broken edges when graph is cleared
        self.broken_edges.clear()
        self.broken_edge_lines.clear()
        self.plot_widget.clear()
        self.timer.stop()
    
    def reset_broken_edges(self):
        """
        [CHAOS MONKEY FEATURE] Tüm kırılmış edge'leri geri yükle (reset).
        
        Bu metod, kırılmış edge'leri NetworkX graph'a geri ekler ve
        görsel temsillerini kaldırır. Kullanıcı "Reset" butonuna bastığında
        veya manuel olarak edge'leri geri yüklemek istediğinde kullanılabilir.
        
        NOT: Edge attribute'ları (delay, reliability, bandwidth) kaybolabilir,
        bu durumda varsayılan değerler kullanılır.
        """
        # Restore edges in graph
        for u, v in list(self.broken_edges):
            if not self.graph.has_edge(u, v):
                # Re-add edge with default attributes if needed
                # Note: Original attributes might be lost, so we use defaults
                self.graph.add_edge(u, v)
        
        # Clear broken edges
        self.broken_edges.clear()
        
        # Remove visual broken edge lines
        for line in self.broken_edge_lines:
            try:
                self.plot_widget.removeItem(line)
            except:
                pass
        self.broken_edge_lines.clear()
        
        # Redraw graph
        if self.graph is not None:
            self._draw_graph()
        
        if hasattr(self, 'placeholder'):
            self.placeholder.show()
            self.plot_widget.hide()
            self.controls_container.hide()
