import sqlite3
import uuid
from datetime import datetime

class SessionManager:
    def __init__(self, db_path="sessions.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the sessions table."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sessions
                     (id TEXT PRIMARY KEY, user_id TEXT, name TEXT, created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS quiz_state
                     (session_id TEXT PRIMARY KEY, quiz_data TEXT, current_index INTEGER, user_answers TEXT, score INTEGER, answer_submitted INTEGER)''')
        conn.commit()
        conn.close()

    def create_session(self, user_id, name=None, session_id=None):
        """Create a new session for a user."""
        if not session_id:
            session_id = str(uuid.uuid4())
        if not name:
            name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO sessions (id, user_id, name, created_at) VALUES (?, ?, ?, ?)",
                      (session_id, user_id, name, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            return session_id
        except Exception as e:
            print(f"Error creating session: {e}")
            return None

    def update_session_name(self, session_id, new_name):
        """Update the name of a session."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("UPDATE sessions SET name=? WHERE id=?", (new_name, session_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error updating session name: {e}")
            return False

    def save_quiz_state(self, session_id, quiz_data, current_index, user_answers, score, answer_submitted):
        """Save the current quiz state."""
        import json
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''INSERT OR REPLACE INTO quiz_state 
                         (session_id, quiz_data, current_index, user_answers, score, answer_submitted) 
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (session_id, json.dumps(quiz_data), current_index, json.dumps(user_answers), score, int(answer_submitted)))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving quiz state: {e}")
            return False

    def load_quiz_state(self, session_id):
        """Load the quiz state for a session."""
        import json
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM quiz_state WHERE session_id=?", (session_id,))
            row = c.fetchone()
            conn.close()
            
            if row:
                user_answers = json.loads(row['user_answers'])
                # Convert keys back to integers (JSON converts them to strings)
                user_answers = {int(k): v for k, v in user_answers.items()}
                
                return {
                    "quiz_data": json.loads(row['quiz_data']),
                    "current_index": row['current_index'],
                    "user_answers": user_answers,
                    "score": row['score'],
                    "answer_submitted": bool(row['answer_submitted'])
                }
            return None
        except Exception as e:
            print(f"Error loading quiz state: {e}")
            return None

    def get_user_sessions(self, user_id):
        """Get all sessions for a user."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM sessions WHERE user_id=? ORDER BY created_at DESC", (user_id,))
            sessions = [dict(row) for row in c.fetchall()]
            conn.close()
            return sessions
        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []

    def delete_session(self, session_id):
        """Delete a session."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("DELETE FROM sessions WHERE id=?", (session_id,))
            c.execute("DELETE FROM quiz_state WHERE session_id=?", (session_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
