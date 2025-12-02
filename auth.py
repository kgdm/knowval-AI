import sqlite3
import hashlib
import re
import dns.resolver

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

    def _validate_email(self, email):
        """Validate email format and domain existence."""
        # 1. Syntax Check
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email):
            return False, "Invalid email format"
            
        # 2. Domain MX Record Check
        domain = email.split('@')[1]
        try:
            dns.resolver.resolve(domain, 'MX')
            return True, "Valid"
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return False, f"Domain '{domain}' does not exist or has no mail server."
        except Exception as e:
            # Fallback: If DNS check fails due to network, assume valid to avoid blocking users
            print(f"DNS Check Error: {e}")
            return True, "Valid (DNS check skipped)"

    def register_user(self, username, password):
        """Register a new user with email validation."""
        is_valid, msg = self._validate_email(username)
        if not is_valid:
            print(msg)
            return msg
            
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
