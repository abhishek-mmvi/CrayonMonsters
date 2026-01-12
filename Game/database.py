"""
CrayonMonsters Database Module
Handles user accounts with SQLite + bcrypt password hashing.
"""
import sqlite3
import bcrypt
from config import DATABASE_PATH


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database tables."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1 TEXT NOT NULL,
            player2 TEXT NOT NULL,
            winner TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized.")


def create_user(username: str, password: str) -> tuple:
    """
    Create a new user account.
    Returns (success: bool, message: str)
    """
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(password) < 4:
        return False, "Password must be at least 4 characters"
    
    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash.decode('utf-8'))
        )
        conn.commit()
        conn.close()
        return True, "Account created successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    except Exception as e:
        return False, str(e)


def verify_user(username: str, password: str) -> tuple:
    """
    Verify user credentials.
    Returns (success: bool, message: str)
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return False, "User not found"
    
    stored_hash = row['password_hash'].encode('utf-8')
    
    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        return True, "Login successful"
    else:
        return False, "Incorrect password"


def record_match(player1: str, player2: str, winner: str):
    """Record a completed match."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO match_history (player1, player2, winner) VALUES (?, ?, ?)',
        (player1, player2, winner)
    )
    conn.commit()
    conn.close()


def get_user_stats(username: str) -> dict:
    """Get win/loss stats for a user."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        'SELECT COUNT(*) as wins FROM match_history WHERE winner = ?',
        (username,)
    )
    wins = cursor.fetchone()['wins']
    
    cursor.execute(
        '''SELECT COUNT(*) as losses FROM match_history 
           WHERE (player1 = ? OR player2 = ?) AND winner != ? AND winner IS NOT NULL''',
        (username, username, username)
    )
    losses = cursor.fetchone()['losses']
    
    conn.close()
    return {'wins': wins, 'losses': losses}


if __name__ == '__main__':
    init_db()
    print("Database setup complete!")
