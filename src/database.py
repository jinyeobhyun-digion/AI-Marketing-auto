import sqlite3
import os
import pandas as pd

# 데이터베이스 파일 경로 설정 (data/marketing.db)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "marketing.db")

def get_connection():
    """
    SQLite 데이터베이스 커넥션을 반환합니다.
    클라우드 환경(예: Streamlit Cloud)의 제한된 파일 시스템 쓰기 권한 및 경로 문제를 우회하고 
    예외 발생 시 메모리 내 DB(:memory:)로 임시 우회하여 시스템 크래시를 방지합니다.
    """
    db_dir = os.path.dirname(DB_PATH)
    try:
        # data/ 폴더가 없을 경우 생성 시도
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        return sqlite3.connect(DB_PATH)
    except Exception as e:
        print(f"⚠️ [DB 경로 오류] 로컬 디스크 DB 생성 실패: {e}")
        print("💡 [우회 작동] 클라우드 샌드박스 환경 우회를 위해 메모리 내 임시 DB(:memory:)로 연결을 시도합니다.")
        # 쓰기 권한이 완전히 막힌 서버 환경용 우회책
        return sqlite3.connect(":memory:")

def init_db():
    """
    마케팅 콘텐츠 히스토리를 저장할 테이블(marketing_history)을 생성합니다.
    """
    try:
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
    except Exception as e:
        print(f"❌ [DB 초기화 실패] {e}")

def insert_marketing_history(date, news_title, blog_post, instagram_reels, youtube_shorts):
    """
    생성된 마케팅 콘텐츠 3종 세트를 데이터베이스에 저장합니다.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
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
        try:
            conn.close()
        except NameError:
            pass

def get_all_history():
    """
    저장된 모든 마케팅 콘텐츠 히스토리를 Pandas DataFrame으로 가져옵니다.
    """
    try:
        conn = get_connection()
        # 최신 등록순으로 데이터 조회
        df = pd.read_sql_query("SELECT * FROM marketing_history ORDER BY id DESC", conn)
        return df
    except Exception as e:
        print(f"❌ [DB 조회 실패] 데이터베이스 오류: {e}")
        return pd.DataFrame()
    finally:
        try:
            conn.close()
        except NameError:
            pass

# 모듈 로드 시 데이터베이스 초기화 자동 실행
init_db()
