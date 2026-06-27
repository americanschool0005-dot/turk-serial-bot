import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")

def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            user_id BIGINT PRIMARY KEY
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS series (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS seasons (
            id SERIAL PRIMARY KEY,
            series_id INTEGER NOT NULL REFERENCES series(id) ON DELETE CASCADE,
            season_number INTEGER NOT NULL,
            UNIQUE(series_id, season_number)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS episodes (
            id SERIAL PRIMARY KEY,
            season_id INTEGER NOT NULL REFERENCES seasons(id) ON DELETE CASCADE,
            episode_number INTEGER NOT NULL,
            file_id TEXT NOT NULL,
            title TEXT,
            UNIQUE(season_id, episode_number)
        )
    """)

    default_series = [
        "Qashqirlar makoni", "Ichkarida", "Chuqur", "Hukm",
        "Hukmdor Usmon", "Oila uchun", "Sevgi istorbi", "Muhtasham Yuz Yil"
    ]
    for s_name in default_series:
        cursor.execute("INSERT INTO series (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (s_name,))

    conn.commit()
    cursor.close()
    conn.close()

def is_admin(user_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM admins WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row is not None

def add_admin(user_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO admins (user_id) VALUES (%s) ON CONFLICT DO NOTHING", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

def get_all_series():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM series ORDER BY id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r[0], "name": r[1]} for r in rows]

def get_seasons(series_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, season_number FROM seasons WHERE series_id = %s ORDER BY season_number", (series_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r[0], "season_number": r[1]} for r in rows]

def get_episodes(season_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, episode_number, file_id, title FROM episodes WHERE season_id = %s ORDER BY episode_number", (season_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r[0], "episode_number": r[1], "file_id": r[2], "title": r[3]} for r in rows]

def get_all_episodes_for_series(series_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.episode_number, e.file_id, e.title
        FROM episodes e
        JOIN seasons s ON e.season_id = s.id
        WHERE s.series_id = %s
        ORDER BY e.episode_number
    """, (series_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"id": r[0], "episode_number": r[1], "file_id": r[2], "title": r[3]} for r in rows]

def get_episode_by_id(episode_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.file_id, e.title, e.episode_number, s.name
        FROM episodes e
        JOIN seasons se ON e.season_id = se.id
        JOIN series s ON se.series_id = s.id
        WHERE e.id = %s
    """, (episode_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def add_series_episode(series_name, season_number, episode_number, file_id, title=""):
    conn = get_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO series (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (series_name,))
        cursor.execute("SELECT id FROM series WHERE name = %s", (series_name,))
        series_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO seasons (series_id, season_number) VALUES (%s, %s) ON CONFLICT (series_id, season_number) DO NOTHING", (series_id, season_number))
        cursor.execute("SELECT id FROM seasons WHERE series_id = %s AND season_number = %s", (series_id, season_number))
        season_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO episodes (season_id, episode_number, file_id, title)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (season_id, episode_number) DO UPDATE SET file_id = EXCLUDED.file_id, title = EXCLUDED.title
        """, (season_id, episode_number, file_id, title))

        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
