"""
Authentication Handler - API Gateway

Handles all authentication-related requests including login, logout, and session management.
"""

from modules.shared.v1.Response import Response
from modules.shared.v1 import Constants
from modules.shared.v1.endpoints import auth_endpoints
import os


class AuthHandler:
    """
    Handles authentication operations for the API gateway.
    
    This handler manages user login, QR code authentication, and session management.
    """
    
    def __init__(self):
        """Initialize the AuthHandler."""
        pass
    
    def handle(self, request, data=None):
        """
        Route authentication requests to appropriate handlers.
        
        Args:
            request (str): The authentication request type
            data: Request data (username/password for login)
            
        Returns:
            dict: Response dictionary with authentication result
        """
        print(f"AuthHandler: Handling request: {request}")
        
        # Handle both new RESTful endpoints and legacy endpoints
        if request in [auth_endpoints.LOGIN, auth_endpoints.LEGACY_LOGIN]:
            return self.handle_login(data)
        elif request in [auth_endpoints.QR_LOGIN, auth_endpoints.LEGACY_QR_LOGIN]:
            return self.handle_qr_login(data)
        else:
            raise ValueError(f"Unknown request: {request}")
            return Response(Constants.RESPONSE_STATUS_ERROR, 
                          message=f"Unknown authentication request: {request}").to_dict()
    
    def handle_login(self, data):
        """
        Handle standard username/password login.
        
        Args:
            data (list): [username, password]
            
        Returns:
            dict: Response with login result
        """
        print("AuthHandler: Handling login")
        
        if not data or len(data) < 2:
            return Response(Constants.RESPONSE_STATUS_ERROR, 
                          message="Username and password required").to_dict()
        
        user_id = data[0]
        password = data[1]
        
        print(f"AuthHandler: Login attempt for user ID: {user_id} (type: {type(user_id)})")
        
        try:
            # Import authentication dependencies
            from modules.shared.shared.user.User import User, Role, UserField
            from modules.shared.shared.user.CSVUsersRepository import CSVUsersRepository
            from modules.shared.shared.user.UserService import UserService
            
            # Set up user repository
            csv_file_path = os.path.join(os.path.dirname(__file__), "../../shared/shared/user/users.csv")
            user_fields = [UserField.ID, UserField.FIRST_NAME, UserField.LAST_NAME, UserField.PASSWORD, UserField.ROLE]
            
            print(f"AuthHandler: User fields: {user_fields}")
            
            repository = CSVUsersRepository(csv_file_path, user_fields, User)
            service = UserService(repository)
            
            # Authenticate user
            user = service.getUserById(user_id)
            print(f"AuthHandler: Found user: {user}")
            
            if user:
                if user.password == password:  # TODO: Replace with hashed comparison in production
                    print(f"AuthHandler: Login successful! Welcome, {user.firstName} ({user.role.value})")
                    
                    # Start user session
                    from modules.shared.shared.user.Session import SessionManager
                    SessionManager.login(user)
                    
                    response = Response(Constants.RESPONSE_STATUS_SUCCESS, "1")
                else:
                    print("AuthHandler: Incorrect password")
                    response = Response(Constants.RESPONSE_STATUS_SUCCESS, "0")
            else:
                print("AuthHandler: User not found")
                response = Response(Constants.RESPONSE_STATUS_SUCCESS, "-1")
                
            return response.to_dict()
            
        except Exception as e:
            print(f"AuthHandler: Login error: {e}")
            import traceback
            traceback.print_exc()
            return Response(Constants.RESPONSE_STATUS_ERROR, 
                          message=f"Login error: {str(e)}").to_dict()
    
    def handle_qr_login(self, data=None):
        """
        Handle QR code-based login.
        
        Args:
            data: QR code data (if any)
            
        Returns:
            dict: Response with QR login result
        """
        print("AuthHandler: Handling QR login")
        
        # TODO: Implement QR code authentication logic
        # This is a placeholder implementation
        
        try:
            # For now, return success - actual QR implementation would go here
            response = Response(Constants.RESPONSE_STATUS_SUCCESS, 
                              message="QR login not yet implemented")
            return response.to_dict()
            
        except Exception as e:
            print(f"AuthHandler: QR login error: {e}")
            return Response(Constants.RESPONSE_STATUS_ERROR, 
                          message=f"QR login error: {str(e)}").to_dict()
    
    def handle_logout(self, data=None):
        """
        Handle user logout.
        
        Args:
            data: Logout data (if any)
            
        Returns:
            dict: Response with logout result
        """
        print("AuthHandler: Handling logout")
        
        try:
            from modules.shared.shared.user.Session import SessionManager
            SessionManager.logout()
            
            response = Response(Constants.RESPONSE_STATUS_SUCCESS, 
                              message="Logged out successfully")
            return response.to_dict()
            
        except Exception as e:
            print(f"AuthHandler: Logout error: {e}")
            return Response(Constants.RESPONSE_STATUS_ERROR, 
                          message=f"Logout error: {str(e)}").to_dict()