# Design

## Source of truth
- Status: Active
- Last refreshed: 2026-07-23
- Primary product surfaces: Google 로그인 랜딩, PubMed 개요, 논문 목록, 챗봇, 수집 사이드바
- Evidence reviewed: `app.py`, `views/landing.py`, `views/dashboard.py`, `views/overview.py`, `views/papers.py`, `views/chat.py`, 사용자 제공 모바일 UI 참고 이미지

## Brand
- Personality: 친근하고 선명한 의료 연구 도우미, 가볍지만 신뢰감 있는 인상
- Trust signals: 명확한 통계 레이블, 일관된 데이터 표기, 차분한 청보라색 바탕
- Avoid: 과도한 장식, 강한 네온색, 의료 진단 서비스처럼 보이는 표현

## Product goals
- Goals: PubMed 수집과 연구 동향 확인을 빠르고 이해하기 쉽게 제공
- Non-goals: 의료 진단 또는 개인별 치료 지침 제공
- Success signals: 핵심 지표와 차트를 한 화면에서 파악하고 논문을 쉽게 필터링·내보낼 수 있음

## Personas and jobs
- Primary personas: 연구자, 의료·바이오 분야 학생, 문헌조사 담당자
- User jobs: 논문 수집, 기간별 추세 확인, 주요 저널 확인, 결과 검색 및 CSV 저장
- Key contexts of use: 데스크톱 중심, 태블릿과 모바일에서도 핵심 기능 접근

## Information architecture
- Primary navigation: 개요, 논문 목록, 챗봇 탭
- Core routes/screens: 로그인 랜딩과 인증 후 단일 대시보드
- Content hierarchy: 서비스 제목 → 탭 → 핵심 지표 → 조건 안내 → 차트/목록

## Design principles
- Principle 1: 깊이감은 카드와 입력 요소에만 사용하고 데이터 자체는 선명하게 유지
- Principle 2: 보라색은 주요 행동과 선택 상태에 집중
- Tradeoffs: 장식적 클레이 효과보다 표 가독성과 차트 비교 가능성을 우선

## Visual language
- Color: 밝은 청보라 배경, 딥 퍼플 주요색, 라벤더 보조색, 진한 남보라 텍스트
- Typography: 시스템 산세리프, 굵은 제목과 안정적인 본문 행간
- Spacing/layout rhythm: 8px 기반, 카드 간 16~24px
- Shape/radius/elevation: 16~28px 둥근 모서리, 부드러운 외부 그림자와 약한 내부 하이라이트
- Motion: 짧은 hover/press 이동만 사용
- Imagery/iconography: 장식은 추상 보라색 형태로 제한하고 기능 아이콘은 단순하게 유지

## Components
- Existing components to reuse: Streamlit metric, tabs, forms, dataframe, Altair charts
- New/changed components: 대시보드 헤더, 통일된 카드 토큰, 명시적 논문 표 열 구성
- Variants and states: primary, hover, active, disabled, empty, error, success
- Token/component ownership: 공통 토큰과 상태 스타일은 `views/theme.py`

## Accessibility
- Target standard: WCAG 2.1 AA 수준의 대비와 키보드 접근성 지향
- Keyboard/focus behavior: 입력·버튼·탭에 명확한 focus outline 제공
- Contrast/readability: 본문은 진한 남보라, 연한 배경 위 회색 본문 사용 제한
- Screen-reader semantics: Streamlit 기본 제목, 탭, 폼 의미 구조 유지
- Reduced motion and sensory considerations: reduced-motion 환경에서 전환 제거

## Responsive behavior
- Supported breakpoints/devices: 데스크톱, 태블릿, 760px 이하 모바일
- Layout adaptations: 지표와 차트는 Streamlit 열 래핑을 따르고 모바일에서 여백·반경 축소
- Touch/hover differences: 버튼 최소 높이 48px, hover 효과는 보조 피드백으로만 사용

## Interaction states
- Loading: Streamlit spinner와 상태 문구
- Empty: 다음 행동을 알려주는 정보 카드
- Error: 오류 원인을 포함한 경고 카드
- Success: 신규·중복·실패 건수를 포함한 완료 메시지
- Disabled: 낮은 대비의 비활성 버튼과 설정 안내
- Offline/slow network, if applicable: PubMed 요청 중 spinner 유지, 오류 메시지 표시

## Content voice
- Tone: 간결하고 친절한 한국어
- Terminology: 논문, 저널, 신규 수집, 중복 제외
- Microcopy rules: 한 문장에 한 행동, 수량에는 단위를 명시

## Implementation constraints
- Framework/styling system: Streamlit과 주입형 CSS, Altair
- Design-token constraints: `--clay-*` CSS 변수 재사용
- Performance constraints: 데이터 전체를 HTML로 재구현하지 않고 `st.dataframe` 유지
- Compatibility constraints: Streamlit 1.59 이상
- Test/screenshot expectations: AppTest 기능 검증, 인증 없이 랜딩 화면 렌더링 가능

## Open questions
- [ ] 실제 배포 화면에서 사용할 브랜드 로고 또는 캐릭터 자산 제공 여부 / 제품 담당자 / 랜딩 시각 완성도
