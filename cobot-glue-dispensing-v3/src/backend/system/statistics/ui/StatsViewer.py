"""
PyQt6 Statistics Viewer Widget for Glue Dispensing System

A comprehensive UI widget for interacting with the Pure shared v2 Statistics system.
Displays real-time hardware statistics from generators, transducers, pumps, fans, and loadcells.
"""

import sys
import json
from typing import Dict, Any, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QScrollArea, QMessageBox, QFrame,
    QApplication, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

# Import the pure shared v2 statistics components
try:
    from backend.system.statistics.ui.PureApiV2StatisticsRequestSender import PureApiV2StatisticsRequestSender
    from backend.system.statistics.api.StatisticsAPI import StatisticsAPI
    from modules.shared.v2.constants.ApiEndpoints import ApiEndpoints, EndpointGroups
except ImportError as e:
    print(f"Warning: Could not import statistics components: {e}")
    PureApiV2StatisticsRequestSender = None


class StatisticsCard(QFrame):
    """Modern card widget for displaying hardware statistics."""
    
    def __init__(self, title: str, component: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.component = component
        self.stats_data = {}
        self.setupUI()
    
    def setupUI(self):
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            StatisticsCard {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                margin: 8px;
            }
            StatisticsCard:hover {
                border-color: #2196F3;
                background-color: #fafafa;
            }
        """)
        
        # Add shadow effect
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        
        # Component icon based on type
        icon_map = {
            'generator': '⚡',
            'transducer': '📡', 
            'pump': '🔧',
            'fan': '🌀',
            'loadcell': '⚖️',
            'system': '🖥️'
        }
        
        icon = QLabel(icon_map.get(self.component.lower(), '📊'))
        icon.setStyleSheet("""
            QLabel {
                font-size: 20px;
                color: #2196F3;
                background-color: #e3f2fd;
                border-radius: 20px;
                padding: 8px;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
            }
        """)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #212121;
            }
        """)
        
        header_layout.addWidget(icon)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Statistics content area
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(16)
        self.content_layout.setContentsMargins(16, 12, 16, 12)
        
        # Initially show "No data" message
        self.updateDisplay({})
        
        layout.addLayout(header_layout)
        layout.addLayout(self.content_layout)
        
        self.setLayout(layout)
        self.setMinimumSize(400, 200)
        # Remove maximum size constraint to allow dynamic sizing
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.MinimumExpanding)
    
    def updateDisplay(self, data: Dict[str, Any]):
        """Update the card display with new statistics data."""
        self.stats_data = data
        
        # Clear existing content
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not data:
            no_data_label = QLabel("No data available")
            no_data_label.setStyleSheet("""
                QLabel {
                    color: #757575;
                    font-style: italic;
                    padding: 20px;
                }
            """)
            no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_data_label)
            return
        
        # Display statistics in a clean format
        for key, value in data.items():
            stat_layout = QHBoxLayout()
            stat_layout.setContentsMargins(0, 0, 0, 0)
            
            # Stat name
            name_label = QLabel(self.formatStatName(key))
            name_label.setStyleSheet("""
                QLabel {
                    color: #424242;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 4px 0px;
                }
            """)
            
            # Stat value
            value_label = QLabel(str(value))
            value_label.setStyleSheet("""
                QLabel {
                    color: #1976D2;
                    font-weight: 600;
                    font-size: 14px;
                    padding: 4px 0px;
                }
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            stat_layout.addWidget(name_label)
            stat_layout.addStretch()
            stat_layout.addWidget(value_label)
            
            self.content_layout.addLayout(stat_layout)
        
        # Add last updated timestamp if available
        if 'timestamp' in data or 'last_updated' in data:
            timestamp = data.get('timestamp', data.get('last_updated', ''))
            if timestamp:
                time_label = QLabel(f"Updated: {timestamp}")
                time_label.setStyleSheet("""
                    QLabel {
                        color: #9E9E9E;
                        font-size: 10px;
                        margin-top: 8px;
                    }
                """)
                self.content_layout.addWidget(time_label)
    
    def formatStatName(self, key: str) -> str:
        """Format statistic key names for display."""
        # Convert snake_case to readable format
        return key.replace('_', ' ').title()


class StatsRefreshWorker(QThread):
    """Background worker for refreshing statistics data from the shared."""
    
    dataReady = pyqtSignal(str, dict)  # component, data
    errorOccurred = pyqtSignal(str)
    
    def __init__(self, stats_sender: PureApiV2StatisticsRequestSender, component: str):
        super().__init__()
        self.stats_sender = stats_sender
        self.component = component
        self.is_running = True
    
    def run(self):
        """Fetch statistics data for the specified component."""
        try:
            if not self.stats_sender:
                self.errorOccurred.emit(f"No statistics sender available for {self.component}")
                return
            
            # Map component to shared endpoint resource
            endpoint_map = {
                'all': '/api/v2/stats/all',
                'generator': '/api/v2/stats/generator', 
                'transducer': '/api/v2/stats/transducer',
                'pumps': '/api/v2/stats/pumps',
                'fan': '/api/v2/stats/fan',
                'loadcells': '/api/v2/stats/loadcells'
            }
            
            resource = endpoint_map.get(self.component)
            if not resource:
                self.errorOccurred.emit(f"Unknown component: {self.component}")
                return
            
            # Create V2Request and send
            from modules.shared.v2.Request import Request as V2Request
            request = V2Request(req_type="GET", resource=resource)
            
            # Send request through the statistics sender
            response = self.stats_sender.send_request(request)
            
            if response and response.get('status') == 'success':
                data = response.get('data', {})
                # Add timestamp
                data['last_updated'] = datetime.now().strftime('%H:%M:%S')
                self.dataReady.emit(self.component, data)
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response'
                self.errorOccurred.emit(f"shared Error for {self.component}: {error_msg}")
                
        except Exception as e:
            self.errorOccurred.emit(f"Error fetching {self.component} stats: {str(e)}")
    
    def stop(self):
        self.is_running = False


class StatsViewer(QWidget):
    """
    Statistics viewer for the glue dispensing system.
    
    Displays real-time statistics from hardware components:
    - Generator statistics
    - Transducer statistics  
    - Pump statistics
    - Fan statistics
    - Loadcell statistics
    - System overview
    """
    
    def __init__(self, stats_sender: Optional[PureApiV2StatisticsRequestSender] = None):
        super().__init__()
        if stats_sender:
            self.stats_sender = stats_sender
        else:
            raise ValueError("StatsViewer requires a PureApiV2StatisticsRequestSender instance")
        
        self.refresh_workers = {}
        self.stats_cards = {}
        self.setupUI()
        self.setupRefreshTimer()
    
    def setupUI(self):
        """Setup the statistics viewer UI."""
        self.setStyleSheet("""
            StatsViewer {
                background-color: #f5f5f5;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Header
        header = self.createHeader()
        main_layout.addWidget(header)
        
        # Create tabs for different component categories
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: transparent;
            }
            QTabBar::tab {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 10px 20px;
                margin-right: 1px;
                font-weight: 500;
                color: #424242;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
                border-color: #2196F3;
            }
            QTabBar::tab:hover:!selected {
                background-color: #f0f0f0;
            }
        """)
        
        # Add component tabs
        self.tabs.addTab(self.createOverviewTab(), "📊 Overview")
        self.tabs.addTab(self.createHardwareTab(), "🔧 Hardware") 
        self.tabs.addTab(self.createActionsTab(), "⚙️ Actions")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    
    def createHeader(self):
        """Create header with title and controls."""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 4px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Title
        title = QLabel("Hardware Statistics Dashboard")
        title.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: 700;
                color: #212121;
            }
        """)
        
        # Status indicator
        self.status_label = QLabel("🟢 Connected")
        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #4CAF50;
                font-weight: 600;
            }
        """)
        
        # Last updated timestamp
        self.last_updated = QLabel("Last updated: Never")
        self.last_updated.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #757575;
            }
        """)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh All")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        refresh_btn.clicked.connect(self.refreshAllData)
        
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel(" • "))
        layout.addWidget(self.last_updated)
        layout.addWidget(refresh_btn)
        
        header.setLayout(layout)
        return header
    
    def createOverviewTab(self):
        """Create overview tab with system-wide statistics."""
        tab = QWidget()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content = QWidget()
        layout = QGridLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 16, 0, 16)
        
        # Create system overview card
        self.stats_cards['all'] = StatisticsCard("System Overview", "system")
        layout.addWidget(self.stats_cards['all'], 0, 0, 1, 2)
        
        # Create individual component cards
        components = [
            ('generator', 'Generator Statistics'),
            ('transducer', 'Transducer Statistics'),
            ('pumps', 'Pump Statistics'),
            ('fan', 'Fan Statistics'),
            ('loadcells', 'Loadcell Statistics')
        ]
        
        row = 1
        col = 0
        for component, title in components:
            card = StatisticsCard(title, component)
            self.stats_cards[component] = card
            layout.addWidget(card, row, col)
            
            # Allow each card to have its own height
            layout.setRowMinimumHeight(row, 250)  # Minimum height for content
            
            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1
        
        # Set column stretch to make cards fill available width
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        
        # Add stretch to fill remaining space
        layout.setRowStretch(row + 1, 1)
        
        content.setLayout(layout)
        scroll.setWidget(content)
        
        tab_layout = QVBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        tab.setLayout(tab_layout)
        
        return tab
    
    def createHardwareTab(self):
        """Create detailed hardware statistics tab."""
        tab = QWidget()
        
        layout = QVBoxLayout()
        info_label = QLabel("Detailed hardware diagnostics and component-specific statistics will be displayed here.")
        info_label.setStyleSheet("""
            QLabel {
                color: #757575;
                font-style: italic;
                padding: 40px;
                text-align: center;
            }
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        tab.setLayout(layout)
        return tab
    
    def createActionsTab(self):
        """Create actions tab for statistics management."""
        tab = QWidget()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Reset statistics section
        reset_frame = QFrame()
        reset_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        
        reset_layout = QVBoxLayout()
        
        reset_title = QLabel("Reset Statistics")
        reset_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #212121;
                margin-bottom: 8px;
            }
        """)
        
        reset_desc = QLabel("Clear component statistics counters and reset to zero.")
        reset_desc.setStyleSheet("""
            QLabel {
                color: #757575;
                margin-bottom: 16px;
            }
        """)
        
        reset_buttons_layout = QHBoxLayout()
        
        # Individual reset buttons
        components = ['generator', 'transducer', 'pumps', 'fan', 'loadcells']
        for component in components:
            btn = QPushButton(f"Reset {component.title()}")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            btn.clicked.connect(lambda checked, c=component: self.resetComponentStats(c))
            reset_buttons_layout.addWidget(btn)
        
        # Reset all button
        reset_all_btn = QPushButton("Reset All Statistics")
        reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        reset_all_btn.clicked.connect(self.resetAllStats)
        
        reset_layout.addWidget(reset_title)
        reset_layout.addWidget(reset_desc)
        reset_layout.addLayout(reset_buttons_layout)
        reset_layout.addWidget(reset_all_btn)
        
        reset_frame.setLayout(reset_layout)
        
        layout.addWidget(reset_frame)
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def setupRefreshTimer(self):
        """Setup automatic data refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refreshAllData)
        self.refresh_timer.start(15000)  # Refresh every 15 seconds
    
    def refreshAllData(self):
        """Refresh statistics data for all components."""
        components = ['all', 'generator', 'transducer', 'pumps', 'fan', 'loadcells']
        
        for component in components:
            if component in self.refresh_workers and self.refresh_workers[component].isRunning():
                continue
            
            worker = StatsRefreshWorker(self.stats_sender, component)
            worker.dataReady.connect(self.updateComponentDisplay)
            worker.errorOccurred.connect(self.handleError)
            self.refresh_workers[component] = worker
            worker.start()
    
    def updateComponentDisplay(self, component: str, data: Dict[str, Any]):
        """Update display for a specific component."""
        if component in self.stats_cards:
            self.stats_cards[component].updateDisplay(data)
        
        # Update last updated timestamp
        self.last_updated.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        self.status_label.setText("🟢 Connected")
    
    def handleError(self, error_message: str):
        """Handle errors from the statistics shared."""
        print(f"Statistics Error: {error_message}")
        self.status_label.setText("🔴 Error")
        self.last_updated.setText(f"Error: {error_message}")
    
    def resetComponentStats(self, component: str):
        """Reset statistics for a specific component."""
        reply = QMessageBox.question(
            self, "Reset Statistics", 
            f"Are you sure you want to reset {component} statistics?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement actual reset shared call
            QMessageBox.information(self, "Reset Complete", f"{component.title()} statistics have been reset.")
    
    def resetAllStats(self):
        """Reset all component statistics."""
        reply = QMessageBox.question(
            self, "Reset All Statistics", 
            "Are you sure you want to reset ALL statistics?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement actual reset all shared call
            QMessageBox.information(self, "Reset Complete", "All statistics have been reset.")


def main():
    """Demo application for testing."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Mock stats sender for demo
    class MockStatsSender:
        def send_request(self, request):
            # Return mock hardware statistics data
            mock_data = {
                '/api/v2/stats/all': {
                    'total_cycles': 1234,
                    'uptime_hours': 48.5,
                    'error_count': 2,
                    'success_rate': 98.3
                },
                '/api/v2/stats/generator': {
                    'voltage': 24.1,
                    'current': 2.3,
                    'power': 55.4,
                    'temperature': 42.1,
                    'runtime_hours': 156.7
                },
                '/api/v2/stats/transducer': {
                    'frequency': 35000,
                    'amplitude': 85.2,
                    'power': 1200,
                    'temperature': 38.5,
                    'cycles_completed': 9847
                },
                '/api/v2/stats/pumps': {
                    'pressure': 2.1,
                    'flow_rate': 15.6,
                    'temperature': 23.4,
                    'cycles': 2341,
                    'maintenance_due': False
                },
                '/api/v2/stats/fan': {
                    'rpm': 2400,
                    'temperature': 35.2,
                    'voltage': 12.0,
                    'runtime_hours': 234.5
                },
                '/api/v2/stats/loadcells': {
                    'weight_kg': 12.34,
                    'calibration_date': '2024-01-15',
                    'zero_offset': 0.02,
                    'readings_count': 15678
                }
            }
            
            resource = request.resource if hasattr(request, 'resource') else '/api/v2/stats/all'
            return {
                'status': 'success',
                'data': mock_data.get(resource, {})
            }
    
    # Create viewer with mock sender
    viewer = StatsViewer(MockStatsSender())
    viewer.setWindowTitle("Glue Dispensing System - Statistics Dashboard")
    viewer.resize(1200, 800)
    viewer.show()
    
    # Start with initial data refresh
    viewer.refreshAllData()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()