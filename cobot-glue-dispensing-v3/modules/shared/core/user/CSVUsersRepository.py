from modules.shared.core.user.User import UserField
from modules.shared.core.user.User import Role
from modules.shared.core.database.repositories.csvRepository.BaseCSVRepository import BaseCSVRepository
from modules.shared.core.user.User import AbstractUser
import traceback


class CSVUsersRepository(BaseCSVRepository):
    def __init__(self, filepath, userFields, user_class):
        """
        Initialize CSV repository with dynamic user fields and user class type.
        :param filepath: Path to the CSV file
        :param userFields: List of fields (from UserField enum)
        :param user_class: The user class to use for creating users
        """

        if not issubclass(user_class, AbstractUser):
            raise ValueError("The user_class must be a subclass of AbstractUser")

        self.userFields = {}
        for field in userFields:
            self.userFields[field.name] = field.value

        # Store the user class type for later use
        self.user_class = user_class

        # Ensure column names passed to the base class are the enum names (upper case)
        super().__init__(filepath, list(self.userFields.keys()))  # Use enum names (uppercase names)

    def get_all(self):
        users = []
        df = self.get_data()

        if df.empty:
            return users

        for _, row in df.iterrows():
            user_data = {self.userFields[key]: row[key] for key in self.userFields}

            # Fix: Convert role string back to Role Enum
            if 'role' in user_data and isinstance(user_data['role'], str):
                if user_data['role'].startswith("Role."):
                    role_str = user_data['role'].split(".")[1]
                    user_data['role'] = Role[role_str]
                else:
                    user_data['role'] = Role(user_data['role'])

            # Fix: Ensure ID is correct type
            user_data['id'] = int(float(user_data['id']))

            users.append(self.user_class(**user_data))
        print("Fetching all users from CSV repository...",len(users))

        return users

    def get(self, user_id):
        df = self.get_data()
        print(f"Columns in CSV: {df.columns}")

        id_column = self.userFields[UserField.ID.name].upper()
        print(f"ID column: {id_column}")

        row = df[df[id_column].astype(str) == str(user_id)]

        if not row.empty:
            row = row.iloc[0]
            user_data = {self.userFields[key]: row[key] for key in self.userFields}
            print(f"User data: {user_data}")

            # Fix: Convert role string to Role Enum
            if 'role' in user_data and isinstance(user_data['role'], str):
                if user_data['role'].startswith("Role."):
                    role_str = user_data['role'].split(".")[1]
                    user_data['role'] = Role[role_str]
                else:
                    user_data['role'] = Role(user_data['role'])

            # Fix: Ensure ID is correct type
            user_data['id'] = int(float(user_data['id']))

            return self.user_class(**user_data)
        else:
            print("row empty")

        return None

    def insert(self, user):
        print(f"Inserting user: {user}")
        try:
            if self.get(user.id) is None:
                # Dynamically map user data using the userFields mapping
                user_data = {
                    key: getattr(user, self.userFields[key]).value if key == "ROLE"
                    else getattr(user, self.userFields[key])
                    for key in self.userFields
                }

                # Ensure that all fields are in the userData dictionary
                print(f"User data to insert: {user_data}")  # Debugging

                # Ensure that all required fields are in the CSV file
                for field in self.userFields:
                    if field not in user_data:
                        raise ValueError(f"Missing required field: {field}")

                # Map back to the enum names
                user_data = {field: user_data[field] for field in self.userFields}
                print(f"User data to insert after mapping: {user_data}")  # Debugging

                super().insert(**user_data)
                return True
            else:
                print(f"User {user.id} already exists.")
                return False
        except Exception as e:
            print(f"Error inserting user: {e}")
            traceback.print_exc()
            return False

    def delete(self, user_id):
        super().delete(user_id)

    def update(self, updated_users):
        df = self._read_rows()
        id_column = UserField.ID.name  # 'ID' column in CSV
        print(df)
        print("id_column", id_column)

        # Prepare updated rows to pass to base class
        update_rows = []

        for updated_user in updated_users:
            update_row = {}
            for field_enum in UserField:
                column_name = field_enum.name  # 'ID', 'FIRST_NAME', etc.
                attribute_name = field_enum.value  # 'id', 'firstName', etc.
                update_row[column_name] = getattr(updated_user, attribute_name)
            update_rows.append(update_row)

        print(f"Updating users: {[user.id for user in updated_users]}")
        super().update(update_rows)

    def get_data(self, filters=None):
        """Retrieve filtered data based on given criteria."""
        return super().get_data(filters)