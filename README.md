# Industrial Energy Intelligence Platform

특강용 **LLM + RAG + Agentic AI + 산업 에너지 관리** 데모입니다. 모든 공정 데이터는 synthetic이며, 실제 설비 제어를 수행하지 않습니다.

## 포함 기능
- Dark industrial operations dashboard
- 클릭/시나리오 기반 설비 이상 시각화
- Chiller equipment zoom + trend chart
- 로컬 문서 기반 RAG evidence 화면
- Agent workflow 표시
- OpenAI API 연결 시 AI Copilot, API 없이도 deterministic demo mode
- Chiller efficiency / compressor air leak / peak demand 시나리오

## 로컬 실행
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## OpenAI API 연결(선택)
`.streamlit/secrets.toml` 파일을 만들고 아래처럼 저장합니다. 이 파일은 `.gitignore`에 포함되어 GitHub에 올라가지 않습니다.
```toml
OPENAI_API_KEY="YOUR_KEY_HERE"
```
API가 없어도 강의용 Demo Mode는 작동합니다.

## GitHub → Streamlit Community Cloud 배포
1. GitHub에서 새 repository 생성
2. 이 폴더의 **내용물 전체**를 repository root에 업로드
3. Streamlit Community Cloud에서 `Create app` → GitHub repository 선택
4. Main file path: `app.py`
5. Deploy
6. OpenAI 기능을 쓸 경우 Streamlit app Settings → Secrets에 `OPENAI_API_KEY="..."` 추가

## 추천 특강 시연 순서
1. `Normal operation`으로 정상 공정 설명
2. `Chiller efficiency drop` 선택
3. Digital Factory에서 Chiller alert 확인
4. Equipment zoom에서 전력/COP 변화 설명
5. RAG evidence에서 기술문서 검색 과정 설명
6. AI Copilot에서 `왜 칠러 전력 사용량이 증가했어?` 실행
7. Agent workflow → 원인 후보 → 점검 권고 → 회피 가능 부하 연결

## 주의
이 프로젝트는 교육/시연용 prototype입니다. 이상 원인과 절감량은 synthetic scenario에 맞춘 데모 결과이며 실제 공장의 안전·운전·정비 의사결정에 사용하면 안 됩니다.
