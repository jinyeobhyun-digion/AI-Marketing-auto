import streamlit as st
import os
import sys
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import shutil

# sys.path에 src 폴더 경로를 추가하여 모듈 참조 에러 방지
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawler import get_latest_news, save_to_excel
from generator import get_latest_news_file, read_news_titles, generate_multi_content

# Windows 콘솔 인코딩 에러 방지 (한글 및 특수문자 출력 안정화)
sys.stdout.reconfigure(encoding='utf-8')

# .env 로드
load_dotenv()

# Streamlit 페이지 설정
st.set_page_config(
    page_title="SME 고밀도 멀티 콘텐츠 팩 엔진 대시보드",
    page_icon="🚀",
    layout="wide"
)

# 메인 헤더
st.title("SME 마케팅 자동화: 고밀도 멀티 콘텐츠 팩 엔진 🚀")
st.markdown("40~60대 중소기업 대표님들을 위한 **실시간 뉴스 수집** 및 **3대 플랫폼 마케팅 콘텐츠 세트 일괄 생성** 대시보드입니다.")
st.markdown("---")

# 사이드바 설정 (API 키 상태 및 도움말)
st.sidebar.header("⚙️ 시스템 연결 상태")
api_key = os.getenv("GEMINI_API_KEY")
if api_key and "your_gemini_api_key" not in api_key:
    st.sidebar.success("✅ 구글 제미나이 API 연결됨")
    # API 키 일부 가려서 노출
    masked_key = f"{api_key[:6]}...{api_key[-4:]}" if len(api_key) > 10 else "연결 성공"
    st.sidebar.info(f"API Key: {masked_key}")
else:
    st.sidebar.error("❌ 구글 제미나이 API 미연결")
    st.sidebar.warning("프로젝트 폴더의 '.env' 파일에 GEMINI_API_KEY를 입력해 주세요.")

st.sidebar.markdown("""
---
### 💡 사용 방법 안내
1. **1단계: 실시간 뉴스 수집**
   - 아래 '뉴스 수집 시작' 버튼을 누르면 실시간 뉴스가 수집되어 `data/naver_news.xlsx`로 저장됩니다.
2. **2단계: 마케팅 콘텐츠 일괄 생성**
   - 셀렉트박스에서 원하는 기사를 선택합니다.
   - [🚀 3대 플랫폼 마케팅 콘텐츠 세트 생성 시작!] 버튼을 누르면 블로그 포스팅, 릴스 대본, 쇼츠 시나리오가 자동으로 한 번에 빌드됩니다.
""")

# 두 개의 컬럼 레이아웃 생성
col1, col2 = st.columns(2)

# 1단계: 실시간 뉴스 수집 및 동기화
with col1:
    st.header("📋 1단계: 실시간 뉴스 수집 및 동기화")
    st.markdown("최신 뉴스를 긁어와 `data/naver_news.xlsx` 파일로 자동 백업 및 동기화합니다.")
    
    keywords = ["중소기업 AI 도입", "중소기업 디지털 전환"]
    st.info(f"🔍 검색 대상 키워드: {', '.join([f'**{k}**' for k in keywords])}")
    
    if st.button("실시간 뉴스 수집 및 엑셀 저장 시작 🔍", use_container_width=True):
        with st.spinner("실시간 뉴스를 수집하고 있습니다. 잠시만 기다려 주세요..."):
            all_collected_news = []
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
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
                            "수집일시": current_time
                        })
            
            if all_collected_news:
                # data/ 폴더가 없을 경우 생성
                os.makedirs("data", exist_ok=True)
                df = pd.DataFrame(all_collected_news)
                
                # 파일 저장 (naver_google_news_오늘날짜.xlsx 및 naver_news.xlsx에 동시에 기록)
                today_str = datetime.now().strftime("%Y-%m-%d")
                df.to_excel(f"data/naver_google_news_{today_str}.xlsx", index=False)
                df.to_excel("data/naver_news.xlsx", index=False)
                
                st.success("🎉 뉴스 수집이 완료되었으며, data/naver_news.xlsx 파일이 동기화되었습니다!")
                
                # 표 형태로 결과 렌더링
                st.markdown("### 📰 실시간 뉴스 수집 목록")
                st.dataframe(
                    df[["검색키워드", "순위", "출처", "뉴스제목", "수집일시"]], 
                    use_container_width=True, 
                    hide_index=True
                )
            else:
                st.error("⚠️ 뉴스를 가져오는 데 실패했습니다. 네트워크 상태나 키워드를 점검해 주세요.")

# 2단계: 고밀도 멀티 콘텐츠 팩 생성
with col2:
    st.header("✍️ 2단계: 고밀도 멀티 콘텐츠 팩 생성")
    st.markdown("선택한 기사를 토대로 네이버 블로그 포스팅, 인스타그램 릴스 대본, 유튜브 쇼츠 시나리오를 일괄 생성합니다.")
    
    target_excel = "data/naver_news.xlsx"
    
    # 엑셀 파일이 존재하지 않는 경우를 대비한 자동 동기화 예외 처리
    if not os.path.exists(target_excel):
        latest_file = get_latest_news_file()
        if latest_file:
            os.makedirs("data", exist_ok=True)
            shutil.copy(latest_file, target_excel)
            st.info(f"💡 기존 수집된 최신 파일 `{os.path.basename(latest_file)}`을 `{target_excel}`로 가져왔습니다.")
            
    if os.path.exists(target_excel):
        try:
            news_df = pd.read_excel(target_excel)
            if not news_df.empty and "뉴스제목" in news_df.columns:
                # 엑셀의 뉴스 제목 리스트로 셀렉트박스 생성
                news_titles = news_df["뉴스제목"].tolist()
                
                selected_title = st.selectbox(
                    "💡 마케팅의 소스로 삼을 뉴스 기사를 선택해 주세요:",
                    options=news_titles,
                    index=0
                )
                
                # 선택한 뉴스의 링크 추출
                selected_row = news_df[news_df["뉴스제목"] == selected_title].iloc[0]
                selected_link = selected_row["링크"] if "링크" in news_df.columns else ""
                
                if selected_link:
                    st.markdown(f"🔗 **선택된 기사 링크:** [기사 읽기]({selected_link})")
                else:
                    st.write("🔗 원본 기사 링크가 존재하지 않습니다.")
                
                st.markdown("---")
                
                # 3대 플랫폼 콘텐츠 일괄 생성 버튼
                if st.button("🚀 3대 플랫폼 마케팅 콘텐츠 세트 생성 시작!", use_container_width=True):
                    if not api_key or "your_gemini_api_key" in api_key:
                        st.error("Gemini API 키가 입력되어 있지 않습니다. 사이드바의 안내에 따라 API 키를 설정해 주세요.")
                    else:
                        with st.spinner("제미나이 AI가 기사를 분석하여 3대 플랫폼 마케팅 콘텐츠 팩을 구축 중입니다..."):
                            multi_content = generate_multi_content(selected_title, selected_link)
                            
                            if multi_content:
                                st.success("✨ 네이버 블로그 포스팅, 인스타그램 릴스 대본, 유튜브 쇼츠 시나리오 3종 세트가 완성되었습니다!")
                                
                                # 성공 시 축하 풍선
                                st.balloons()
                                
                                # 복사용 큼직한 텍스트 영역 제공
                                st.markdown("### 📝 복사용 콘텐츠 텍스트")
                                st.text_area(
                                    "아래 텍스트 박스의 전체 내용(Ctrl+A)을 복사해서 마케팅 채널에 활용하세요.",
                                    value=multi_content,
                                    height=500
                                )
                                
                                # 미리보기 렌더링
                                st.markdown("### 👁️ 마케팅 콘텐츠 미리보기")
                                st.markdown(multi_content)
                            else:
                                st.error("AI 콘텐츠 생성 도중 API 호출 오류가 발생했습니다. 다시 시도해 주세요.")
            else:
                st.warning("⚠️ `data/naver_news.xlsx` 엑셀 파일 내에 수집된 뉴스 데이터가 없습니다.")
        except Exception as e:
            st.error(f"⚠️ 엑셀 데이터를 로드하는 중 오류가 발생했습니다: {e}")
    else:
        st.warning("⚠️ 수집된 뉴스 엑셀 파일(naver_news.xlsx)이 존재하지 않습니다. 먼저 1단계를 실행해 주세요.")
