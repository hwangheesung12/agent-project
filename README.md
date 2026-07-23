# * 메디톡톡 * ( https://meditalk.streamlit.app/ )

PubMed 논문을 수집하고 연도별 연구 동향과 상위 저널을 분석하는 Streamlit
대시보드입니다. Google 로그인을 완료한 사용자만 대시보드에 접근할 수 있습니다.

## 설치 및 실행

1. 의존성을 설치합니다.

   ```powershell
   pip install -r requirements.txt
   ```

2. `.env.example`을 `.env`로 복사하고 NCBI API 정보를 입력합니다.

3. `.streamlit/secrets.toml.example`을 `.streamlit/secrets.toml`로 복사하고
   Google OAuth 클라이언트 정보를 입력합니다.

   ```toml
   [auth]
   redirect_uri = "http://localhost:8501/oauth2callback"
   cookie_secret = "충분히 긴 무작위 문자열"
   client_id = "Google OAuth Client ID"
   client_secret = "Google OAuth Client Secret"
   server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
   ```

4. Google Cloud Console의 OAuth 웹 클라이언트에 다음 승인된 리디렉션 URI를
   정확히 등록합니다.

   ```text
   http://localhost:8501/oauth2callback
   ```

5. 앱을 실행합니다.

   ```powershell
   streamlit run app.py
   ```

배포 환경에서는 `redirect_uri`를 실제 HTTPS 서비스 주소의
`/oauth2callback`으로 변경하고 Google Cloud Console에도 동일하게 등록해야 합니다.
