from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserFactory:
    email: str = "alice@example.com"
    password: str = "correct-horse-battery"

    def as_register_payload(self) -> dict[str, str]:
        return {"email": self.email, "password": self.password}

    def as_login_form(self) -> dict[str, str]:
        return {"username": self.email, "password": self.password}
