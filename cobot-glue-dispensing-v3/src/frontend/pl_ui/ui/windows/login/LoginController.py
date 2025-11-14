from typing import Any, Tuple

from frontend.pl_ui.localization import TranslationKeys, TranslatableObject
from frontend.pl_ui.Endpoints import START_CONTOUR_DETECTION


class LoginController(TranslatableObject):
    def __init__(self, controller: Any) -> None:
        super().__init__()
        self.controller: Any = controller

    def handle_login(self, username: str, password: str) -> Tuple[bool, str]:
        """Handle login process for both tabs"""
        print("User", username)
        print("pass", password)

        message: str = ""
        if not username or not password:  # Check if either is None or empty
            message = self.tr(TranslationKeys.Auth.ENTER_ID_AND_PASSWORD)
            return False, message

        if not username.isdigit():  # Check if username is a number
            message = self.tr(TranslationKeys.Auth.INVALID_LOGIN_ID)
            return False, message

        message = self.controller.handleLogin(username, password)
        print("Login response:", message)
        print("Controller message:", message)

        if message == "1":
            self.controller.handle(START_CONTOUR_DETECTION)
            return True, ""
        elif message == "0":
            print("INCORRECT_PASSWORD")
            message = self.tr(TranslationKeys.Auth.INCORRECT_PASSWORD)
            return False, message
        elif message == "-1":
            print("USER_NOT_FOUND")
            message = self.tr(TranslationKeys.Auth.USER_NOT_FOUND)
            return False, message

        return False, "Unexpected response"
