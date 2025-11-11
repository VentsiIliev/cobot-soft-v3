import json
from API.shared.user.User import Role
from deprecated.pl_gui.settings.Paths import ROLE_VISIBILITY_JSON_PATH
CONFIG_FILE = ROLE_VISIBILITY_JSON_PATH


class UserPermissionManager:
    _permissions = None  # Cache

    @staticmethod
    def _load_permissions():
        if UserPermissionManager._permissions is None:
            try:
                with open(CONFIG_FILE, "r") as f:
                    UserPermissionManager._permissions = json.load(f)
            except FileNotFoundError:
                print("⚠️ role_visibility.json not found. ",ROLE_VISIBILITY_JSON_PATH)
                UserPermissionManager._permissions = {}
            except json.JSONDecodeError as e:
                print("⚠️ Error parsing role_visibility.json:", e)
                UserPermissionManager._permissions = {}

        return UserPermissionManager._permissions

    @staticmethod
    def get_visible_buttons(role: Role) -> list[str]:
        permissions = UserPermissionManager._load_permissions()
        return permissions.get(role.name, [])

    @staticmethod
    def is_button_visible(role: Role, button_name: str) -> bool:
        return button_name in UserPermissionManager.get_visible_buttons(role)

    @staticmethod
    def get_permissions() -> list[str]:
        """
        Get the permissions for a specific role.
        """

        permissions = UserPermissionManager._load_permissions()
        return permissions

    @staticmethod
    def set_permissions(updated_permissions: dict):
        """
        Save updated permissions dict to JSON file and update the cache.
        `updated_permissions` should be a dict like:
          {'Admin': ['Dashboard', 'Start', ...], 'Operator': [...], ...}
        """
        # Update the cached permissions
        UserPermissionManager._permissions = updated_permissions

        # Write to the JSON file
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(updated_permissions, f, indent=4)
            print("✅ Permissions saved to", CONFIG_FILE)
        except Exception as e:
            print("⚠️ Failed to save permissions:", e)
