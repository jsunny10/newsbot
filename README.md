# 금융감사 뉴스 수집 봇 📰

현대캐피탈 감사/소비자보호/정보보안 관련 뉴스 자동 수집 시스템

## 주요 기능

### 📊 뉴스 수집
- **Google News RSS**: 키워드 기반 검색 (API 키 불필요, 무료, 무제한)
- **전일자 기준**: 평일 전일, 주말 후 월요일은 금요일부터 수집
- **카테고리별 분류**:
  - 🏛️ 금융감독 및 규제
  - 🏢 여신업계 및 캐피탈
  - 🔒 소비자보호 및 정보보안
  - ⚖️ 내부통제 및 컴플라이언스
  - 🌏 해외법인 및 글로벌

### 🔍 중복 제거
- 유사도 분석 (70% 이상 유사 시 중복 처리)
- 메이저 언론사 우선 선택
- 공식 보도자료 우선순위 최상위

### 📅 자동 실행
- 매일 오전 8시 자동 실행 (GitHub Actions)
- 주말 및 공휴일 제외
- JSON 데이터 자동 저장
- GitHub Pages 자동 배포

### 🌐 웹 페이지
- 달력 UI로 날짜별 조회
- 카테고리별 접기/펼치기
- 언론사 표시
- 점수 및 키워드 표시

## 설정 방법

### 1. GitHub Pages 활성화
Repository Settings > Pages:
- Source: Deploy from a branch
- Branch: main
- Folder: /docs

### 2. 수동 실행
Actions 탭 > Daily News Collector > Run workflow

## 파일 구조

```
newsbot/
├── news_collector.py          # 뉴스 수집 메인 스크립트
├── requirements.txt            # Python 패키지
├── .github/workflows/
│   └── daily_news.yml         # GitHub Actions 워크플로우
└── docs/
    ├── index.html             # 웹 페이지
    └── data/
        ├── index.json         # 날짜 목록
        └── YYYY-MM-DD.json    # 일별 뉴스 데이터
```

## 기술 스택

- **Python 3.11**
- **feedparser**: RSS 피드 파싱
- **BeautifulSoup4**: HTML 정제
- **GitHub Actions**: 자동 실행
- **GitHub Pages**: 웹 호스팅

## 장점

- ✅ **완전 무료**: API 키 불필요
- ✅ **호출 제한 없음**: Google News RSS 무제한
- ✅ **간편한 유지보수**: Secrets 설정 불필요
- ✅ **다양한 언론사**: 조선, 중앙, 한경, 연합뉴스 등 자동 통합

## 라이선스

MIT License
