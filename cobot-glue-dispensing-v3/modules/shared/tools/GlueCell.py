# from system.tools.enums.GlueType import GlueType
from enum import Enum
import requests
import json
import threading
from backend.system.SensorPublisher import Sensor
from communication_layer.api.v1.topics import GlueTopics
from modules.shared.MessageBroker import MessageBroker
from backend.system.utils.custom_logging import ColoredFormatter, LoggingLevel
from pathlib import Path
from backend.system.utils import PathResolver
import logging
import inspect
import time
"""
   Enum representing the types of glue used in the application.

   Attributes:
       TypeA (str): Represents Glue Type A.
       TypeB (str): Represents Glue Type B.
       TypeC (str): Represents Glue Type C.
   """

STORAGE_PATH = Path(__file__).parent.parent / ".."/"robot_application"/"glue_dispensing_application"/"storage"
print(f"Storage path: {STORAGE_PATH}")

TARE_ENDPOINT = "/tare?loadCellId={current_cell}"
GET_CONFIG_ENDPOINT = "/get-config?loadCellId={current_cell}"
UPDATE_OFFSET_ENDPOINT = "/update-config?loadCellId={current_cell}&offset={offset}"
UPDATE_SCALE_ENDPOINT = "/update-config?loadCellId={current_cell}&scale={scale}"
UPDATE_CONFIG_ENDPOINT = "/update-config?loadCellId={current_cell}&offset={offset}&scale={scale}"
"""offset - /update-config?loadCellId={current_cell}&offset={offset}"""
"""scale - /update-config?loadCellId={current_cell}&scale={scale}"""

"""offset/scale - /get-config?loadCellId={current_cell}"""


# Full path to config inside storage - use application-specific storage
def _get_glue_config_path():
    """Get the path to glue cell config using application-specific storage."""
    try:
        from backend.system.utils.ApplicationStorageResolver import get_app_settings_path
        return Path(get_app_settings_path("glue_dispensing_application", "glue_cell_config"))
    except ImportError:
        # Fallback to old path for backward compatibility
        return Path(PathResolver.get_settings_file_path('glue_cell_config.json'))

config_path = _get_glue_config_path()
# Global logger variable
ENABLE_LOGGING = False  # Enable or disable logging

# Initialize logger if enabled
if ENABLE_LOGGING:
    glue_cell_logger = logging.getLogger('glue_cell')
    glue_cell_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    for handler in glue_cell_logger.handlers[:]:
        glue_cell_logger.removeHandler(handler)
    
    # Create console handler with custom formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    # Custom format with function name and values
    formatter = ColoredFormatter(
        '[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    glue_cell_logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    glue_cell_logger.propagate = False
else:
    glue_cell_logger = None


def log_if_enabled(level, message):
    """Helper function to log only if logging is enabled"""
    if ENABLE_LOGGING and glue_cell_logger:
        # Get the calling function's name
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name
        
        # Convert LoggingLevel enum to string if necessary
        if isinstance(level, LoggingLevel):
            level_name = level.name.lower()
        else:
            level_name = level
        
        # Create a temporary log record with the caller's function name
        log_method = getattr(glue_cell_logger, level_name)
        
        # Temporarily modify the logger to show the actual caller
        original_findCaller = glue_cell_logger.findCaller
        def mock_findCaller(stack_info=False, stacklevel=1):
            # Return the caller's info instead of log_if_enabled
            return (caller_frame.f_code.co_filename, caller_frame.f_lineno, caller_name, None)
        
        glue_cell_logger.findCaller = mock_findCaller
        try:
            log_method(message)
        finally:
            # Restore original findCaller
            glue_cell_logger.findCaller = original_findCaller



class GlueType(Enum):
    TypeA = "Type A"
    TypeB = "Type B"
    TypeC = "Type C"
    TypeD = "Type D"

    def __str__(self):
        """
        Return the string representation of the glue type.

        Returns:
            str: The human-readable glue type value (e.g., "Type A").
        """
        return self.value


class GlueDataFetcher:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(GlueDataFetcher, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent reinitialization on subsequent instantiations
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.weight1 = 0
        self.weight2 = 0
        self.weight3 = 0

        # Load config to determine mode and URL
        try:
            with config_path.open("r") as f:
                config_data = json.load(f)

            mode = config_data.get("MODE", "production")
            if mode == "test":
                # Start mock server automatically in test mode
                self._start_mock_server()

                base_url = config_data.get("MOCK_SERVER_URL", "http://localhost:5000")
                self.url = f"{base_url}/weights"
                print(f"[GlueDataFetcher] Running in TEST mode - using {self.url}")
            else:
                base_url = config_data.get("PRODUCTION_SERVER_URL", "http://192.168.222.143")
                weights_endpoint = config_data.get("WEIGHTS_ENDPOINT", "/weights")
                self.url = f"{base_url}{weights_endpoint}"
                print(f"[GlueDataFetcher] Running in PRODUCTION mode - using {self.url}")
        except Exception as e:
            print(f"[GlueDataFetcher] Error loading config: {e}, defaulting to production mode")
            self.url = "http://192.168.222.143/weights"

        self.fetchTimeout = 5
        self._stop_thread = threading.Event()
        self.thread = None
        self._initialized = True
        self.broker = MessageBroker()

    def _start_mock_server(self):
        """Start the mock server in a background thread"""
        import subprocess
        import sys
        from pathlib import Path

        try:
            # Get the path to the mock server script
            project_root = Path(__file__).parent.parent.parent
            mock_server_path = project_root / "mock_glue_server.py"

            if not mock_server_path.exists():
                print(f"[GlueDataFetcher] Warning: Mock server script not found at {mock_server_path}")
                return

            # Check if server is already running
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('localhost', 5000))
                sock.close()
                if result == 0:
                    print(f"[GlueDataFetcher] Mock server already running on port 5000")
                    return
            except Exception:
                pass

            # Start the mock server in a background process
            print(f"[GlueDataFetcher] Starting mock server from {mock_server_path}")
            subprocess.Popen(
                [sys.executable, str(mock_server_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )

            # Wait a bit for the server to start
            time.sleep(2)
            print(f"[GlueDataFetcher] Mock server started successfully")

        except Exception as e:
            print(f"[GlueDataFetcher] Error starting mock server: {e}")

    def fetch(self):
        log_if_enabled(LoggingLevel.DEBUG, f"Fetching weights from {self.url}")
        try:
            response = requests.get(self.url, timeout=self.fetchTimeout)
            response.raise_for_status()
            weights = json.loads(response.text.strip())

            log_if_enabled(LoggingLevel.DEBUG, f"Raw weights received: {weights}")
            self.weight1 = float(weights.get("weight1", 0))
            self.weight2 = float(weights.get("weight2", 0))
            self.weight3 = float(weights.get("weight3", 0))

            log_if_enabled(LoggingLevel.INFO, f"WEIGHT DATA UPDATED:")
            log_if_enabled(LoggingLevel.INFO, f"  ├─ Weight 1: {self.weight1:.2f}g")
            log_if_enabled(LoggingLevel.INFO, f"  ├─ Weight 2: {self.weight2:.2f}g") 
            log_if_enabled(LoggingLevel.INFO, f"  └─ Weight 3: {self.weight3:.2f}g")

            self.broker.publish(GlueTopics.GLUE_METER_1_VALUE, self.weight1)
            self.broker.publish(GlueTopics.GLUE_METER_2_VALUE, self.weight2)
            self.broker.publish(GlueTopics.GLUE_METER_3_VALUE, self.weight3)
            log_if_enabled(LoggingLevel.DEBUG, "Published weights to message broker")
            
        except requests.exceptions.ConnectionError:
            log_if_enabled(LoggingLevel.ERROR, f"🔴 CONNECTION ERROR: Network unreachable or service down at {self.url}")
            log_if_enabled(LoggingLevel.WARNING, "Setting all weights to 0.0g due to connection failure")
            # Set weights to 0 when connection fails
            self.weight1 = self.weight2 = self.weight3 = 0.0
            
        except requests.exceptions.Timeout:
            log_if_enabled(LoggingLevel.WARNING, f"⏱️  TIMEOUT: Request to {self.url} took longer than {self.fetchTimeout}s")
            log_if_enabled(LoggingLevel.DEBUG, "Keeping previous weight values during timeout")
            # Keep previous values on timeout
            
        except requests.exceptions.HTTPError as e:
            log_if_enabled(LoggingLevel.ERROR, f"🔴 HTTP ERROR: {e.response.status_code} - {e.response.reason} from {self.url}")
            log_if_enabled(LoggingLevel.WARNING, "Setting all weights to 0.0g due to server error")
            # Set weights to 0 when server returns error
            self.weight1 = self.weight2 = self.weight3 = 0.0
            
        except json.JSONDecodeError:
            log_if_enabled(LoggingLevel.ERROR, f"🔴 JSON ERROR: Invalid response format from {self.url}")
            log_if_enabled(LoggingLevel.DEBUG, "Keeping previous weight values during parsing error")
            # Keep previous values on parsing error
            
        except ValueError as e:
            log_if_enabled(LoggingLevel.ERROR, f"🔴 VALUE ERROR: Unable to convert weight values to float - {e}")
            log_if_enabled(LoggingLevel.DEBUG, "Keeping previous weight values during conversion error")
            # Keep previous values on conversion error
            
        except Exception as e:
            log_if_enabled(LoggingLevel.ERROR, f"🔴 UNEXPECTED ERROR: {type(e).__name__}: {e} from {self.url}")
            log_if_enabled(LoggingLevel.DEBUG, "Keeping previous weight values during unexpected error")
            # Keep previous values on unexpected errors

    def _fetch_loop(self):
        while not self._stop_thread.is_set():
            self.fetch()
            time.sleep(0.1)

    def reload_config(self):
        """Reload configuration and restart the fetcher with new settings"""
        print("[GlueDataFetcher] Reloading configuration...")

        # Stop current thread
        was_running = self.thread is not None and self.thread.is_alive()
        if was_running:
            self.stop()

        # Reload config
        try:
            with config_path.open("r") as f:
                config_data = json.load(f)

            mode = config_data.get("MODE", "production")
            if mode == "test":
                # Start mock server automatically in test mode
                self._start_mock_server()

                base_url = config_data.get("MOCK_SERVER_URL", "http://localhost:5000")
                self.url = f"{base_url}/weights"
                print(f"[GlueDataFetcher] Switched to TEST mode - using {self.url}")
            else:
                base_url = config_data.get("PRODUCTION_SERVER_URL", "http://192.168.222.143")
                weights_endpoint = config_data.get("WEIGHTS_ENDPOINT", "/weights")
                self.url = f"{base_url}{weights_endpoint}"
                print(f"[GlueDataFetcher] Switched to PRODUCTION mode - using {self.url}")
        except Exception as e:
            print(f"[GlueDataFetcher] Error reloading config: {e}, keeping current settings")

        # Restart if it was running
        if was_running:
            self.start()

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self._stop_thread.clear()
            self.thread = threading.Thread(target=self._fetch_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self._stop_thread.set()
        if self.thread is not None:
            self.thread.join()



class GlueCell:
    """
    Represents a glue cell in the dispensing application.

    Attributes:
        id (int): The unique identifier for the glue cell.
        glueType (GlueType): The type of glue used in the cell.
        glueMeter (GlueMeter): The glue meter associated with the cell for measuring glue weight.
        capacity (int): The maximum capacity of the glue cell.

    Methods:
        setId(id): Sets the unique identifier for the glue cell.
        setGlueType(glueType): Sets the type of glue used in the cell.
        setGlueMeter(glueMeter): Sets the glue meter for the cell.
        setCapacity(capacity): Sets the maximum capacity of the glue cell.
        getGlueInfo(): Retrieves the current glue weight and percentage of capacity used.
    """

    def __init__(self, id, glueType, glueMeter, capacity):
        """
        Initializes a GlueCell instance.

        Args:
            id (int): The unique identifier for the glue cell.
            glueType (GlueType): The type of glue used in the cell.
            glueMeter (GlueMeter): The glue meter associated with the cell.
            capacity (int): The maximum capacity of the glue cell.

        Raises:
            TypeError: If glueType is not an instance of GlueType or glueMeter is not an instance of GlueMeter.
            ValueError: If capacity is less than or equal to 0.
        """
        self.logTag = "GlueCell"
        self.setId(id)
        self.setGlueType(glueType)
        self.setGlueMeter(glueMeter)
        self.setCapacity(capacity)

    def setId(self, id):
        """
        Sets the unique identifier for the glue cell.

        Args:
            id (int): The unique identifier for the glue cell.
        """
        self.id = id

    def setGlueType(self, glueType):
        """
        Sets the type of glue used in the cell.

        Args:
            glueType (GlueType): The type of glue used in the cell.

        Raises:
            TypeError: If glueType is not an instance of GlueType.
        """
        if not isinstance(glueType, GlueType):
            raise TypeError(f"[DEBUG] [{self.logTag}] glueType must be an instance of GlueType class, got {type(glueType)}")
        self.glueType = glueType

    def setGlueMeter(self, glueMeter):
        """
        Sets the glue meter for the cell.

        Args:
            glueMeter (GlueMeter): The glue meter associated with the cell.

        Raises:
            TypeError: If glueMeter is not an instance of GlueMeter.
        """

        if not isinstance(glueMeter, GlueMeter):
            raise TypeError(f"[DEBUG] [{self.logTag}] glueMeter must be an instance of GlueMeter class, got {type(glueMeter)}")
        self.glueMeter = glueMeter

    def setCapacity(self, capacity):
        """
        Sets the maximum capacity of the glue cell.

        Args:
            capacity (int): The maximum capacity of the glue cell.

        Raises:
            ValueError: If capacity is less than or equal to 0.
        """
        if capacity <= 0:
            raise ValueError(f"DEbug] [{self.logTag}] capacity must be greater than 0, got {capacity}")
        self.capacity = capacity

    def getGlueInfo(self):
        """
        Retrieves the current glue weight and percentage of capacity used.

        Returns:
            list: A list containing the current glue weight and percentage of capacity used.
        """
        weight = self.glueMeter.fetchData()
        if weight < 0:
            weight = 0
        percent = int((weight / self.capacity) * 100)
        return [weight, percent]

    def __str__(self):
        """
        Returns a string representation of the GlueCell instance.

        Returns:
            str: A string representation of the GlueCell instance.
        """
        return f"GlueCell(id={self.id}, glueType={self.glueType}, glueMeter={self.glueMeter}, capacity={self.capacity})"



class GlueMeter(Sensor):
    """
    Represents a glue meter used to measure the weight of glue in a container.

    Attributes:
        url (str): The URL endpoint for fetching glue weight data.
        fetchTimeout (int): The timeout duration (in seconds) for HTTP requests.

    Methods:
        __init__(url, fetchTimeout=2):
            Initializes a GlueMeter instance with the specified URL and timeout.
        setFetchTimeut(timeout):
            Sets the timeout duration for HTTP requests.
        setUrl(url):
            Sets the URL endpoint for fetching glue weight data.
        fetchData():
            Fetches the current glue weight from the URL and calculates the net weight.
        __str__():
            Returns a string representation of the GlueMeter instance.
    """

    def __init__(self,id, url, fetchTimeout=10, useLowPass=False, alpha=0.3):
        self.id = id
        self.name = f"GlueMeter_{self.id}"
        self.state = "Initializing"
        self.setFetchTimeut(fetchTimeout)
        self.setUrl(url)
        self.smoothedValue = None
        self.pollTime = 0.5
        self.type = "http"
        self.useLowPass = useLowPass
        self.alpha = alpha  # Smoothing factor for low-pass filter
        self.lastValue = None  # Last smoothed value for low-pass
        self.fetcher = GlueDataFetcher()


    def setFetchTimeut(self, timeout):
        """
        Sets the timeout duration for HTTP requests.

        Args:
            timeout (int): The timeout duration (in seconds).

        Raises:
            ValueError: If timeout is less than or equal to 0.
        """
        if timeout <= 0:
            raise ValueError(f"[DEBUG] [{self.name}] fetchTimeout must be greater than 0, got {timeout}")
        self.fetchTimeout = timeout

    def setUrl(self, url):
        """
        Sets the URL endpoint for fetching glue weight data.

        Args:
            url (str): The URL endpoint.
        """
        self.url = url

    def fetchData(self):
        weight = 0
        try:
            if self.id == 1:
                weight = self.fetcher.weight1

            if self.id == 2:
                weight = self.fetcher.weight2

            if self.id == 3:
                weight = self.fetcher.weight3

            self.state = "READY"
            self.lastValue = weight
            return  weight


        except requests.exceptions.Timeout:
            self.state = "DISCONNECTED"
            log_if_enabled(LoggingLevel.WARNING, f"[{self.name}] Connection timeout")
            return None

        except requests.exceptions.RequestException as e:
            self.state = "ERROR"
            log_if_enabled(LoggingLevel.ERROR, f"[{self.name}] Request error: {e}")
            return None

    def __str__(self):
        """
        Returns a string representation of the GlueMeter instance.

        Returns:
            str: A string representation of the GlueMeter instance.
        """
        return f"GlueMeter(url={self.url})"

    ### SENSOR INTERFACE METHODS IMPLEMENTATION

    def getState(self):
        return self.state


    def getValue(self):
        return self.lastValue


    def getName(self):
        return self.name

    def testConnection(self):
        # Not needed, as fetchData determines state
        self.fetchData()

    def reconnect(self):
        # Not needed, as fetchData attempts fresh HTTP request each time
        pass


class GlueCellsManager:
    """
    Manages multiple glue cells in the dispensing application.

    Attributes:
        cells (list): A list of GlueCell instances.

    Methods:
        setCells(cells): Sets the list of glue cells.
        getCellById(id): Retrieves a glue cell by its unique identifier.
    """

    def __init__(self, cells, config_data, config_path):
        """
        Initializes a GlueCellsManager instance.

        Args:
            cells (list): A list of GlueCell instances.

        Raises:
            TypeError: If any item in the cells list is not an instance of GlueCell.
        """
        self.logTag = "GlueCellsManager"
        self.setCells(cells)
        self.config_path = config_path
        self.config_data = config_data  # keep a copy of the loaded JSON


    def updateGlueTypeById(self, id, glueType):
        """
        Updates the glue type of a specific glue cell by its unique identifier
        and persists the change to the config file.
        """
        # Normalize string to enum
        if glueType == GlueType.TypeA.value:
            glueType = GlueType.TypeA
        elif glueType == GlueType.TypeB.value:
            glueType = GlueType.TypeB
        elif glueType == GlueType.TypeC.value:
            glueType = GlueType.TypeC
        elif glueType == GlueType.TypeD.value:
            glueType = GlueType.TypeD
        elif isinstance(glueType, GlueType):
            pass
        else:
            raise ValueError(f"[DEBUG] {self.logTag} Invalid glue type: {glueType}")

        log_if_enabled(LoggingLevel.INFO, f"🔄 UPDATING GLUE TYPE: Cell {id} → {glueType}")
        # Update in-memory object
        cell = self.getCellById(id)
        if cell is None:
            log_if_enabled(LoggingLevel.ERROR, f"❌ CELL NOT FOUND: Cell {id} does not exist")
            return False

        log_if_enabled(LoggingLevel.DEBUG, f"Setting cell {id} glue type from {cell.glueType} to {glueType}")
        cell.setGlueType(glueType)

        # Update JSON data
        for c in self.config_data["CELL_CONFIG"]:
            if c["id"] == id:
                c["type"] = glueType.name  # store enum name like "TypeA"
                break

        # Persist to file
        with self.config_path.open("w") as f:
            json.dump(self.config_data, f, indent=2)

        return True


    def setCells(self, cells):
        """
        Sets the list of glue cells.

        Args:
            cells (list): A list of GlueCell instances.

        Raises:
            TypeError: If any item in the cells list is not an instance of GlueCell.
        """
        if not all(isinstance(cell, GlueCell) for cell in cells):
            raise TypeError(f"[DEBUG] {self.logTag} All items in the cells list must be instances of GlueCell")
        self.cells = cells

    def getCellById(self, id):
        """
        Retrieves a glue cell by its unique identifier.

        Args:
            id (int): The unique identifier of the glue cell.

        Returns:
            GlueCell: The glue cell with the specified identifier, or None if not found.
        """
        for cell in self.cells:
            if cell.id == id:
                return cell
        return None

    def pollGlueDataById(self,id):
        weight, percent = self.getCellById(id).getGlueInfo()
        return weight, percent

    def __str__(self):
        """
        Returns a string representation of the GlueCellsManager instance.

        Returns:
            str: A string representation of the GlueCellsManager instance.
        """
        return f"CellsManager(cells={self.cells})"

class GlueCellsManagerSingleton:
    _manager_instance = None

    # Use application-specific storage for glue cell config
    @classmethod
    def _get_config_path(cls):
        """Get the path to glue cell config using application-specific storage."""
        try:
            from backend.system.utils.ApplicationStorageResolver import get_app_settings_path
            return Path(get_app_settings_path("glue_dispensing_application", "glue_cell_config"))
        except ImportError:
            # Fallback to old path for backward compatibility
            return Path(PathResolver.get_settings_file_path('glue_cell_config.json'))
    
    CONFIG_PATH = None  # Will be set in get_instance()
    @staticmethod
    def get_instance():
        if GlueCellsManagerSingleton._manager_instance is None:
            # Set CONFIG_PATH if not already set
            if GlueCellsManagerSingleton.CONFIG_PATH is None:
                GlueCellsManagerSingleton.CONFIG_PATH = GlueCellsManagerSingleton._get_config_path()
            
            # Load config JSON inside the manager
            with GlueCellsManagerSingleton.CONFIG_PATH.open("r") as f:
                config_data = json.load(f)

            type_map = {
                "TypeA": GlueType.TypeA,
                "TypeB": GlueType.TypeB,
                "TypeC": GlueType.TypeC,
                "TypeD": GlueType.TypeD
            }

            # Determine the base URL based on MODE
            mode = config_data.get("MODE", "production")
            if mode == "test":
                base_url = config_data.get("MOCK_SERVER_URL", "http://localhost:5000")
                print(f"[GlueCellsManager] Running in TEST mode - using mock server: {base_url}")
            else:
                base_url = config_data.get("PRODUCTION_SERVER_URL", "http://192.168.222.143")
                print(f"[GlueCellsManager] Running in PRODUCTION mode - using server: {base_url}")

            cells = []
            for cell_cfg in config_data["CELL_CONFIG"]:
                glue_type = type_map.get(cell_cfg["type"])
                if glue_type is None:
                    raise ValueError(f"Unknown glue type in config: {cell_cfg['type']}")

                # Override URL based on mode
                if mode == "test":
                    url = f"{base_url}/weight{cell_cfg['id']}"
                else:
                    url = cell_cfg["url"]

                print(f"[GlueCellsManager] Cell {cell_cfg['id']}: {url}")

                glue_meter = GlueMeter(cell_cfg["id"], url)
                glue_cell = GlueCell(
                    id=cell_cfg["id"],
                    glueType=glue_type,
                    glueMeter=glue_meter,
                    capacity=cell_cfg["capacity"]
                )
                cells.append(glue_cell)

            # ✅ Pass config_data and CONFIG_PATH into manager
            GlueCellsManagerSingleton._manager_instance = GlueCellsManager(
                cells, config_data, GlueCellsManagerSingleton.CONFIG_PATH
            )

        return GlueCellsManagerSingleton._manager_instance





"""     EXAMPLE USAGE   """
if __name__ == "__main__":
    # try:
    #     print("Meter 1: ",GlueCellsManagerSingleton.get_instance().pollGlueDataById(1))
    #     # print("Meter 2: ",GlueCellsManagerSingleton.get_instance().pollGlueDataById(2))
    #     # print("Meter 3: ",GlueCellsManagerSingleton.get_instance().pollGlueDataById(3))
    # except Exception as e:
    #     print(f"Error: {e}")

    fetcher= GlueDataFetcher()
    fetcher.start()
    import time
    while True:
        time.sleep(1)  # Add a delay to allow the fetcher thread to run
        print("running")

