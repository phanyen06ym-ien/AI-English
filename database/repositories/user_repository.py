"""Repository cho bang `users`.

Cau SQL giu NGUYEN VAN so voi Sprint 3. Chi khac o cho:

- Tra ve entity `User` thay vi tuple/dict.
- Khong con tu bam mat khau, khong con tu quyet dinh nang cap hash.
  Phan do la business rule, da chuyen len `AuthService`.
"""

from __future__ import annotations

from database.entities import User
from database.exceptions import NotFoundError
from database.repositories.base import BaseRepository


SQL_FIND_BY_USERNAME = """
    SELECT
        id,
        username,
        fullname,
        password
    FROM users
    WHERE username = %s
    LIMIT 1;
"""

SQL_FIND_PASSWORD_BY_ID = """
    SELECT password
    FROM users
    WHERE id = %s
    LIMIT 1;
"""

SQL_INSERT_USER = """
    INSERT INTO users (
        fullname,
        username,
        password
    )
    VALUES (%s, %s, %s)
    RETURNING id, username, fullname;
"""

SQL_UPDATE_PASSWORD = """
    UPDATE users
    SET password = %s
    WHERE id = %s;
"""


class UserRepository(BaseRepository):
    """Truy cap bang `users`."""

    def find_by_username(
        self,
        username: str,
    ) -> User | None:
        """Tim nguoi dung theo ten dang nhap. None neu khong co."""
        normalized_username = username.strip()

        if not normalized_username:
            return None

        row = self.fetch_one(
            SQL_FIND_BY_USERNAME,
            (normalized_username,),
        )

        if row is None:
            return None

        return User.from_row(row)

    def exists(
        self,
        username: str,
    ) -> bool:
        """True neu ten dang nhap da duoc dung."""
        return self.find_by_username(username) is not None

    def get_password_hash(
        self,
        user_id: int,
    ) -> str:
        """Doc gia tri mat khau dang luu cua mot nguoi dung."""
        row = self.fetch_one(
            SQL_FIND_PASSWORD_BY_ID,
            (user_id,),
        )

        if row is None:
            raise NotFoundError(
                f"Không tìm thấy người dùng id={user_id}."
            )

        return str(row[0] or "")

    def create(
        self,
        fullname: str,
        username: str,
        password_hash: str,
    ) -> User:
        """Them nguoi dung moi va tra ve entity vua tao."""
        row = self.execute_returning(
            SQL_INSERT_USER,
            (
                fullname.strip(),
                username.strip(),
                password_hash,
            ),
        )

        return User.from_row(
            row,
            include_password=False,
        )

    def update_password_hash(
        self,
        user_id: int,
        password_hash: str,
    ) -> bool:
        """Cap nhat mat khau da bam. True neu co dong bi sua."""
        affected = self.execute(
            SQL_UPDATE_PASSWORD,
            (
                password_hash,
                int(user_id),
            ),
        )

        return affected > 0
