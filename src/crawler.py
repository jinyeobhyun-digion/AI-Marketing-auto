import os
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import urllib.parse
import sys
from datetime import datetime
import pandas as pd

# Windows 콘솔 인코딩 에러 방지 (한글 및 특수문자 출력 안정화)
sys.stdout.reconfigure(encoding='utf-8')

def fetch_naver_news(query, limit=10):
    """
    네이버 뉴스 검색을 직접 시도합니다. (봇 차단/CAPTCHA 감지 시 빈 리스트 반환)
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://search.naver.com/search.naver?where=news&query={encoded_query}&sm=tab_srt&sort=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 네이버의 봇 차단(CAPTCHA 또는 로그인 리다이렉션) 감지 시 백업 시스템으로 전환
        if "captcha" in response.text.lower() or "nid.naver.com" in response.text.lower():
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        news_titles = soup.select("a.news_tit")
        
        results = []
        for item in news_titles[:limit]:
            title = item.get_text(strip=True)
            link = item.get('href')
            results.append({"title": title, "link": link})
            
        return results
    except Exception:
        return []

def fetch_google_news_rss(query, limit=10):
    """
    네이버 뉴스 봇 감지 시 구글 뉴스 RSS 피드를 활용해 최신 뉴스를 100% 안정적으로 가져옵니다.
    """
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        results = []
        for item in items[:limit]:
            title_el = item.find('title')
            link_el = item.find('link')
            title = title_el.text if title_el is not None else "제목 없음"
            
            # 구글 뉴스 제목 포맷("기사 제목 - 언론사")에서 뒷부분 언론사명 제거
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
                
            link = link_el.text if link_el is not None else ""
            results.append({"title": title, "link": link})
            
        return results
    except Exception as e:
        print(f"[⚠️ 백업 뉴스 시스템 작동 오류] {e}")
        return []

def get_latest_news(query, limit=10):
    """
    네이버 뉴스 검색을 우선 시도하고, 봇 탐지 시 안전하게 구글 뉴스 RSS로 백업 전환합니다.
    """
    # 1. 네이버 뉴스 검색 시도
    news = fetch_naver_news(query, limit)
    if news:
        return news, "네이버 뉴스 (실시간 수집)"
        
    # 2. 실패 시 구글 뉴스 RSS 백업 시스템 작동
    news = fetch_google_news_rss(query, limit)
    if news:
        return news, "구글 뉴스 RSS (네이버 차단 우회 백업)"
        
    return [], None

def save_to_excel(all_news, output_dir="data"):
    """
    수집된 뉴스 데이터를 Pandas DataFrame으로 변환하여 엑셀 파일로 저장합니다.
    """
    if not all_news:
        print("\n[⚠️ 경고] 수집된 뉴스 데이터가 없어 엑셀 저장을 건너뜁니다.")
        return
        
    # data/ 폴더가 없을 경우 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    df = pd.DataFrame(all_news)
    
    # 오늘 날짜 구하기 (YYYY-MM-DD)
    today_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"naver_google_news_{today_str}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    try:
        df.to_excel(filepath, index=False)
        print(f"\n💾 [엑셀 저장 완료] 뉴스 수집 데이터가 성공적으로 저장되었습니다!")
        print(f"   📂 저장 경로: {filepath}")
    except Exception as e:
        print(f"\n❌ [엑셀 저장 실패] 파일 쓰기 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    keywords = ["중소기업 AI 도입", "중소기업 디지털 전환"]
    
    print("=" * 75)
    print("[NEWS] 실시간 최신 비즈니스 뉴스 크롤러 작동")
    print("=" * 75)
    
    all_collected_news = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for kw in keywords:
        print(f"\n🔍 검색 키워드: [{kw}] (최신 10개)")
        print("-" * 75)
        
        news_list, source = get_latest_news(kw, limit=10)
        
        if not news_list:
            print("   ⚠️ 실시간 뉴스를 가져오는 데 실패했습니다. 네트워크 상태를 확인해 주세요.")
        else:
            print(f"📌 [출처: {source}]")
            for idx, news in enumerate(news_list, 1):
                print(f"[{idx:2d}] {news['title']}")
                print(f"     URL: {news['link']}")
                
                # 엑셀 파일 기록을 위한 데이터 구조화
                all_collected_news.append({
                    "검색키워드": kw,
                    "순위": idx,
                    "출처": source,
                    "뉴스제목": news['title'],
                    "링크": news['link'],
                    "수집일시": current_time
                })
        print("-" * 75)
        
    # 수집한 뉴스 데이터를 엑셀 파일로 자동 저장
    save_to_excel(all_collected_news)
