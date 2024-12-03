from app.domain.models.user import User

class UserRepository:
    """Репозиторий для работы с таблицей пользователей."""

    def add_user(self, user_data: dict) -> User:
        """Добавляет нового пользователя в базу данных."""
        # Здесь добавьте логику для добавления пользователя в базу данных
        print("Добавление пользователя в базу данных:", user_data)
        return User(**user_data)

    def get_user_by_email(self, email: str) -> User:
        """Получает пользователя по email."""
        # Здесь добавьте логику для получения пользователя из базы данных
        print("Получение пользователя по email:", email)
        return User(email=email)
