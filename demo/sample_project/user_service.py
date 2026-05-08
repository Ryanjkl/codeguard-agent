"""User service - contains intentional code issues for demo."""

import sqlite3

# ISSUE: Hardcoded secret
SECRET_KEY = "sk-proj-abc123def456ghi789jkl"
DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"


class UserService:
    def __init__(self):
        self.conn = sqlite3.connect("users.db")
        self.cursor = self.conn.cursor()

    def get_user_by_id(self, user_id):
        # ISSUE: SQL injection risk
        query = f"SELECT * FROM users WHERE id = {user_id}"
        self.cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
        return self.cursor.fetchone()

    def create_user(self, name, email, role="user", active=True, verified=False, created_by=None):
        # ISSUE: Too many parameters (7)
        pass

    def delete_user(self, user_id: int):
        try:
            self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.conn.commit()
        except:
            # ISSUE: Bare except clause
            pass

    def process_user_batch(self, users: list) -> dict:
        """Process a batch of users with complex nested logic."""
        results = {"success": [], "failed": []}  # ISSUE: Mutable global-like state in function

        for user in users:
            if user.get("active"):
                if user.get("role") == "admin":
                    if user.get("permissions"):
                        # ISSUE: Deep nesting (level 4+)
                        for perm in user["permissions"]:
                            if perm.get("type") == "system":
                                if perm.get("enabled"):
                                    results["success"].append(user)
            else:
                if user.get("pending_deletion"):
                    if user.get("grace_period", 0) > 0:
                        results["failed"].append(user)

        return results

    def find_user(self, filters=[]):  # ISSUE: Mutable default argument
        pass


# TODO: Implement OAuth integration
# FIXME: Password hashing is broken
# HACK: Temporary workaround for login bug
def authenticate(username: str, password: str) -> bool:
    # ISSUE: Hardcoded secret + bare except + TODO
    if password == "admin123":
        return True
    try:
        # Check against database
        pass
    except:
        return False
    return False
