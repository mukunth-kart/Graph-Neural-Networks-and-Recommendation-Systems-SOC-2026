import sqlite3
import os
import bcrypt

def hash_password(password: str) -> str:
    # Hash password using bcrypt
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    # Verify password using bcrypt
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

DB_PATH = os.path.join(os.path.dirname(__file__), "recommender.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        status TEXT NOT NULL DEFAULT 'active'
    )
    """)
    
    # 2. Movies Table (ID matches MovieLens movieID)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        genres TEXT NOT NULL,
        release_year INTEGER
    )
    """)
    
    # 3. Ratings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        movie_id INTEGER NOT NULL,
        rating REAL NOT NULL,
        timestamp INTEGER NOT NULL,
        is_new_feedback INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (movie_id) REFERENCES movies(id),
        UNIQUE(user_id, movie_id)
    )
    """)
    
    # 4. Training Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS training_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        status TEXT NOT NULL,
        loss REAL,
        metrics TEXT
    )
    """)
    
    conn.commit()
    
    # Insert default admin user if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_pass_hash = hash_password("admin123")
        cursor.execute(
            "INSERT INTO users (username, email, phone, password_hash, role, status) VALUES (?, ?, ?, ?, ?, ?)",
            ("admin", "admin@recommender.com", "+1234567890", admin_pass_hash, "admin", "active")
        )
        conn.commit()
        
    conn.close()

# Helper queries for auth
def create_user(username, email, phone, password, role="user"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, phone, password_hash, role, status) VALUES (?, ?, ?, ?, ?, 'active')",
            (username, email, phone, password_hash, role)
        )
        conn.commit()
        return True, "User registered successfully."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def set_user_status(user_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE id = ?", (status, user_id))
    conn.commit()
    conn.close()

def list_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, phone, role, status FROM users WHERE role != 'admin'")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Helper queries for movies
def search_movies(query_str=None, genre=None, limit=20, offset=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = "SELECT * FROM movies WHERE 1=1"
    params = []
    
    if query_str:
        sql += " AND title LIKE ?"
        params.append(f"%{query_str}%")
    if genre:
        sql += " AND genres LIKE ?"
        params.append(f"%{genre}%")
        
    sql += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_movies_by_ids(movie_ids):
    if not movie_ids:
        return []
    conn = get_db_connection()
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(movie_ids))
    cursor.execute(f"SELECT * FROM movies WHERE id IN ({placeholders})", movie_ids)
    rows = cursor.fetchall()
    conn.close()
    # Return as dict keyed by id for quick lookup
    return {r["id"]: dict(r) for r in rows}

def bulk_insert_movies(movies_list):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT OR IGNORE INTO movies (id, title, genres, release_year) VALUES (?, ?, ?, ?)",
        movies_list
    )
    conn.commit()
    conn.close()

# Helper queries for ratings
def add_user_rating(user_id, movie_id, rating, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if user is active
        cursor.execute("SELECT status FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user or user["status"] == "banned":
            return False, "User is banned or does not exist."
            
        cursor.execute(
            """
            INSERT INTO ratings (user_id, movie_id, rating, timestamp, is_new_feedback)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(user_id, movie_id) DO UPDATE SET
                rating = excluded.rating,
                timestamp = excluded.timestamp,
                is_new_feedback = 1
            """,
            (user_id, movie_id, rating, timestamp)
        )
        conn.commit()
        return True, "Rating recorded."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_user_ratings(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.movie_id, r.rating, m.title, m.genres, m.release_year 
        FROM ratings r
        JOIN movies m ON r.movie_id = m.id
        WHERE r.user_id = ?
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_ratings_for_training():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Exclude ratings from banned users
    cursor.execute(
        """
        SELECT r.user_id, r.movie_id, r.rating 
        FROM ratings r
        JOIN users u ON r.user_id = u.id
        WHERE u.status = 'active'
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_ratings_as_trained():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE ratings SET is_new_feedback = 0 WHERE is_new_feedback = 1")
    conn.commit()
    conn.close()

# Logs management
def add_training_log(timestamp, status, loss=None, metrics=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO training_logs (timestamp, status, loss, metrics) VALUES (?, ?, ?, ?)",
        (timestamp, status, loss, metrics)
    )
    conn.commit()
    conn.close()

def get_latest_training_logs(limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM training_logs ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
