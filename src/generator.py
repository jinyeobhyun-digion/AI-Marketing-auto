import os
import glob
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from google import genai
import sys

# Windows 콘솔 인코딩 에러 방지 (한글 및 특수문자 출력 안정화)
sys.stdout.reconfigure(encoding='utf-8')

# .env 파일에서 환경 변수(API 키 등) 로드
load_dotenv()

def get_latest_news_file(data_dir="data"):
    """
    data/ 폴더에서 파일명이 naver_google_news_*.xlsx 패턴인 파일 중 가장 최근 파일을 찾습니다.
    """
    search_pattern = os.path.join(data_dir, "naver_google_news_*.xlsx")
    files = glob.glob(search_pattern)
    
    if not files:
        return None
        
    # 파일의 마지막 수정 시간을 기준으로 내림차순 정렬하여 가장 최신 파일 반환
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def read_news_titles(filepath):
    """
    엑셀 파일에서 '뉴스제목' 열을 읽어 리스트로 변환합니다.
    """
    try:
        df = pd.read_excel(filepath)
        if "뉴스제목" in df.columns:
            return df["뉴스제목"].tolist()
        else:
            print("[WARNING] 엑셀 파일에 '뉴스제목' 컬럼이 없습니다.")
            return []
    except Exception as e:
        print(f"[ERROR] 엑셀 파일을 읽는 중 오류 발생: {e}")
        return []

def generate_marketing_copy_gemini(news_titles):
    """
    Google Gemini API를 사용하여 대표님들을 위한 인스타그램 마케팅 문구 초안 3개를 생성합니다.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "your_gemini_api_key" in api_key:
        print("\n[INFO] 대표님, Gemini AI 문구를 생성하려면 구글 API 키가 필요합니다.")
        print("   1. 구글 AI 스튜디오(https://aistudio.google.com/)에서 무료 API 키를 발급받으세요.")
        print("   2. 프로젝트 폴더의 '.env' 파일에 'GEMINI_API_KEY=발급받은키' 형태로 입력해 주세요.")
        return None
        
    # 최신 google-genai SDK의 Client 초기화
    client = genai.Client(api_key=api_key)
    
    # AI에게 컨텍스트로 전달할 뉴스 제목 목록 구성 (최대 10개로 제한)
    news_context = "\n".join([f"- {title}" for title in news_titles[:10]])
    
    system_prompt = (
        "당신은 중소기업 대표님들을 밀착 케어하는 상냥하고 전문적인 AI 비즈니스 마케터입니다. "
        "주요 고객층은 AI 도입을 주저하고 두려워하는 40대부터 60대 중소기업 대표님들입니다."
    )
    
    user_prompt = f"""
{system_prompt}

최근 뉴스 트렌드를 녹여내어, AI 도입을 망설이는 40~60대 중소기업 대표님들의 공감과 행동을 이끌어낼 '상냥하고 전문적인 인스타그램 마케팅 문구 초안 3개'를 생성해 주세요.

[분석된 최근 뉴스 트렌드]
{news_context}

[작성 지침]
1. 친근하게 말을 걸면서도 격식과 품격을 갖춘 부드러운 경어체(~합니다, ~해요, 대표님)를 사용해 주세요.
2. 기술 용어를 과도하게 사용하지 않고, 40~60대 대표님들께서 직관적으로 이해할 수 있게 쉬운 단어로 풀어써 주세요.
3. AI가 거창한 것이 아니라, 바쁜 대표님들을 돕는 비서이며, 생산성을 개선해 실질적 매출 성장을 돕는 도구임을 소구해 주세요.
4. 인스타그램 플랫폼 특성에 어울리게 가독성 높은 줄바꿈과 어울리는 이모지를 적극적으로 활용해 주세요.
5. 각 초안 하단에는 관련 해시태그(예: #중소기업AI #디지털전환 #AI마케팅 #경영인사이트 #대표님고민 등)를 5개 이상 달아주세요.
6. 초안 1, 초안 2, 초안 3을 알아보기 쉽게 구분해 주세요.
"""

    import time
    
    print("\n[AI] 구글 제미나이(Gemini) 모델을 사용하여 인스타그램 마케팅 문구를 생성하고 있습니다...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # gemini-2.5-flash 모델 사용하여 콘텐츠 생성
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_prompt,
            )
            return response.text
        except Exception as e:
            # 일시적인 구글 무료 서버 부하(503) 감지 시 2초 대기 후 자동으로 재시도합니다.
            if "503" in str(e) and attempt < max_retries - 1:
                print(f"[AI] 구글 서버 혼잡 감지 (503). {attempt + 1}초 대기 후 재시도합니다...")
                time.sleep(3)
                continue
            print(f"[ERROR] Gemini API 호출 오류 발생: {e}")
            return None

if __name__ == "__main__":
    print("=" * 75)
    print("[AI] Gemini 기반 인스타그램 마케팅 카피 생성기 작동")
    print("=" * 75)
    
    # 1. 가장 최신의 뉴스 파일 찾기
    latest_file = get_latest_news_file()
    
    if not latest_file:
        print("\n[WARNING] data/ 폴더에 뉴스 엑셀 파일이 없습니다.")
        print("   먼저 'python src/crawler.py'를 실행하여 뉴스 수집을 진행해 주세요.")
    else:
        print(f"📂 대상 엑셀 파일: {latest_file}")
        
        # 2. 뉴스 제목 리스트업
        titles = read_news_titles(latest_file)
        print(f"📰 분석된 뉴스 타이틀: {len(titles)}개 수집됨")
        
        if titles:
            # 3. Gemini를 통한 문구 생성
            marketing_copy = generate_marketing_copy_gemini(titles)
            
            if marketing_copy:
                print("\n========================= 생성된 마케팅 카피 초안 3선 =========================")
                print(marketing_copy)
                print("=================================================================================")
