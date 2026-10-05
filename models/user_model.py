from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from services.database_service import DatabaseService

class User(UserMixin):
    def __init__(self, id, name, email, password_hash, role, is_active=1, created_at=None):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = (role or "USER").upper()
        self._is_active = bool(int(is_active)) if is_active is not None else True
        self.created_at = created_at

    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = bool(value)

    @property
    def is_admin(self):
        return self.role.upper() == "ADMIN"

    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_id(cls, user_id):
        data = DatabaseService.execute_query(
            "SELECT * FROM users WHERE id = %s", (user_id,), fetch_one=True
        )
        if data:
            return cls(
                id=data["id"],
                name=data["name"],
                email=data["email"],
                password_hash=data["password_hash"],
                role=data.get("role", "USER"),
                is_active=data.get("is_active", 1),
                created_at=data.get("created_at")
            )
        return None

    @classmethod
    def get_by_email(cls, email):
        if not email:
            return None
        data = DatabaseService.execute_query(
            "SELECT * FROM users WHERE email = %s", (email.strip().lower(),), fetch_one=True
        )
        if data:
            return cls(
                id=data["id"],
                name=data["name"],
                email=data["email"],
                password_hash=data["password_hash"],
                role=data.get("role", "USER"),
                is_active=data.get("is_active", 1),
                created_at=data.get("created_at")
            )
        return None

    @classmethod
    def create_user(cls, name, email, password, role="USER"):
        hashed = generate_password_hash(password)
        user_id = DatabaseService.execute_insert(
            "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, 1)",
            (name.strip(), email.strip().lower(), hashed, role.upper())
        )
        return cls.get_by_id(user_id)

    @classmethod
    def get_all_users(cls, search=None, role=None, status=None):
        query = "SELECT id, name, email, role, is_active, created_at FROM users WHERE 1=1"
        params = []

        if search:
            query += " AND (name LIKE %s OR email LIKE %s)"
            params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])

        if role and role.upper() != "ALL":
            query += " AND role = %s"
            params.append(role.strip().upper())

        if status is not None and str(status).strip() != "" and str(status).lower() != "all":
            try:
                query += " AND is_active = %s"
                params.append(int(status))
            except ValueError:
                pass

        query += " ORDER BY created_at DESC"
        return DatabaseService.execute_query(query, tuple(params))

    @classmethod
    def update_profile(cls, user_id, name):
        return DatabaseService.execute_query(
            "UPDATE users SET name = %s WHERE id = %s", (name.strip(), user_id), fetch_all=False
        )

    @classmethod
    def update_password(cls, user_id, new_password):
        hashed = generate_password_hash(new_password)
        return DatabaseService.execute_query(
            "UPDATE users SET password_hash = %s WHERE id = %s", (hashed, user_id), fetch_all=False
        )

    @classmethod
    def update_role(cls, user_id, new_role):
        return DatabaseService.execute_query(
            "UPDATE users SET role = %s WHERE id = %s", (new_role.upper(), user_id), fetch_all=False
        )

    @classmethod
    def toggle_active(cls, user_id):
        user = cls.get_by_id(user_id)
        if not user:
            return False
        new_status = 0 if user.is_active else 1
        DatabaseService.execute_query(
            "UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id), fetch_all=False
        )
        return new_status

    @classmethod
    def count_admins(cls):
        res = DatabaseService.execute_query(
            "SELECT COUNT(*) as cnt FROM users WHERE role = 'ADMIN' AND (is_active = 1 OR is_active IS NULL)",
            fetch_one=True
        )
        return res.get("cnt", 0) if res else 0

    @classmethod
    def delete_user(cls, user_id):
        return DatabaseService.execute_query(
            "DELETE FROM users WHERE id = %s", (user_id,), fetch_all=False
        )
