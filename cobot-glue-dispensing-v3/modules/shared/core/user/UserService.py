from modules.shared.core.user.User import AbstractUser
class UserService:
    def __init__(self,repository):
        self.repository = repository

    def addUser(self, user):
        if not self.validateUser(user):
            raise ValueError("Invalid user")
        print(f"Adding user: {user}")
        result = self.repository.insert(user)
        return result

    def getUserById(self, id):
        return self.repository.get(id)

    def validateUser(self, user):
        if not isinstance(user, AbstractUser):
            return False
        return True
