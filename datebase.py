import sqlite3
import os
from typing import Optional, List, Dict
from datetime import datetime


class Database:
    def __init__(self, db_name="data/advice.db"):
        # Создаем папку data если она не существует
        os.makedirs(os.path.dirname(db_name), exist_ok=True)

        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self.create_tables()
        self.insert_initial_data()

    def create_tables(self):
        # Таблица пользователей
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица упражнений (exercise)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS exercise (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                video_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица советов (advice)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS advice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT NOT NULL,
                video_url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица комментариев
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                comment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Таблица истории просмотров
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS view_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_type TEXT NOT NULL, -- 'exercise' или 'advice'
                item_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        self.conn.commit()

    def insert_initial_data(self):
        """Вставляем начальные данные если таблицы пустые"""

        # Проверяем есть ли данные в таблице exercise
        self.cur.execute("SELECT COUNT(*) as count FROM exercise")
        if self.cur.fetchone()['count'] == 0:
            # Вставляем упражнения
            exercises = [
                ("1.1 тыныс алу", "Терен тыныс алу: Мұрынмен 5 секунд...", "1.2.mp4"),
                ("2.2 жаттығу", "Күн сайын 15 минут йога немесе жеңіл...", "1.2.mp4"),
                ("3.3 жаттығу", "Иық айналдыру: 10 рет алға, 10 рет ...", "1.2.mp4"),
                ("4.4 жаттығу", "Қол бұлғау: 30 секунд бойы қолды кен...", "1.2.mp4"),
                ("5.5 жаттығу", "Көз жаттығуы: алыстағы нысанға 5 ...", "1.2.mp4"),
                ("6.6 жаттығу", "Мойын айналдыру: басты жаймен онға ...", "1.2.mp4"),
            ]
            self.cur.executemany(
                "INSERT INTO exercise (name, description, video_url) VALUES (?, ?, ?)",
                exercises
            )

        # Проверяем есть ли данные в таблице advice
        self.cur.execute("SELECT COUNT(*) as count FROM advice")
        if self.cur.fetchone()['count'] == 0:
            # Вставляем советы
            advices = [
                ("1.1 кеңес", "Күніне 10 минут тыныс алу жаттығуын ...", "1.1.mp4"),
                ("2.2 кеңес", "Таңертен күн сәулесіне шығып, ...", "1.1.mp4"),
                ("3.3 кеңес", "Ұйықтар алдында 5 минут тыныштықта ...", "1.1.mp4"),
                ("4.4 кеңес", "Күніне кемінде 1,5 литр су ішуді ...", "1.1.mp4"),
                ("5.5 кеңес", "Таңертен бір стакан жылы су ішініз —...", "1.1.mp4"),
                ("6.6 кеңес", "Күні бойы ер сағат сайын аздан ...", "1.1.mp4"),
            ]
            self.cur.executemany(
                "INSERT INTO advice (name, content, video_url) VALUES (?, ?, ?)",
                advices
            )

        self.conn.commit()

    # Методы для работы с упражнениями
    def get_all_exercises(self) -> List[Dict]:
        self.cur.execute("SELECT * FROM exercise ORDER BY id")
        rows = self.cur.fetchall()
        return [dict(row) for row in rows]

    def get_exercise_by_id(self, exercise_id: int) -> Optional[Dict]:
        self.cur.execute("SELECT * FROM exercise WHERE id = ?", (exercise_id,))
        row = self.cur.fetchone()
        return dict(row) if row else None

    def add_exercise(self, name: str, description: str, video_url: str) -> bool:
        try:
            self.cur.execute(
                "INSERT INTO exercise (name, description, video_url) VALUES (?, ?, ?)",
                (name, description, video_url)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    # Методы для работы с советами
    def get_all_advice(self) -> List[Dict]:
        self.cur.execute("SELECT * FROM advice ORDER BY id")
        rows = self.cur.fetchall()
        return [dict(row) for row in rows]

    def get_advice_by_id(self, advice_id: int) -> Optional[Dict]:
        self.cur.execute("SELECT * FROM advice WHERE id = ?", (advice_id,))
        row = self.cur.fetchone()
        return dict(row) if row else None

    def add_advice(self, name: str, content: str, video_url: str) -> bool:
        try:
            self.cur.execute(
                "INSERT INTO advice (name, content, video_url) VALUES (?, ?, ?)",
                (name, content, video_url)
            )
            self.conn.commit()
            return True
        except sqlite3.Error:
            return False

    # Методы для комментариев
    def add_comment(self, user_id: int, first_name: str, last_name: str, comment: str) -> bool:
        try:
            self.cur.execute(
                "INSERT INTO comments (user_id, first_name, last_name, comment) VALUES (?, ?, ?, ?)",
                (user_id, first_name, last_name, comment)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding comment: {e}")
            return False

    def get_all_comments(self) -> List[Dict]:
        self.cur.execute("""
            SELECT c.*, u.name as user_name 
            FROM comments c 
            LEFT JOIN users u ON c.user_id = u.id 
            ORDER BY c.created_at DESC
        """)
        rows = self.cur.fetchall()
        return [dict(row) for row in rows]

    def get_user_comments(self, user_id: int) -> List[Dict]:
        self.cur.execute("SELECT * FROM comments WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = self.cur.fetchall()
        return [dict(row) for row in rows]

    # Методы для истории просмотров
    def add_view_history(self, user_id: int, item_type: str, item_id: int, item_name: str) -> bool:
        try:
            # Проверяем, есть ли уже такая запись в истории
            self.cur.execute(
                "SELECT * FROM view_history WHERE user_id = ? AND item_type = ? AND item_id = ?",
                (user_id, item_type, item_id)
            )
            existing = self.cur.fetchone()

            if not existing:
                # Добавляем новую запись
                self.cur.execute(
                    "INSERT INTO view_history (user_id, item_type, item_id, item_name) VALUES (?, ?, ?, ?)",
                    (user_id, item_type, item_id, item_name)
                )
            else:
                # Обновляем время просмотра
                self.cur.execute(
                    "UPDATE view_history SET viewed_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (existing['id'],)
                )

            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error adding view history: {e}")
            return False

    def get_view_history(self, user_id: int) -> List[Dict]:
        self.cur.execute(
            "SELECT * FROM view_history WHERE user_id = ? ORDER BY viewed_at DESC LIMIT 20",
            (user_id,)
        )
        rows = self.cur.fetchall()
        return [dict(row) for row in rows]

    # Методы для пользователей
    def insert_user(self, name, email, password):
        try:
            self.cur.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                             (name, email, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # Email уже существует

    def get_user_by_email(self, email) -> Optional[sqlite3.Row]:
        self.cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        return self.cur.fetchone()

    def get_user_by_id(self, user_id: int) -> Optional[sqlite3.Row]:
        self.cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return self.cur.fetchone()

    def verify_user(self, email, password) -> bool:
        user = self.get_user_by_email(email)
        if user and user['password'] == password:
            return True
        return False

    def get_all_users(self):
        self.cur.execute("SELECT * FROM users")
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()


# Функция для dependency injection
def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()