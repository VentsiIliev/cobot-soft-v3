import logging
from enum import Enum
from modules.shared.MessageBroker import MessageBroker
import functools
import inspect
import datetime

class LoggingLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels and milliseconds support"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[92m',  # Bright Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[95m',  # Magenta
        'RESET': '\033[0m'  # Reset
    }

    def format(self, record):
        # Add color to the log level
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']

        # Format: [TIMESTAMP] [LEVEL] [FUNCTION] MESSAGE
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        record.funcName = f"{log_color}{record.funcName}{reset_color}"

        return super().format(record)

    def formatTime(self, record, datefmt=None):
        """Override to add milliseconds support"""
        import datetime
        ct = datetime.datetime.fromtimestamp(record.created)
        if datefmt:
            # Custom handling for milliseconds
            if '%f' in datefmt:
                # Replace %f with milliseconds (3 digits)
                milliseconds = ct.strftime('%f')[:-3]
                datefmt_with_ms = datefmt.replace('%f', milliseconds)
                s = ct.strftime(datefmt_with_ms)
            else:
                s = ct.strftime(datefmt)
        else:
            s = ct.strftime('%H:%M:%S.') + ct.strftime('%f')[:-3]
        return s

class LoggerContext:
    def __init__(self,enabled:bool,logger:logging.Logger,broadcast_to_ui:bool=False,topic="log"):
        self.enabled=enabled
        self.logger=logger
        self.broadcast_to_ui = broadcast_to_ui
        self.topic = topic

def log_warning_message(logger_context:LoggerContext, message:str):
    log_if_enabled(enabled=logger_context.enabled,
                   logger=logger_context.logger,
                   message=message,
                   level=LoggingLevel.WARNING,
                   broadcast_to_ui=logger_context.broadcast_to_ui,
                   topic=logger_context.topic)

def log_info_message(logger_context:LoggerContext, message:str):
    log_if_enabled(enabled=logger_context.enabled,
                   logger=logger_context.logger,
                   message=message,
                   level=LoggingLevel.INFO,
                   broadcast_to_ui=logger_context.broadcast_to_ui,
                   topic=logger_context.topic)

def log_debug_message(logger_context:LoggerContext, message:str):
    log_if_enabled(enabled=logger_context.enabled,
                   logger=logger_context.logger,
                   message=message,
                   level=LoggingLevel.DEBUG,
                   broadcast_to_ui=logger_context.broadcast_to_ui,
                   topic=logger_context.topic)

def log_error_message(logger_context:LoggerContext, message:str):
    log_if_enabled(enabled=logger_context.enabled,
                   logger=logger_context.logger,
                   message=message,
                   level=LoggingLevel.ERROR,
                   broadcast_to_ui=logger_context.broadcast_to_ui,
                   topic=logger_context.topic)

def setup_logger(name:str):
    """Setup a specialized logger for RobotWrapper operations"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler with custom formatter
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Custom format with function name and values
    formatter = ColoredFormatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s',
        datefmt='%H:%M:%S.%f'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to avoid duplicate messages
    logger.propagate = False

    return logger

def log_if_enabled(enabled, logger, level, message, broadcast_to_ui=False, topic="log"):
    """Helper function to log only if logging is enabled"""
    if enabled and logger:

        if broadcast_to_ui:
            broker = MessageBroker()
            broker.publish(topic, message)

        import inspect
        # Get the calling function's name
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name

        # Convert LoggingLevel enum to string if necessary
        if isinstance(level, LoggingLevel):
            level_name = level.name.lower()
        elif isinstance(level, str):
            level_name = level.lower()
        else:
            # Fallback to info if level is invalid
            level_name = 'info'

        # Create a temporary log record with the caller's function name
        log_method = getattr(logger, level_name)

        # Temporarily modify the logger to show the actual caller
        original_findCaller = logger.findCaller

        def mock_findCaller(stack_info=False, stacklevel=1):
            # Return the caller's info instead of log_if_enabled
            return (caller_frame.f_code.co_filename, caller_frame.f_lineno, caller_name, None)

        logger.findCaller = mock_findCaller
        try:
            log_method(message)
        finally:
            # Restore original findCaller
            logger.findCaller = original_findCaller





def log_calls_with_timestamp_decorator(logger=None, enabled=True):
    """
    Decorator to log method/function calls with timestamp, function name, and parameters.

    Args:
        logger: Logger instance (must have .info/.debug/.error methods). If None, prints to console.
        enabled: Toggle logging on/off.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if enabled:
                # Timestamp
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                # Get function arguments
                bound_args = inspect.signature(func).bind(*args, **kwargs)
                bound_args.apply_defaults()
                args_repr = ", ".join(f"{k}={v!r}" for k, v in bound_args.arguments.items())

                # Log message
                message = f"[{timestamp}] CALL {func.__qualname__}({args_repr})"

                if logger:
                    if hasattr(logger, "debug"):
                        logger.debug(message)
                    else:
                        logger.info(message)
                else:
                    print(message)

            return func(*args, **kwargs)

        return wrapper

    return decorator
