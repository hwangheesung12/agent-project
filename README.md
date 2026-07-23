# PubMed Insight Dashboard

Streamlit 화면에서 검색 조건을 입력하면 PubMed PMID와 논문 제목, 초록, 저널,
출판 연도, 저자를 수집해 SQLite의 `pubmed_records` 테이블에 저장합니다.

## 실행

1. `.env.example`을 `.env`로 복사하고 `NCBI_API_KEY`, `NCBI_EMAIL` 값을 입력합니다.
2. 의존성을 설치합니다: `pip install -r requirements.txt`
3. 앱을 실행합니다: `streamlit run app.py`

API Key가 없어도 PubMed 요청은 가능하지만, NCBI 요청 제한이 더 낮습니다.
이미 저장된 PMID는 기본키 중복으로 판단해 건너뜁니다.
