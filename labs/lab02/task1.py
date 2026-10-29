"""Завдання 1: модель користувача, безпечних сесій та журналу аудиту."""

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

PBKDF2_ITERATIONS = 600_000
SALT_SIZE = 16
SESSION_TIMEOUT_SEC = 900

# Локальна частина: літера + 2-63 символи (літери, цифри, _), тобто 3-64 разом.
# Домен: щонайменше одна крапка.
EMAIL_PATTERN = re.compile(
    r"[A-Za-z][A-Za-z0-9_]{2,63}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
)


def utc_now() -> datetime:
    """Поточний час UTC з часовим поясом."""
    return datetime.now(timezone.utc)


class User:
    """Користувач із безпечним зберіганням пароля (PBKDF2 + сіль)."""

    def __init__(self, username: str, email: str, role: str, active: bool = True):
        self.username = username
        self.email = email  # проходить через setter із валідацією
        self.role = role
        self.active = active
        self.__password_salt: bytes = b""
        self.__password_hash: bytes = b""

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not isinstance(value, str) or not EMAIL_PATTERN.fullmatch(value):
            raise ValueError(f"Некоректний формат email: {value!r}")
        self._email = value

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )

    def set_password(self, password: str) -> None:
        if not isinstance(password, str) or not password:
            raise ValueError("Пароль повинен бути непорожнім рядком")
        self.__password_salt = os.urandom(SALT_SIZE)
        self.__password_hash = self._derive_key(password, self.__password_salt)

    def check_password(self, password: str) -> bool:
        if not self.__password_hash or not isinstance(password, str):
            return False
        candidate = self._derive_key(password, self.__password_salt)
        return hmac.compare_digest(self.__password_hash, candidate)

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return (
            f"User({self.username}, {self.email}, Role: {self.role}, Status: {status})"
        )


class Admin(User):
    """Адміністратор: користувач із набором дозволів."""

    def __init__(
        self,
        username: str,
        email: str,
        permissions: list[str] | set[str] | None = None,
        active: bool = True,
    ):
        super().__init__(username, email, role="admin", active=active)
        self.permissions: set[str] = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        perms = ", ".join(sorted(self.permissions)) if self.permissions else "none"
        return f"{super().__str__()} | Permissions: [{perms}]"


class Session:
    """Сеанс користувача з відстеженням останньої активності (UTC)."""

    def __init__(self, ip: str):
        self.ip = ip
        now = utc_now()
        self.login_time: datetime = now
        self.last_activity: datetime = now

    def touch(self) -> None:
        self.last_activity = utc_now()

    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec повинен бути додатним числом")
        return utc_now() - self.last_activity <= timedelta(seconds=timeout_sec)


@dataclass(frozen=True)
class AuditRecord:
    """Один запис журналу аудиту (незмінний)."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Журнал подій безпеки. Паролі в журнал не потрапляють."""

    def __init__(self):
        self._records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        self._records.append(AuditRecord(utc_now(), username, action))

    def show_all(self) -> list[AuditRecord]:
        return list(self._records)


class UserAccount:
    """Композиція: User + Session + AuditLog."""

    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ):
        self.user = user
        self.session = session
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        if (
            username == self.user.username
            and self.user.active
            and self.user.check_password(password)
        ):
            self.session = Session(ip)
            self.session.touch()
            self.audit_log.add_log(username, "login_success")
            return True
        self.audit_log.add_log(username, "login_failure")
        return False

    def is_authenticated(self) -> bool:
        """Перевірка не продовжує сеанс."""
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        if self.session is not None:
            self.audit_log.add_log(self.user.username, "logout")
        self.session = None

    def __getitem__(self, key: str):
        if key == "user":
            return self.user
        if key == "session":
            return self.session
        if key == "audit_log":
            return self.audit_log
        raise KeyError(f"Ключ {key!r} невідомий або недоступний")

    def __setitem__(self, key: str, value) -> None:
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Значення для 'user' повинно бути User")
            self.user = value
            self.session = None  # сеанс попереднього користувача недійсний
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Значення для 'session' повинно бути Session")
            self.session = value
        elif key == "audit_log":
            if not isinstance(value, AuditLog):
                raise TypeError("Значення для 'audit_log' повинно бути AuditLog")
            self.audit_log = value
        else:
            raise KeyError(f"Ключ {key!r} невідомий або недоступний")