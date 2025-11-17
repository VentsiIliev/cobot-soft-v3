from dataclasses import dataclass, field
from datetime import datetime
from modules.shared.core.user.User import User
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), "../../../storage/logs/session.txt")

@dataclass
class Session:
    user: User
    login_time: datetime = field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.user.firstName} ({self.user.role.value}) logged in at {self.login_time.strftime('%Y-%m-%d %H:%M:%S')}"

class SessionManager:
    _current_session: Session = None

    @classmethod
    def login(cls, user: User):
        cls._current_session = Session(user=user)
        log_entry = f"[LOGIN] {cls._current_session}\n"
        print(log_entry.strip())
        cls._log_to_file(log_entry)

    @classmethod
    def logout(cls):
        if cls._current_session:
            logout_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = (f"[LOGOUT] {cls._current_session.user.firstName} "
                         f"({cls._current_session.user.role.value}) logged out at {logout_time}\n")
            print(log_entry.strip())
            cls._log_to_file(log_entry)
        cls._current_session = None

    @classmethod
    def get_current_user(cls) -> User:
        return cls._current_session.user if cls._current_session else None

    @classmethod
    def is_logged_in(cls) -> bool:
        return cls._current_session is not None

    @staticmethod
    def _log_to_file(entry: str):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(entry)
