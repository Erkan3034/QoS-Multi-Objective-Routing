"""
Live Convergence Plot Widget - Real-time visualization of GA progress
"""
try:
    import matplotlib
    matplotlib.use('Qt5Agg')  # Use Qt5 backend
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.lines import Line2D
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    # Create dummy classes for graceful degradation
    class FigureCanvas:
        pass
    class Figure:
        pass
    class Line2D:
        pass

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt
from typing import List


class ConvergenceWidget(QWidget):
    """
    Live convergence plot widget showing Generation vs. Cost in real-time.
    
    Performance optimized:
    - Line2D object initialized once in __init__
    - Updates use set_data() instead of replotting
    - Uses draw_idle() for non-blocking UI updates
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.generations: List[int] = []
        self.fitness_values: List[float] = []
        self.line: Line2D = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15) # Add padding
        layout.setSpacing(4)
        
        # Semi-transparent background
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(15, 23, 42, 0.90);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        
        if not MATPLOTLIB_AVAILABLE:
            # Graceful degradation: show message if matplotlib is missing
            error_label = QLabel("Matplotlib not available.\nConvergence plot disabled.")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: #94a3b8; font-size: 11px; padding: 20px;")
            layout.addWidget(error_label)
            return
        
        # Title
        title_label = QLabel("Yakınsama Grafiği")
        title_label.setStyleSheet("""
            color: #94a3b8;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 0px;
        """)
        layout.addWidget(title_label)
        
        # Matplotlib Figure - Larger size for better visibility
        self.figure = Figure(figsize=(3.5, 2.5), facecolor='#1e293b')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background: transparent;")
        # Set size policy to allow expansion
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumHeight(180)  # Minimum height for visibility
        
        # Axes setup
        self.ax = self.figure.add_subplot(111, facecolor='#1e293b')
        self.ax.set_xlabel('Nesil', color='#94a3b8', fontsize=9)
        self.ax.set_ylabel('Maliyet', color='#94a3b8', fontsize=9)
        self.ax.tick_params(colors='#64748b', labelsize=8)
        self.ax.spines['bottom'].set_color('#334155')
        self.ax.spines['top'].set_color('#334155')
        self.ax.spines['right'].set_color('#334155')
        self.ax.spines['left'].set_color('#334155')
        self.ax.grid(True, alpha=0.2, color='#334155', linestyle='--')
        
        # [PERFORMANCE] Initialize Line2D object once
        # This avoids recreating the line on every update
        self.line, = self.ax.plot(
            [], [],
            color='#22c55e',  # emerald-500 (green)
            linewidth=1.5,
            marker='o',
            markersize=3,
            markerfacecolor='#22c55e',
            markeredgecolor='#10b981',
            alpha=0.8
        )
        
        # Set initial empty state
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 1)
        
        layout.addWidget(self.canvas)
        
        # Initially hidden
        self.hide()
    
    def update_plot(self, generation: int, fitness: float):
        """
        Update the plot with new data point.
        
        Args:
            generation: Current generation number
            fitness: Best fitness value at this generation
        """
        if not MATPLOTLIB_AVAILABLE or self.line is None:
            return
        
        # Append new data
        self.generations.append(generation)
        self.fitness_values.append(fitness)
        
        # [PERFORMANCE] Update line data using set_data() instead of replotting
        self.line.set_data(self.generations, self.fitness_values)
        
        # Rescale axes to fit data
        if len(self.generations) > 0:
            self.ax.relim()
            self.ax.autoscale_view()
            
            # Ensure minimum range for better visualization
            x_range = max(10, max(self.generations) - min(self.generations) + 1)
            y_min = min(self.fitness_values) if self.fitness_values else 0
            y_max = max(self.fitness_values) if self.fitness_values else 1
            y_range = max(0.1, (y_max - y_min) * 1.1) if y_max > y_min else 1.0
            
            self.ax.set_xlim(0, max(10, max(self.generations) + 1))
            self.ax.set_ylim(max(0, y_min - y_range * 0.05), y_max + y_range * 0.05)
        
        # [PERFORMANCE] Use draw_idle() for non-blocking UI updates
        # This schedules a redraw without blocking the main thread
        self.canvas.draw_idle()
    
    def reset_plot(self):
        """Clear all data and reset the plot."""
        if not MATPLOTLIB_AVAILABLE or self.line is None:
            return
        
        self.generations.clear()
        self.fitness_values.clear()
        
        # Reset line data
        self.line.set_data([], [])
        
        # Reset axes
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 1)
        
        # Redraw
        self.canvas.draw_idle()
        
        # Show widget when reset (ready for new data)
        self.show()

