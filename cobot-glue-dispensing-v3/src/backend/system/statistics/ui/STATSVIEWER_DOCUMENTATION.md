# StatsViewer - Pure API v2 Statistics UI Documentation

## 📊 Overview

The **StatsViewer** is a comprehensive PyQt6 widget that provides a modern, real-time interface for interacting with the Pure API v2 Statistics system. It offers complete statistics viewing, management, and reporting capabilities through an intuitive tabbed interface.

## 🏗️ Architecture

### Actual System Stack (Corrected)

The statistics system uses **data models** and **file persistence**, NOT hardware interfaces:

### Complete System Stack

```
┌─────────────────────────────────────┐
│  StatsViewer (PyQt6 UI)             │  ← User Interface Layer
├─────────────────────────────────────┤
│  PureApiV2StatisticsRequestSender   │  ← Pure API v2 Request Layer
├─────────────────────────────────────┤
│  DomesticRequestSender              │  ← Local Transport Layer
├─────────────────────────────────────┤
│  HandlerAdapter                     │  ← Method Name Bridge
├─────────────────────────────────────┤
│  PureApiV2StatisticsHandler         │  ← Pure API v2 Handler
├─────────────────────────────────────┤
│  StatisticsAPI                      │  ← API Abstraction Layer
├─────────────────────────────────────┤
│  StatsService                       │  ← Business Logic Layer
├─────────────────────────────────────┤
│  Controller (Data Models)           │  ← Data Model Container
│  + StatsPersistence                 │  ← File Storage Layer
└─────────────────────────────────────┘
```

### Data Flow

**Request Flow (UI → Hardware)**:
1. User clicks "Refresh" in StatsViewer
2. PureApiV2StatisticsRequestSender creates `V2Request(req_type="GET", resource="/api/v2/stats/all")`
3. DomesticRequestSender calls `handleRequest(v2_request)`
4. HandlerAdapter bridges to `pure_handler.handle(v2_request)`
5. PureApiV2StatisticsHandler routes to appropriate handler method
6. StatisticsAPI calls service methods
7. StatsService manages data models + persistence
8. Controller provides access to data models (GeneratorStats, PumpStats, etc.)
9. StatsPersistence loads/saves data from files

**Response Flow (Hardware → UI)**:
1. Data flows back through the stack
2. StatsViewer receives JSON response
3. UI updates cards, tables, and logs automatically

## 🎨 User Interface Features

### 📱 4-Tab Interface

#### 1. **Overview Tab** - Real-time Dashboard
- **Statistics Cards**: Visual metric displays with hover effects
  - Generator Runtime (hours)
  - Active Pumps (count)  
  - Total Cycles (count)
  - System Efficiency (%)
  - Fan Speed (%)
  - Total Volume (L)
- **Recent Activity Log**: Timestamped operation history
- **Auto-refresh**: Updates every 5 seconds (toggleable)

#### 2. **Detailed View Tab** - Comprehensive Data
- **Filterable Statistics Table**: All system parameters
- **Component Filters**: Generator, Pumps, Fan, Transducer, Load Cells
- **Time Range Filters**: Last Hour, Day, Week, Month, All Time
- **Sortable Columns**: Component, Parameter, Current Value, Min, Max, Average
- **Real-time Updates**: Live data refresh

#### 3. **Management Tab** - System Control
- **Component Reset Controls**:
  - Reset Generator Statistics
  - Reset Fan Statistics  
  - Reset Transducer Statistics
  - Reset All Statistics (with confirmation)
- **Pump-Specific Controls**:
  - Select Pump ID (1-10)
  - Reset Motor Statistics
  - Reset Belt Statistics
- **Load Cell Management**:
  - Select Load Cell ID (1-5)
  - Reset Load Cell Statistics
- **Operation Log**: Detailed command history with timestamps

#### 4. **Reports Tab** - Analytics & Export
- **Report Generation**:
  - Daily Reports
  - Weekly Reports
  - Monthly Reports
  - Date selection with calendar
- **Export Options**:
  - CSV Export
  - JSON Export
  - PDF Export (planned)
- **Report Preview**: Live preview of generated reports

### 🎯 Key UI Components

#### Statistics Cards
```python
class StatisticsCard(QWidget):
    """Individual metric display with hover effects and animations."""
    
    def updateValue(self, value: str, unit: str = ""):
        """Update card display with new value and unit."""
```

#### Background Data Refresh
```python
class StatsRefreshWorker(QThread):
    """Non-blocking background worker for data fetching."""
    
    dataReady = pyqtSignal(dict)      # Emitted when data is ready
    errorOccurred = pyqtSignal(str)   # Emitted on errors
```

## 🚀 Installation & Setup

### Prerequisites

```bash
# Required Python packages
pip install PyQt6
pip install python-dateutil
```

### Project Structure

```
GlueDispensingApplication/
├── statistics/
│   ├── ui/
│   │   ├── StatsViewer.py                    # Main UI widget
│   │   └── PureApiV2StatisticsRequestSender.py
│   ├── backend/
│   │   ├── PureApiV2StatisticsHandler.py
│   │   ├── StatsService.py
│   │   ├── StatisticsController.py
│   │   └── StatsPersistence.py
│   └── api/
│       └── StatisticsAPI.py
```

## 💻 Usage Examples

### 🔧 Standalone Application

Run StatsViewer as a complete standalone application:

```bash
# Navigate to project directory
cd /path/to/cobot-soft-glue-dispencing-v2

# Run standalone
python3 system/statistics/ui/StatsViewer.py
```

**What happens:**
1. Creates complete backend stack locally
2. Initializes data persistence (`stats_data.json`)
3. Sets up hardware controller interface
4. Launches PyQt6 application with full functionality

### 🏗️ Embedded in Main Application

Integrate StatsViewer into your existing PyQt6 application:

```python
from GlueDispensingApplication.statistics.ui.StatsViewer import StatsViewer
from GlueDispensingApplication.statistics.ui.PureApiV2StatisticsRequestSender import PureApiV2StatisticsRequestSender

class MainApplicationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupStatisticsTab()
    
    def setupStatisticsTab(self):
        # Use your existing request sender
        stats_sender = PureApiV2StatisticsRequestSender(your_existing_sender)
        
        # Create and embed the viewer
        self.stats_viewer = StatsViewer(stats_sender)
        
        # Add to your tab widget
        self.tab_widget.addTab(self.stats_viewer, "📊 Statistics")
        
        # Or add to layout
        # your_layout.addWidget(self.stats_viewer)
```

### 🌐 Network-Based Setup

Connect to remote statistics service:

```python
from GlueDispensingApplication.statistics.ui.StatsViewer import StatsViewer
from GlueDispensingApplication.statistics.ui.PureApiV2StatisticsRequestSender import PureApiV2StatisticsRequestSender

class NetworkStatsProvider:
    def __init__(self, server_url):
        self.server_url = server_url
    
    def sendRequest(self, request):
        # Send V2Request to remote server
        response = requests.post(f"{self.server_url}/api/v2/stats", 
                               json=request.to_dict())
        return response.json()

# Usage
network_provider = NetworkStatsProvider("http://your-server:8080")
stats_sender = PureApiV2StatisticsRequestSender(network_provider)
viewer = StatsViewer(stats_sender)
viewer.show()
```

### 🔌 Custom Data Provider

Create custom data source integration:

```python
class CustomHardwareProvider:
    def __init__(self):
        self.modbus_client = YourModbusClient()
        self.database = YourDatabase()
    
    def sendRequest(self, request):
        """Handle Pure shared v2 requests with real hardware data."""
        resource = request.resource
        method = request.req_type
        
        if resource == "/api/v2/stats/all" and method == "GET":
            return {
                "status": "success",
                "data": {
                    "generator": {
                        "runtime": self.modbus_client.read_generator_runtime(),
                        "cycles": self.database.get_generator_cycles()
                    },
                    "pumps": self.get_all_pump_data(),
                    "fan": self.get_fan_data(),
                    "transducer": self.get_transducer_data()
                }
            }
        elif "/stats/reset/" in resource and method == "POST":
            return self.handle_reset_operation(resource)
        # Handle other endpoints...
    
    def get_all_pump_data(self):
        pumps = []
        for pump_id in range(1, 4):  # Pumps 1-3
            pumps.append({
                "id": pump_id,
                "volume": self.modbus_client.read_pump_volume(pump_id),
                "cycles": self.database.get_pump_cycles(pump_id),
                "motor_temperature": self.modbus_client.read_pump_temp(pump_id)
            })
        return pumps

# Usage
hardware_provider = CustomHardwareProvider()
stats_sender = PureApiV2StatisticsRequestSender(hardware_provider)
viewer = StatsViewer(stats_sender)
```

## 🛠️ Advanced Configuration

### Custom Styling

```python
# Apply custom theme
viewer = StatsViewer(stats_sender)

# Override default styles
viewer.setStyleSheet("""
    StatsViewer {
        background-color: #2b2b2b;
        color: white;
    }
    StatisticsCard {
        background-color: #3c3c3c;
        border: 1px solid #555;
    }
    QPushButton {
        background-color: #4CAF50;
        color: white;
    }
""")
```

### Auto-refresh Configuration

```python
viewer = StatsViewer(stats_sender)

# Disable auto-refresh
viewer.auto_refresh_cb.setChecked(False)

# Change refresh interval (default 5000ms)
viewer.refresh_timer.setInterval(10000)  # 10 seconds

# Custom refresh callback
def on_data_updated(data):
    print(f"Received {len(data)} data points")
    # Custom processing...

viewer.refresh_worker.dataReady.connect(on_data_updated)
```

### Component Visibility Control

```python
# Hide specific tabs
viewer.tab_widget.removeTab(3)  # Remove Reports tab

# Hide specific controls
viewer.reset_all_btn.hide()  # Hide dangerous reset button

# Custom tab order
viewer.tab_widget.insertTab(0, custom_tab, "Custom View")
```

## 🔗 API Integration

### Supported Pure API v2 Endpoints

The StatsViewer automatically handles all Pure API v2 statistics endpoints:

#### **Read Operations (GET)**
```python
GET /api/v2/stats/all                    # Get all statistics
GET /api/v2/stats/generator              # Get generator stats
GET /api/v2/stats/transducer             # Get transducer stats
GET /api/v2/stats/pumps                  # Get all pump stats  
GET /api/v2/stats/pumps/{pump_id}        # Get specific pump stats
GET /api/v2/stats/fan                    # Get fan stats
GET /api/v2/stats/loadcells              # Get all loadcell stats
GET /api/v2/stats/loadcells/{loadcell_id} # Get specific loadcell stats
```

#### **Reset Operations (POST)**
```python
POST /api/v2/stats/reset/all                    # Reset all statistics
POST /api/v2/stats/reset/generator              # Reset generator stats
POST /api/v2/stats/reset/transducer             # Reset transducer stats
POST /api/v2/stats/reset/fan                    # Reset fan stats
POST /api/v2/stats/reset/pumps/{pump_id}/motor  # Reset pump motor
POST /api/v2/stats/reset/pumps/{pump_id}/belt   # Reset pump belt
POST /api/v2/stats/reset/loadcells/{loadcell_id} # Reset loadcell
```

#### **Export Operations (POST)**
```python
POST /api/v2/stats/export/csv            # Export as CSV
POST /api/v2/stats/export/json           # Export as JSON
```

#### **Reporting Operations (GET)**
```python
GET /api/v2/stats/reports/daily          # Daily report
GET /api/v2/stats/reports/weekly         # Weekly report
GET /api/v2/stats/reports/monthly        # Monthly report
```

### Request/Response Format

#### Sample Request
```python
# Generated automatically by StatsViewer
V2Request(
    req_type="GET",                    # HTTP method
    resource="/api/v2/stats/pumps/5",  # Endpoint URL with parameters
    action=None,                       # No legacy actions (Pure shared v2)
    data={}                           # Optional request body
)
```

#### Sample Response
```json
{
    "status": "success",
    "message": "Retrieved statistics for pump 5",
    "data": {
        "id": 5,
        "volume": 125.7,
        "cycles": 230,
        "motor_temperature": 65.2,
        "belt_tension": 85.1,
        "last_maintenance": "2025-09-01T10:30:00Z"
    },
    "error": {}
}
```

## 🎛️ User Interface Guide

### Overview Tab Usage

1. **Statistics Cards**: Hover over cards to see additional information
2. **Auto-refresh Toggle**: Enable/disable automatic data updates
3. **Manual Refresh**: Click "Refresh" button for immediate update
4. **Activity Log**: Scroll through recent operations and system events

### Detailed View Usage

1. **Component Filter**: Select specific components to view
2. **Time Range Filter**: Choose data time span
3. **Apply Filters**: Click to apply selected filters
4. **Table Sorting**: Click column headers to sort data
5. **Row Selection**: Click rows for detailed information

### Management Tab Usage

1. **Component Resets**: 
   - Click individual component reset buttons
   - Confirm dangerous operations
   - Monitor operation log for results
2. **Pump Controls**:
   - Select pump ID with spin box
   - Choose motor or belt reset
   - View operation results in log
3. **Load Cell Controls**:
   - Select load cell ID
   - Reset individual load cell data

### Reports Tab Usage

1. **Report Generation**:
   - Select report type (Daily/Weekly/Monthly)
   - Choose date with calendar picker
   - Click "Generate Report"
   - View preview in text area
2. **Export Operations**:
   - Select export format (CSV/JSON/PDF)
   - Choose current view or all data
   - Click export button
   - Check operation log for file location

## 🔧 Troubleshooting

### Common Issues

#### Issue: "No data displayed"
**Cause**: Backend stack not properly initialized
**Solution**:
```python
# Ensure proper initialization order:
persistence = StatsPersistence("stats_data.json")
controller = Controller()  # Creates data model container
service = StatsService(controller=controller, persistence=persistence)
api = StatisticsAPI(service=service)  # No request_sender parameter
# Note: Controller is a data container, not hardware interface
```

#### Issue: "Method not found error"
**Cause**: Missing HandlerAdapter for method name bridging
**Solution**:
```python
class HandlerAdapter:
    def handleRequest(self, request, data=None):
        return self.pure_handler.handle(request)

adapter = HandlerAdapter(handler)
sender = DomesticRequestSender(adapter)  # Use adapter, not handler directly
```

#### Issue: "Import errors"
**Cause**: Missing dependencies or incorrect paths
**Solution**:
```bash
# Install required packages
pip install PyQt6 python-dateutil

# Verify Python path includes project root
export PYTHONPATH="/path/to/cobot-soft-glue-dispencing-v2:$PYTHONPATH"
```

#### Issue: "UI freezing during refresh"
**Cause**: Blocking operations on main thread
**Solution**: The StatsRefreshWorker automatically handles background operations. Ensure it's not disabled:
```python
# Check if background refresh is working
if viewer.refresh_worker and viewer.refresh_worker.running:
    print("Background refresh active")
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug output
viewer = StatsViewer(stats_sender)
viewer.show()
```

### Performance Optimization

For large datasets:

```python
# Reduce refresh frequency
viewer.refresh_timer.setInterval(10000)  # 10 seconds instead of 5

# Limit table rows
viewer.stats_table.setRowCount(100)  # Maximum 100 rows

# Disable animations
viewer.setUpdatesEnabled(False)  # During bulk updates
# ... update operations ...
viewer.setUpdatesEnabled(True)
```

## 🔮 Future Enhancements

### Planned Features

1. **Real-time Charting**: Interactive graphs and trend analysis
2. **Alert System**: Configurable thresholds and notifications
3. **Custom Dashboards**: User-configurable widget layouts
4. **Data Export**: Advanced filtering and scheduling
5. **Mobile Responsive**: Touch-friendly interface adaptations
6. **Multi-language**: Internationalization support
7. **Plugin System**: Custom widget extensions

### Extensibility Points

```python
# Custom statistics cards
class CustomMetricCard(StatisticsCard):
    def __init__(self, title, calculation_func):
        super().__init__(title)
        self.calculation_func = calculation_func
    
    def updateValue(self, data):
        calculated_value = self.calculation_func(data)
        super().updateValue(calculated_value, "units")

# Custom export formats
class CustomExporter:
    def export_to_excel(self, data):
        # Implementation for Excel export
        pass

# Custom data filters
class AdvancedDataFilter:
    def filter_by_efficiency(self, data, min_efficiency):
        # Custom filtering logic
        pass
```

## 📋 API Reference

### StatsViewer Class

```python
class StatsViewer(QWidget):
    """Main statistics viewer widget."""
    
    def __init__(self, stats_sender: PureApiV2StatisticsRequestSender = None):
        """Initialize with optional stats sender."""
    
    def refreshData(self):
        """Manually trigger data refresh."""
    
    def toggleAutoRefresh(self, enabled: bool):
        """Enable/disable automatic refresh."""
    
    def updateUI(self):
        """Update all UI components with current data."""
```

### StatisticsCard Class

```python
class StatisticsCard(QWidget):
    """Individual statistics display card."""
    
    def __init__(self, title: str, value: str = "0", unit: str = "", icon: str = None):
        """Create new statistics card."""
    
    def updateValue(self, value: str, unit: str = ""):
        """Update displayed value and unit."""
```

### StatsRefreshWorker Class

```python
class StatsRefreshWorker(QThread):
    """Background worker for non-blocking data refresh."""
    
    dataReady = pyqtSignal(dict)      # Data received signal
    errorOccurred = pyqtSignal(str)   # Error occurred signal
    
    def __init__(self, stats_sender: PureApiV2StatisticsRequestSender):
        """Initialize with stats sender."""
    
    def run(self):
        """Execute background data fetch."""
```

## 📄 License & Support

### License
This code is part of the Cobot Soft v2 glue dispensing system and is subject to the project's license terms.

### Support
For issues, questions, or contributions:

1. **Documentation**: Check this comprehensive guide first
2. **Code Issues**: Review the troubleshooting section
3. **Feature Requests**: Consider the extensibility points for custom implementations
4. **Integration Help**: Follow the usage examples for your specific use case

### Contributing

When extending StatsViewer:

1. **Follow Pure API v2**: All new endpoints must use resource URLs, no legacy actions
2. **Maintain Threading**: Use background workers for non-blocking operations  
3. **Preserve Architecture**: Respect the layered architecture pattern
4. **Add Documentation**: Update this guide for new features
5. **Test Integration**: Verify compatibility with existing components

---

## 🎯 Quick Start Checklist

- [ ] Install PyQt6 and dependencies
- [ ] Verify project structure and imports
- [ ] Run standalone: `python3 GlueDispensingApplication/statistics/ui/StatsViewer.py`
- [ ] Check data display in Overview tab
- [ ] Test management operations in Management tab  
- [ ] Generate report in Reports tab
- [ ] Verify auto-refresh functionality
- [ ] Review operation logs for any errors

**Congratulations!** You now have a fully functional, Pure API v2 compliant statistics viewer with comprehensive data model management and persistence capabilities! 🎉