from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication, QMainWindow
import pyqtgraph as pg
from datetime import datetime, timedelta
import random
import sys
from PyQt6.QtWidgets import QSizePolicy


class WorkpiecesGraphCard(QWidget):
    def __init__(self, start_time, data, parent=None):
        super().__init__(parent)

        self.start_time = start_time  # datetime object
        self.data = data  # List of integers, one per hour

        layout = QVBoxLayout()

        # Plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("Hourly Progress", color="black")
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setLabel('left', 'Workpieces')
        self.plot_widget.setLabel('bottom', 'Time (hour)')
        self.plot_widget.setMaximumHeight(180)
        self.plot_widget.setMinimumWidth(120)

        self.plot_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Disable zoom and pan
        # self.plot_widget.setMouseEnabled(x=False, y=False)
        self.plot_widget.hideButtons()

        # X-axis labels (hours)
        self.hours = [(self.start_time + timedelta(hours=i)).strftime('%H:%M') for i in range(len(data))]
        self.x = list(range(len(data)))

        # Create BarGraphItem and keep reference for updates
        self.bg = pg.BarGraphItem(x=self.x, height=self.data, width=0.6, brush='#905BA9')
        self.plot_widget.addItem(self.bg)
        self.plot_widget.getAxis('bottom').setTicks([list(zip(self.x, self.hours))])

        layout.addWidget(self.plot_widget)

        # Stats footer
        self.footer = QLabel()
        self.footer.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self.footer)

        self.setLayout(layout)

        # Initialize footer text
        self._update_footer()

    def _update_footer(self):
        total = sum(self.data)
        self.footer.setText(f"Start Time: {self.start_time.strftime('%H:%M')} | "
                            f"Now: {datetime.now().strftime('%H:%M')} | "
                            f"Total: {total} workpieces")

    def update_data(self, new_data):
        """Update the bar heights with new data"""
        self.data = new_data
        # Remove old bars
        self.plot_widget.removeItem(self.bg)
        # Add updated bars
        self.bg = pg.BarGraphItem(x=self.x, height=self.data, width=0.6, brush='#905BA9')
        self.plot_widget.addItem(self.bg)
        # Update footer
        self._update_footer()


# Run standalone
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Example start time 5 hours ago
    start_time = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=5)
    data = [random.randint(5, 20) for _ in range(6)]  # Data for 6 hours

    window = QMainWindow()
    window.setWindowTitle("Test Workpieces Graph Card")
    card = WorkpiecesGraphCard(start_time, data)
    window.setCentralWidget(card)
    window.resize(600, 400)
    window.show()

    sys.exit(app.exec())
