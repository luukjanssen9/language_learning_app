from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPkMixin


class User(UUIDPkMixin, CreatedAtMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Google's stable per-account subject id (the ID token's `sub` claim) --
    # never changes, unlike email. Nullable: a row created before real auth
    # existed (or seeded directly) has none until someone actually signs in
    # and claims it -- see app/api/routes/auth.py's legacy-claim logic.
    google_sub: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
