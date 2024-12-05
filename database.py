import sqlite3
import json
from typing import Dict, List, Optional

class Database:
    def __init__(self, db_file: str = "friendship_test.db"):
        self.db_file = db_file
        self.create_tables()
    
    def create_tables(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tests (
            test_id TEXT PRIMARY KEY,
            creator_id INTEGER,
            creator_answers TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id TEXT,
            user_id INTEGER,
            answers TEXT,
            correct_count INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (test_id) REFERENCES tests (test_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_test(self, test_id: str, creator_id: int, creator_answers: Dict) -> bool:
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO tests (test_id, creator_id, creator_answers) VALUES (?, ?, ?)',
                (test_id, creator_id, json.dumps(creator_answers))
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving test: {e}")
            return False
    
    def get_test(self, test_id: str) -> Optional[Dict]:
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM tests WHERE test_id = ?', (test_id,))
            test = cursor.fetchone()
            
            if test:
                return {
                    'test_id': test[0],
                    'creator_id': test[1],
                    'creator_answers': json.loads(test[2]),
                    'created_at': test[3]
                }
            
            return None
        except Exception as e:
            print(f"Error getting test: {e}")
            return None
    
    def save_participant(self, test_id: str, user_id: int, answers: Dict, correct_count: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute(
                'INSERT INTO participants (test_id, user_id, answers, correct_count) VALUES (?, ?, ?, ?)',
                (test_id, user_id, json.dumps(answers), correct_count)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving participant: {e}")
            return False
    
    def get_participant_results(self, test_id: str) -> List[Dict]:
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM participants WHERE test_id = ?', (test_id,))
            participants = cursor.fetchall()
            
            return [{
                'id': p[0],
                'test_id': p[1],
                'user_id': p[2],
                'answers': json.loads(p[3]),
                'correct_count': p[4],
                'completed_at': p[5]
            } for p in participants]
            
        except Exception as e:
            print(f"Error getting participants: {e}")
            return []
    
    def has_participant_completed(self, test_id: str, user_id: int) -> bool:
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT COUNT(*) FROM participants WHERE test_id = ? AND user_id = ?',
                (test_id, user_id)
            )
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            print(f"Error checking participant completion: {e}")
            return False
