from modules.shared.core.user.User import Role, User
from enum import Enum

class Permission(Enum):
    VIEW_WORK_FOLDER = "view_work_folder"
    VIEW_SERVICE_FOLDER = "view_service_folder"
    VIEW_ADMIN_FOLDER = "view_admin_folder"
    VIEW_STATS_FOLDER = "view_stats_folder"


# Mapping roles to allowed permissions
ROLE_PERMISSION_MAP = {
    Role.ADMIN: {
        Permission.VIEW_ADMIN_FOLDER,
        Permission.VIEW_SERVICE_FOLDER,
        Permission.VIEW_WORK_FOLDER,
        Permission.VIEW_STATS_FOLDER,
    },
    Role.SERVICE: {
        Permission.VIEW_SERVICE_FOLDER,
        Permission.VIEW_WORK_FOLDER,
    },
    Role.OPERATOR: {
        Permission.VIEW_WORK_FOLDER,
    },
}

class AuthorizationService:
    def __init__(self):
        # Initialize any required attributes here
        pass

    def can_view(self, user: User, permission: Permission) -> bool:
        role = user.role
        allowed_permissions = ROLE_PERMISSION_MAP.get(role, set())
        authorized = permission in allowed_permissions
        print(
            f"[Authorization] User '{user.firstName} {user.lastName}' with role '{role.name}' "
            f"is {'AUTHORIZED' if authorized else 'NOT AUTHORIZED'} to view folder '{permission.name}'"
        )
        return authorized


# Example usage:
if __name__ == "__main__":
    auth_service = AuthorizationService()

    admin_user = User(id=1, firstName="Alice", lastName="Admin", password="aaa", role=Role.ADMIN)
    service_user = User(id=2, firstName="Bob", lastName="Service", password="aaa", role=Role.SERVICE)
    operator_user = User(id=3, firstName="Charlie", lastName="Operator", password="aaa", role=Role.OPERATOR)

    auth_service.can_view(admin_user, Permission.VIEW_ADMIN_FOLDER)      # True
    auth_service.can_view(service_user, Permission.VIEW_ADMIN_FOLDER)    # False
    auth_service.can_view(operator_user, Permission.VIEW_WORK_FOLDER)    # True
    auth_service.can_view(operator_user, Permission.VIEW_SERVICE_FOLDER) # False
