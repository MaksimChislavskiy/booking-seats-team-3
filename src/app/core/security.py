import re

from app.core.constants import MIN_LENGTH_USER_PASSWORD, PASSWORD_PATTERN


def check_password_rules(
    password: str,
    email: str | None = None,
) -> str | None:
    """Проверяет пароль на соответствие правилам безопасности."""
    if len(password) < MIN_LENGTH_USER_PASSWORD:
        return (
            f'Минимальная длина пароля — {MIN_LENGTH_USER_PASSWORD} символов.'
        )

    if email:
        email_part = email.split('@', 1)[0].lower()
        if email_part and email_part in password.lower():
            return 'Пароль не должен содержать email пользователя.'

    if not re.fullmatch(PASSWORD_PATTERN, password):
        return (
            'Пароль содержит недопустимые символы. '
            'Разрешены латинские буквы, цифры и символы: _ @ # $ % ! ? & *'
        )

    return None
