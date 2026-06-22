import os
import json
import holidays
import feedparser
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
import re


def get_fetch_days():
    """평일 기준으로 데이터 수집 일수 계산"""
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).date()

    kr_holidays = holidays.KR()
    labor_day = datetime(today.year, 5, 1).date()

    def check_is_holiday(dt):
        return dt.weekday() >= 5 or dt in kr_holidays or dt == labor_day

    if check_is_holiday(today):
        return None

    fetch_days = 1
    check_date = today - timedelta(days=1)
    while check_is_holiday(check_date):
        fetch_days += 1
        check_date -= timedelta(days=1)

    return fetch_days


def calculate_similarity(text1, text2):
    """두 텍스트의 유사도 계산 (0~1)"""
    return SequenceMatcher(None, text1, text2).ratio()


def clean_html(text):
    """HTML 태그 제거"""
    if not text:
        return ""
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text(strip=True)


def extract_source_from_url(url):
    """URL에서 언론사 추출"""
    try:
        match = re.search(r'https?://(?:www\.)?([^/]+)', url)
        if match:
            domain = match.group(1)
            # 주요 언론사 매핑
            source_map = {
                'chosun.com': '조선일보',
                'joongang.co.kr': '중앙일보',
                'donga.com': '동아일보',
                'hankyung.com': '한국경제',
                'mk.co.kr': '매일경제',
                'sedaily.com': '서울경제',
                'edaily.co.kr': '이데일리',
                'yonhapnews.co.kr': '연합뉴스',
                'yna.co.kr': '연합뉴스',
                'ajunews.com': '아주경제',
                'newspim.com': '뉴스핌',
                'fss.or.kr': '금융감독원',
                'kfb.or.kr': '금융정보원',
                'mt.co.kr': '머니투데이',
                'news1.kr': '뉴스1',
                'newsis.com': '뉴시스'
            }
            for key, value in source_map.items():
                if key in domain:
                    return value
            return domain
        return '기타'
    except:
        return '기타'


def get_google_news_rss(keyword, days_to_fetch):
    """Google News RSS로 뉴스 수집"""
    news_items = []

    try:
        # Google News RSS URL
        url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"

        print(f"  🔎 키워드: {keyword}")
        feed = feedparser.parse(url)

        kst = timezone(timedelta(hours=9))
        search_limit = datetime.now(kst) - timedelta(days=days_to_fetch)

        for entry in feed.entries[:30]:  # 최대 30개
            try:
                title = clean_html(entry.get('title', ''))
                desc = clean_html(entry.get('summary', ''))
                link = entry.get('link', '')

                # 발행일 파싱
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    pub_date = pub_date.astimezone(kst)
                else:
                    # 발행일이 없으면 현재 시각 사용
                    pub_date = datetime.now(kst)

                # 날짜 필터링 (전일자 기준)
                if pub_date < search_limit:
                    continue

                # 언론사 추출
                source = extract_source_from_url(link)

                news_items.append({
                    'title': title,
                    'desc': desc,
                    'link': link,
                    'pub_date': pub_date,
                    'source': source,
                    'score': 0
                })
            except Exception as e:
                print(f"    ⚠️ 항목 파싱 오류: {e}")
                continue

        print(f"    ✓ {len(news_items)}개 수집")
        return news_items

    except Exception as e:
        print(f"    ❌ RSS 피드 오류: {e}")
        return []


def remove_duplicates(news_list, similarity_threshold=0.7):
    """유사도 기반 중복 제거 + 메이저 언론사 우선"""
    major_sources = [
        '조선일보', '중앙일보', '동아일보', '한국경제', '매일경제',
        '연합뉴스', '서울경제', '이데일리', '아주경제', '뉴스핌',
        '금융감독원', '금융정보원', '머니투데이', '뉴스1', '뉴시스'
    ]

    def is_major_source(source):
        return source in major_sources

    unique_news = []

    for news in news_list:
        is_duplicate = False
        news_text = news['title'][:100]

        for existing in unique_news:
            existing_text = existing['title'][:100]
            similarity = calculate_similarity(news_text, existing_text)

            if similarity > similarity_threshold:
                is_duplicate = True

                # 메이저 언론사 우선 선택
                if is_major_source(news['source']) and not is_major_source(existing['source']):
                    unique_news.remove(existing)
                    unique_news.append(news)
                elif news['source'] in ['금융감독원', '금융정보원']:
                    # 공식 보도자료는 항상 우선
                    unique_news.remove(existing)
                    unique_news.append(news)

                break

        if not is_duplicate:
            unique_news.append(news)

    return unique_news


def save_news_json(news_by_category, date_str):
    """JSON 파일로 저장"""
    os.makedirs('docs/data', exist_ok=True)

    with open(f'docs/data/{date_str}.json', 'w', encoding='utf-8') as f:
        json.dump(news_by_category, f, ensure_ascii=False, indent=2)

    index_path = 'docs/data/index.json'
    if os.path.exists(index_path):
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                index = json.loads(content) if content else []
        except (json.JSONDecodeError, ValueError):
            print(f"⚠️  index.json 파싱 오류, 빈 배열로 초기화합니다.")
            index = []
    else:
        index = []

    if date_str not in index:
        index.append(date_str)
        index.sort(reverse=True)

    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False)

    print(f"✅ JSON 저장 완료: docs/data/{date_str}.json")


if __name__ == "__main__":
    days_to_fetch = get_fetch_days()

    kst = timezone(timedelta(hours=9))
    date_str = datetime.now(kst).strftime('%Y-%m-%d')

    if days_to_fetch is None:
        print("🚩 오늘은 한국 공휴일 또는 주말입니다. 배치를 종료합니다.")
        exit()

    print(f"🔍 최근 {days_to_fetch}일치 데이터를 수집합니다. (전일자 기준)")

    # 카테고리별 키워드 및 점수
    categories = {
        "🏛️ 금융감독 및 규제": {
            "keywords": {
                "금융감독원": 5, "금감원": 5, "금융위원회": 5, "금융위": 4,
                "금융당국": 3, "금감원 검사": 5, "금융감독원 검사": 5,
                "금감원 제재": 4, "과징금": 3, "과태료": 3,
                "금융위원장": 2, "금감원장": 2, "금융규제": 3
            }
        },
        "🏢 여신업계 및 캐피탈": {
            "keywords": {
                "현대캐피탈": 5, "캐피탈업계": 4, "여신전문금융": 4,
                "여전업계": 4, "여전업권": 3, "캐피탈사": 3,
                "신용카드": 2, "할부금융": 3, "리스": 2, "캐피탈": 2
            }
        },
        "🔒 소비자보호 및 정보보안": {
            "keywords": {
                "소비자보호": 5, "개인정보보호": 4, "신용정보보호": 4,
                "정보보안": 4, "보안사고": 5, "유출사고": 5,
                "개인정보위": 3, "개보위": 3, "랜섬웨어": 3,
                "해킹": 3, "피싱": 3, "금융사기": 4
            }
        },
        "⚖️ 내부통제 및 컴플라이언스": {
            "keywords": {
                "내부통제": 5, "컴플라이언스": 4, "준법감시": 4,
                "금융사고": 4, "횡령": 4, "배임": 4,
                "내부감사": 4, "리스크관리": 3, "의무위반": 3,
                "감사": 2
            }
        },
        "🌏 해외법인 및 글로벌": {
            "keywords": {
                "해외법인": 5, "해외진출": 4, "글로벌": 2,
                "중국법인": 4, "베트남법인": 4, "인도법인": 4,
                "현지규제": 4, "해외규제": 4, "해외투자": 3
            }
        }
    }

    # 모든 키워드 수집
    all_keywords = set()
    for cat_data in categories.values():
        all_keywords.update(cat_data['keywords'].keys())

    print(f"\n📡 Google News RSS로 뉴스 수집 중...")
    print(f"   총 {len(all_keywords)}개 키워드")

    all_news = []

    # 키워드별 뉴스 수집
    for keyword in sorted(all_keywords):
        news = get_google_news_rss(keyword, days_to_fetch)
        all_news.extend(news)

    # 중복 제거 (유사도 50% 이상이면 중복으로 판단)
    print(f"\n📊 수집된 뉴스: {len(all_news)}개")
    unique_news = remove_duplicates(all_news, similarity_threshold=0.5)
    print(f"✨ 중복 제거 후: {len(unique_news)}개")

    # 카테고리별 분류 및 점수 계산
    news_by_category = {}

    for category_name, cat_data in categories.items():
        category_news = []

        for news in unique_news:
            check_text = (news['title'] + " " + news.get('desc', ''))[:200]
            total_score = 0
            matched_keywords = []

            for kw, kw_score in cat_data['keywords'].items():
                if kw in check_text:
                    total_score += kw_score
                    matched_keywords.append(f"{kw}({kw_score})")

            if total_score > 0:
                news['score'] = total_score
                news['matched_keywords'] = matched_keywords
                category_news.append(news)

        if category_news:
            # 점수 높은 순으로 정렬
            category_news.sort(key=lambda x: x['score'], reverse=True)
            # 상위 20개만 선택
            top_news = category_news[:20]

            # datetime 객체를 문자열로 변환
            for news in top_news:
                if isinstance(news.get('pub_date'), datetime):
                    news['pub_date'] = news['pub_date'].strftime('%Y-%m-%d %H:%M:%S')

            news_by_category[category_name] = top_news
            print(f"  ✓ {category_name}: {len(top_news)}건")

    # JSON 저장
    if news_by_category:
        save_news_json(news_by_category, date_str)
        print(f"\n✅ 총 {sum(len(v) for v in news_by_category.values())}건의 뉴스를 저장했습니다.")
    else:
        print("📭 수집된 뉴스가 없습니다.")
