from sqlmodel import SQLModel

SQLModel.metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

from app.models.checkout import Checkout  # noqa: E402
from app.models.user import User  # noqa: E402

__all__ = ["Checkout", "User"]
