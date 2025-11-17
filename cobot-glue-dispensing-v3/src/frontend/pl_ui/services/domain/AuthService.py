"""
Authentication Domain Service

Handles all authentication-related operations with explicit return values.
No callbacks - just clean, clear method calls!
"""

import logging
from typing import TYPE_CHECKING, Dict, Any

from ..types.ServiceResult import ServiceResult

# Import endpoint constants
from modules.shared.v1.endpoints import auth_endpoints

if TYPE_CHECKING:
    from frontend.pl_ui.controller.Controller import Controller


class AuthService:
    """
    Domain service for all authentication operations.
    
    Provides explicit, type-safe methods for authentication.
    All methods return ServiceResult - no callbacks needed!
    
    Usage:
        result = auth_service.login("user", "password")
        if result:
            print(f"Login successful: {result.message}")
        else:
            print(f"Login failed: {result.message}")
    """
    
    def __init__(self, controller: 'Controller', logger: logging.Logger):
        """
        Initialize the authentication service.
        
        Args:
            controller: The main controller instance
            logger: Logger for this service
        """
        self.controller = controller
        self.logger = logger.getChild(self.__class__.__name__)
    
    def login(self, username: str, password: str) -> ServiceResult:
        """
        Authenticate user with username and password.
        
        Args:
            username: The username for authentication
            password: The password for authentication
        
        Returns:
            ServiceResult with login success/failure and message
        """
        try:
            # Validate inputs
            if not username or username.strip() == "":
                return ServiceResult.error_result("Username cannot be empty")
            
            if not password or password.strip() == "":
                return ServiceResult.error_result("Password cannot be empty")
            
            self.logger.info(f"Attempting login for user: {username}")
            
            # Call the controller
            message = self.controller.handleLogin(username, password)
            
            # Assume successful login if no exception and message doesn't contain "error" or "failed"
            if message and not any(word in message.lower() for word in ["error", "failed", "invalid", "incorrect"]):
                return ServiceResult.success_result(
                    f"Login successful: {message}",
                    data={"username": username, "message": message}
                )
            else:
                return ServiceResult.error_result(f"Login failed: {message}")
                
        except Exception as e:
            error_msg = f"Login failed for user {username}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)
    
    def qr_login(self) -> ServiceResult:
        """
        Initiate QR code login process.
        
        Returns:
            ServiceResult with QR login data or error message
        """
        try:
            self.logger.info("Initiating QR code login")
            
            response = self.controller.handleQrLogin()
            
            if response:
                return ServiceResult.success_result(
                    "QR login initiated successfully",
                    data=response
                )
            else:
                return ServiceResult.error_result("Failed to initiate QR login")
                
        except Exception as e:
            error_msg = f"QR login failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return ServiceResult.error_result(error_msg)