from enum import Enum
from abc import ABC, abstractmethod


class Role(Enum):
    ADMIN = "Admin"
    OPERATOR = "Operator"
    SERVICE = "Service"


class UserField(Enum):
    ID = "id"
    FIRST_NAME = "firstName"
    LAST_NAME = "lastName"
    PASSWORD = "password"
    ROLE = "role"
    EMAIL = "email"


# Abstract class to ensure all users have an 'id' field
class AbstractUser(ABC):
    def __init__(self, id):
        """
        Enforces that all subclasses must have an 'id' field.
        """
        if not id:
            raise ValueError("ID must be provided")
        self.id = id

    @abstractmethod
    def __eq__(self, other):
        pass


class BaseUser(AbstractUser):
    def __init__(self, id):
        super().__init__(id)

    def __eq__(self, other):
        return self.id == other.id


# Subclass User must call super().__init__(id) to ensure 'id' is set
class User(BaseUser):
    def __init__(self, id, firstName, lastName, password, role,email=None):
        # Enforce 'id' by calling the AbstractUser's constructor
        super().__init__(id)
        self.firstName = firstName
        assert isinstance(lastName, object)
        self.lastName = lastName
        self.password = password  # TODO: Hash password before storing
        self.role = role
        self.email = email

    def __str__(self):
        return f"ID: {self.id} {self.firstName} {self.lastName} {self.email} ({self.role})"

    def __eq__(self, other):
        return self.id == other.id

    def get_full_name(self):
        return f"{self.firstName} {self.lastName}"


# NewUser class also inherits from AbstractUser, so 'id' must be passed and enforced
class NewUser(BaseUser):
    def __init__(self, id, firstName):
        # Enforce 'id' by calling the AbstractUser's constructor
        super().__init__(id)
        self.firstName = firstName
        # self.lastName = lastName
        # self.password = password
        # self.role = role

    # def __str__(self):
    #     return f"ID: {self.id} {self.firstName} {self.lastName} ({self.role})"

    def __eq__(self, other):
        return self.id == other.id


if __name__ == "__main__":
    from modules.shared.core.user.User import User, Role, UserField
    from UserService import UserService
    from CSVUsersRepository import CSVUsersRepository

    # Setup
    csv_file_path = "users.csv"
    user_fields = [UserField.ID, UserField.FIRST_NAME, UserField.LAST_NAME, UserField.PASSWORD, UserField.ROLE]
    repository = CSVUsersRepository(csv_file_path, user_fields, User)
    service = UserService(repository)

    # # Optional: Add a user for testing
    # new_user = User(
    #     id=2,  # Use string if CSV stores ID as string
    #     firstName="Admin",
    #     lastName="Admin",
    #     password="pass",  # TODO: hash in production
    #     role=Role.ADMIN
    # )
    #
    # try:
    #     added = service.addUser(new_user)
    #     if added:
    #         print("User added successfully.")
    #     else:
    #         print("User already exists.")
    # except Exception as e:
    #     print(f"Error adding user: {e}")

    # --- Simulate login ---
    print("\n=== LOGIN ===")
    user_id = input("Enter user ID: ").strip()
    password_input = input("Enter password: ").strip()

    user = service.getUserById(user_id)

    if user:
        if user.password == password_input:  # Replace with hashed comparison in real use
            print(f"Login successful! Welcome, {user.firstName} ({user.role.value})")
        else:
            print("Incorrect password.")
    else:
        print("User not found.")
