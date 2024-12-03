from app.infrastructure.repositories.user_repository import UserRepository
from app.domain.models.user import User

class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user_data: dict) -> User:
        """Создает нового пользователя."""
        return self.user_repository.add_user(user_data)

    def find_user_by_email(self, email: str) -> User:
        """Находит пользователя по email."""
        # Логика поиска пользователя по email может быть добавлена здесь
        print("Поиск пользователя по email:", email)
        return self.user_repository.get_user_by_email(email)
