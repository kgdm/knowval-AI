import sqlite3
import hashlib

class AuthManager:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the users table."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (username TEXT PRIMARY KEY, password TEXT)''')
        conn.commit()
        conn.close()

    def _hash_password(self, password):
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password):
        """Register a new user."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            hashed_pw = self._hash_password(password)
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_pw))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
        except Exception as e:
            print(f"Registration error: {e}")
            return False

    def login_user(self, username, password):
        """Verify user credentials."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        hashed_pw = self._hash_password(password)
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_pw))
        user = c.fetchone()
        conn.close()
        return user is not None
