# 메디톡톡

> PubMed 논문을 수집하고 연구 동향을 분석하는 의학 논문 인사이트 서비스

[배포 서비스 바로가기](https://meditalk.streamlit.app/)

메디톡톡은 사용자가 입력한 키워드와 연도 범위에 따라 PubMed 논문을 수집하고,
수집 결과를 연도 및 저널별로 시각화하는 Streamlit 기반 대시보드입니다.
Google 로그인을 완료한 사용자만 대시보드에 접근할 수 있습니다.

## 주요 기능

- 키워드와 출판 연도를 기준으로 PubMed 논문 수집
- PMID를 기준으로 중복 논문을 제외하고 SQLite에 저장
- 전체 논문 수, 신규 수집 수, 중복 수, 저널 수 요약
- 연도별 논문 수와 상위 저널 시각화
- 제목·초록·연도·저널 기반 논문 검색
- 검색 결과 CSV 다운로드
- 사용자별 챗봇 대화 내역 저장
- 개인 의료 조언 및 진단 요청 차단
- Google OAuth 로그인 및 사용자 인증

## 구현 결과

아래 경로에 캡처 이미지를 추가한 뒤 주석을 해제하면 README에 바로 표시됩니다.

```text
docs/
└── images/
    ├── landing.png
    ├── dashboard.png
    ├── papers.png
    └── chatbot.png
```

<!-- 캡처 이미지를 추가한 뒤 아래 주석을 해제하세요.

### 랜딩 및 로그인

![메디톡톡 랜딩 및 로그인 화면](docs/images/landing.png)

### 연구 동향 대시보드

![메디톡톡 연구 동향 대시보드](docs/images/dashboard.png)

### 논문 검색

![메디톡톡 논문 검색 화면](docs/images/papers.png)

### 챗봇

![메디톡톡 챗봇 화면](docs/images/chatbot.png)

-->

## 기술 스택

| 구분 | 기술 | 사용 목적 |
| --- | --- | --- |
| Language | Python 3.11 | 애플리케이션 및 데이터 처리 로직 |
| Web UI | Streamlit 1.59.2 | 로그인 화면과 대시보드 구성 |
| Visualization | Altair 6.2.2 | 연도별 논문 수와 상위 저널 시각화 |
| Database | SQLite | 논문 정보와 사용자별 채팅 내역 저장 |
| External API | NCBI PubMed E-utilities | 논문 PMID 검색 및 메타데이터 수집 |
| Authentication | Streamlit OIDC · Google OAuth | 사용자 로그인과 접근 제어 |
| Testing | unittest · Streamlit AppTest | 데이터 처리 및 화면 동작 검증 |
| Development | Dev Containers | Python 및 개발 도구 환경 표준화 |
| Deployment | Streamlit Community Cloud | 웹 애플리케이션 배포 |

## 프로젝트 구조

```text
agent-project/
├── .devcontainer/
│   └── devcontainer.json          # Python 3.11 개발 컨테이너 설정
├── .streamlit/
│   └── secrets.toml.example       # Google OAuth 설정 예시
├── views/
│   ├── __init__.py
│   ├── chat.py                    # 챗봇과 사용자별 대화 내역
│   ├── dashboard.py               # 대시보드 레이아웃과 논문 수집 제어
│   ├── landing.py                 # 로그인 전 랜딩 화면
│   ├── overview.py                # 통계 지표와 차트
│   ├── papers.py                  # 논문 검색, 필터링 및 CSV 저장
│   └── theme.py                   # 공통 UI 테마
├── .env.example                   # NCBI API 및 DB 환경 변수 예시
├── app.py                         # 애플리케이션 진입점과 인증 처리
├── pubmed.py                      # PubMed API, XML 파싱 및 SQLite 처리
├── requirements.txt               # Python 의존성
├── test_chat.py                   # 챗봇 단위 테스트
├── test_dashboard.py              # Streamlit 화면 테스트
├── test_pubmed.py                 # PubMed 및 DB 단위 테스트
└── README.md
```

> 캡처 이미지를 추가하면 `docs/images/`도 위 구조에 포함해 주세요.

## 동작 흐름

```text
Google 로그인
    ↓
검색어·연도·수집 개수 입력
    ↓
PubMed E-utilities 호출
    ↓
논문 XML 파싱 및 중복 검사
    ↓
SQLite 저장
    ↓
통계·차트·논문 목록·챗봇 제공
```

## 팀 구성 및 역할

Git 커밋 이력을 기준으로 주요 구현 영역을 정리했습니다.

| 팀원 | 역할 | 주요 담당 |
| --- | --- | --- |
| 김준 | 데이터·대시보드 개발 | PubMed API 연동, 논문 수집 및 DB 저장, 개요 화면, 랜딩 페이지, 전반적인 UI 개선 |
| 황희성 | 서비스 기능·개발 환경 | 프로젝트 초기 구성, 논문 필터, 챗봇, Dev Container 설정 |

## 구현 시 고려했던 점

> 이 섹션은 팀에서 직접 작성해 주세요.

- **데이터 수집:** <!-- PubMed API 요청 제한, 실패 처리 등을 작성 -->
- **데이터 정합성:** <!-- PMID 중복 처리, 누락 데이터 처리 등을 작성 -->
- **사용자 경험:** <!-- 검색 흐름, 대시보드 구성 등을 작성 -->
- **보안 및 개인정보:** <!-- OAuth 비밀 값, 의료 조언 제한 등을 작성 -->

## 구현 중 어려웠던 점

> 이 섹션은 팀에서 직접 작성해 주세요.

- **문제 상황:** <!-- 어떤 문제가 발생했는지 작성 -->
  - 원인:
  - 해결 과정:
  - 결과:
- **문제 상황:** <!-- 필요한 만큼 항목을 복사해서 작성 -->
  - 원인:
  - 해결 과정:
  - 결과:

## 설치 및 실행

### 1. 가상환경과 의존성 준비

`uv`를 사용하는 경우:

```powershell
uv venv
uv pip install -r requirements.txt
```

가상환경을 활성화하려면 다음 명령을 실행합니다.

```powershell
.venv\Scripts\Activate.ps1
```

### 2. 환경 변수 설정

`.env.example`을 `.env`로 복사하고 NCBI 정보를 입력합니다.

```dotenv
NCBI_API_KEY=your_ncbi_api_key_here
NCBI_EMAIL=your_email@example.com
PUBMED_DB_PATH=pubmed.db
```

### 3. Google OAuth 설정

`.streamlit/secrets.toml.example`을 `.streamlit/secrets.toml`로 복사하고
Google OAuth 웹 클라이언트 정보를 입력합니다.

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "충분히 긴 무작위 문자열"
client_id = "Google OAuth Client ID"
client_secret = "Google OAuth Client Secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

Google Cloud Console의 승인된 리디렉션 URI에도 아래 주소를 정확히 등록해야
합니다.

```text
http://localhost:8501/oauth2callback
```

배포 환경에서는 `redirect_uri`를 실제 HTTPS 서비스 주소의
`/oauth2callback`으로 변경하고 Google Cloud Console에도 동일하게 등록합니다.

### 4. 애플리케이션 실행

```powershell
uv run streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속합니다.

## 테스트

```powershell
uv run python -m unittest discover -p "test_*.py"
```
