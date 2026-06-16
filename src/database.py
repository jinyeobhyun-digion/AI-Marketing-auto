import sqlite3
import os
import pandas as pd

# 데이터베이스 파일 경로 설정 (data/marketing.db)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "marketing.db")

def get_connection():
    """
    SQLite 데이터베이스 커넥션을 반환하고, data/ 폴더가 없을 경우 생성합니다.
    """
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return sqlite3.connect(DB_PATH)

def init_db():
    """
    마케팅 콘텐츠 히스토리를 저장할 테이블(marketing_history)을 생성합니다.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marketing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            news_title TEXT NOT NULL,
            blog_post TEXT,
            instagram_reels TEXT,
            youtube_shorts TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("📢 [DB] 데이터베이스 테이블 marketing_history 초기화 완료.")

def insert_marketing_history(date, news_title, blog_post, instagram_reels, youtube_shorts):
    """
    생성된 마케팅 콘텐츠 3종 세트를 데이터베이스에 저장합니다.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO marketing_history (date, news_title, blog_post, instagram_reels, youtube_shorts)
            VALUES (?, ?, ?, ?, ?)
        """, (date, news_title, blog_post, instagram_reels, youtube_shorts))
        conn.commit()
        print(f"💾 [DB 저장 성공] {date}자 마케팅 콘텐츠가 데이터베이스에 저장되었습니다.")
        return True
    except Exception as e:
        print(f"❌ [DB 저장 실패] 데이터베이스 오류: {e}")
        return False
    finally:
        conn.close()

def get_all_history():
    """
    저장된 모든 마케팅 콘텐츠 히스토리를 Pandas DataFrame으로 가져옵니다.
    """
    conn = get_connection()
    try:
        # 최신 등록순으로 데이터 조회
        df = pd.read_sql_query("SELECT * FROM marketing_history ORDER BY id DESC", conn)
        return df
    except Exception as e:
        print(f"❌ [DB 조회 실패] 데이터베이스 오류: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

# 모듈 로드 시 데이터베이스 초기화 자동 실행
init_db()
