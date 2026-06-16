import os
import sys
import time
from datetime import datetime
import pandas as pd
import schedule
from dotenv import load_dotenv

# sys.path에 src 폴더 경로를 추가하여 모듈 참조 에러 방지
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler import get_latest_news, save_to_excel
from generator import generate_multi_content
from database import insert_marketing_history

def parse_multi_content(text):
    """
    제미나이가 생성한 3대 플랫폼 마크다운 텍스트를 분석하여 
    블로그, 릴스, 쇼츠 텍스트로 분할합니다.
    """
    blog_post = ""
    instagram_reels = ""
    youtube_shorts = ""
    
    # 헤더 단위로 스플릿
    parts = text.split("###")
    for part in parts:
        part_strip = part.strip()
        if not part_strip:
            continue
            
        # 블로그 포스팅 감지
        if "1. 네이버 블로그" in part_strip or "네이버 블로그" in part_strip:
            blog_post = part_strip.split("]", 1)[-1].strip() if "]" in part_strip else part_strip
        # 인스타그램 릴스 감지
        elif "2. 인스타그램 릴스" in part_strip or "인스타그램 릴스" in part_strip:
            instagram_reels = part_strip.split("]", 1)[-1].strip() if "]" in part_strip else part_strip
        # 유튜브 쇼츠 감지
        elif "3. 유튜브 쇼츠" in part_strip or "유튜브 쇼츠" in part_strip:
            youtube_shorts = part_strip.split("]", 1)[-1].strip() if "]" in part_strip else part_strip
            
    # 파싱이 안 되었을 경우의 예외 방지용 백업
    if not blog_post and not instagram_reels and not youtube_shorts:
        blog_post = text
        
    return blog_post, instagram_reels, youtube_shorts

# Windows 콘솔 인코딩 에러 방지 (한글 및 특수문자 출력 안정화)
sys.stdout.reconfigure(encoding='utf-8')

# .env 파일에서 환경 변수(API 키 등) 로드
load_dotenv()

# ==========================================
# ⚙️ 스케줄러 설정 (원하는 시간으로 변경 가능)
# ==========================================
TARGET_TIME = "09:00"  # 매일 아침 09시 실행
# ==========================================

def run_daily_marketing_automation():
    """
    매일 지정된 시간에 뉴스를 수집하고, 
    최신 뉴스를 바탕으로 AI 마케팅 콘텐츠 3종 세트를 생성 및 텍스트 파일로 저장합니다.
    """
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n[⏳ {current_time_str}] 매일 자동 마케팅 자동화 프로세스를 시작합니다!")
    
    # ---------------------------------------------
    # 1단계: 실시간 뉴스 수집 및 엑셀 저장
    # ---------------------------------------------
    keywords = ["중소기업 AI 도입", "중소기업 디지털 전환"]
    all_collected_news = []
    
    print(f"[1단계] 실시간 뉴스 수집 중... (키워드: {', '.join(keywords)})")
    for kw in keywords:
        news_list, source = get_latest_news(kw, limit=10)
        if news_list:
            for idx, news in enumerate(news_list, 1):
                all_collected_news.append({
                    "검색키워드": kw,
                    "순위": idx,
                    "출처": source,
                    "뉴스제목": news['title'],
                    "링크": news['link'],
                    "수집일시": current_time_str
                })
                
    if not all_collected_news:
        print("[⚠️ 경고] 수집된 뉴스 데이터가 없어 오늘의 자동화 작업을 중단합니다.")
        return
        
    # data/ 폴더가 없을 경우 생성
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(all_collected_news)
    
    # 엑셀 파일 저장 및 동기화
    excel_date_path = f"data/naver_google_news_{current_date_str}.xlsx"
    excel_sync_path = "data/naver_news.xlsx"
    
    try:
        df.to_excel(excel_date_path, index=False)
        df.to_excel(excel_sync_path, index=False)
        print(f"✅ [엑셀 저장 완료] 뉴스 데이터가 '{excel_sync_path}' 및 '{excel_date_path}'에 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"[❌ 에러] 엑셀 저장 중 오류 발생: {e}")
        return

    # ---------------------------------------------
    # 2단계: 최신 기사 1위를 소스로 AI 멀티 콘텐츠 제작
    # ---------------------------------------------
    print("[2단계] 수집된 뉴스 중 최신 1위 기사로 AI 마케팅 콘텐츠 3종을 생성합니다.")
    
    # 수집 리스트의 첫 번째 기사를 가져옵니다.
    top_news = all_collected_news[0]
    top_title = top_news["뉴스제목"]
    top_link = top_news["링크"]
    
    print(f"👉 대상 기사 제목: '{top_title}'")
    
    # Gemini를 활용한 고밀도 3대 플랫폼 마케팅 콘텐츠 세트 생성
    multi_content = generate_multi_content(top_title, top_link)
    
    if not multi_content:
        print("[❌ 에러] AI 마케팅 문구 생성에 실패했습니다.")
        return
        
    # ---------------------------------------------
    # 3단계: 생성된 콘텐츠 팩 데이터베이스(DB) 및 텍스트 파일 저장
    # ---------------------------------------------
    # DB 저장 연동
    blog_post, instagram_reels, youtube_shorts = parse_multi_content(multi_content)
    insert_marketing_history(current_date_str, top_title, blog_post, instagram_reels, youtube_shorts)
    
    txt_filename = f"data/marketing_content_{current_date_str}.txt"
    try:
        with open(txt_filename, "w", encoding="utf-8") as f:
            f.write(f"====================================================\n")
            f.write(f"📅 생성 일시: {current_time_str}\n")
            f.write(f"📰 기반 뉴스 기사: {top_title}\n")
            f.write(f"🔗 기사 링크: {top_link if top_link else '링크 없음'}\n")
            f.write(f"====================================================\n\n")
            f.write(multi_content)
            
        print(f"🎉 [자동화 완료] 오늘의 3대 플랫폼 마케팅 콘텐츠 세트가 성공적으로 저장되었습니다!")
        print(f"   📂 텍스트 파일 경로: {txt_filename}\n")
    except Exception as e:
        print(f"[❌ 에러] 결과 텍스트 파일 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    print("=" * 75)
    print("⏰ SME AI 마케팅 스케줄러 자동 제어판 가동")
    print(f"   - 매일 아침 [{TARGET_TIME}] 자동 실행 대기 중")
    print("   - (안정성 검증을 위해 실행 즉시 최초 1회 테스트 구동을 진행합니다.)")
    print("=" * 75)
    
    # 스케줄러 기동 시, 바로 잘 작동하는지 1회 사전 테스트 실행
    run_daily_marketing_automation()
    
    # 매일 지정된 시간에 자동 실행되도록 스케줄 등록
    schedule.every().day.at(TARGET_TIME).do(run_daily_marketing_automation)
    
    # 무한 루프로 돌며 스케줄 감시
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏰ 스케줄러가 사용자에 의해 종료되었습니다.")
