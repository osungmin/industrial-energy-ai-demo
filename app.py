import os, re, time
from pathlib import Path
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st

ROOT=Path(__file__).parent
st.set_page_config(page_title='산업 에너지 AI 관제센터', page_icon='⚡', layout='wide')

st.markdown('''<style>
.block-container{padding-top:1.3rem;max-width:1500px}.metric-card{background:linear-gradient(145deg,#0c1a2b,#0a1422);border:1px solid #1c3850;border-radius:14px;padding:16px;box-shadow:0 8px 30px #0005}.eyebrow{font-size:.72rem;letter-spacing:.18em;color:#6f91aa}.big{font-size:1.75rem;font-weight:700}.ok{color:#45e0a8}.warn{color:#ffbd59}.bad{color:#ff667a}.equip{border:1px solid #24445d;border-radius:14px;padding:18px;text-align:center;background:#0b1827}.agent{border-left:3px solid #00d4ff;padding-left:14px}.small{color:#8aa5b9;font-size:.82rem}</style>''',unsafe_allow_html=True)

df=pd.read_csv(ROOT/'data/factory_energy.csv',parse_dates=['timestamp'])
scenario=st.sidebar.radio('시연 시나리오',['정상 운전','냉동기 효율 저하','압축공기 누설','최대전력 발생'],index=1)
st.sidebar.caption('합성데이터 기반 교육용 프로토타입')
st.sidebar.divider()
st.sidebar.markdown('### AI 기능 제어')
llm_on=st.sidebar.toggle('LLM 해석',value=False,help='센서와 경보를 자연어로 해석합니다.')
rag_on=st.sidebar.toggle('RAG 기술지식 연결',value=False,help='사내 매뉴얼과 지침을 검색해 근거를 연결합니다.')
agent_on=st.sidebar.toggle('Agentic AI 자율진단',value=False,help='목표를 받고 데이터·RAG·계산 도구를 순차적으로 실행합니다.')


view=df.tail(72).copy()
if scenario=='정상 운전':
    view['chiller_kw']-=np.where(np.arange(len(view))<42,34,0); view['compressor_kw']-=np.where((np.arange(len(view))>=44)&(np.arange(len(view))<60),27,0)
elif scenario=='압축공기 누설': view.loc[view.index[-24:],'compressor_kw']+=35
elif scenario=='최대전력 발생': view.loc[view.index[-8:-4],'other_kw']+=180
view['total_kw']=view[['compressor_kw','chiller_kw','boiler_kw','other_kw']].sum(axis=1)

st.markdown('<div class="eyebrow">INDUSTRIAL ENERGY AI / LIVE DEMO</div>',unsafe_allow_html=True)
st.title('산업 에너지 AI 관제센터')
st.caption('기존 EMS → LLM → RAG → Agentic AI 단계별 확장 데모')

st.markdown('#### AI 기능 활성화 상태')
cc1,cc2,cc3,cc4=st.columns(4)
for cc,name,on in [(cc1,'기존 EMS',True),(cc2,'LLM',llm_on),(cc3,'RAG',rag_on),(cc4,'Agentic AI',agent_on)]:
    cc.markdown(f'<div class="metric-card"><div class="eyebrow">{name}</div><div class="big {"ok" if on else ""}">● {"ON" if on else "OFF"}</div></div>',unsafe_allow_html=True)
st.markdown('### 1. 기존 EMS · 공정 모니터링')
c1,c2,c3,c4=st.columns(4)
metrics=[('공장 운영 상태','정상 가동','ok'),('현재 전력부하',f"{view.total_kw.iloc[-1]:,.0f} kW",''),('에너지 원단위',f"{(view.total_kw/view.production_kg_h).iloc[-1]:.3f} kWh/kg",''),('활성 경보','1' if scenario!='정상 운전' else '0','warn' if scenario!='정상 운전' else 'ok')]
for c,(a,b,cl) in zip([c1,c2,c3,c4],metrics): c.markdown(f'<div class="metric-card"><div class="eyebrow">{a}</div><div class="big {cl}">{b}</div></div>',unsafe_allow_html=True)

st.subheader('디지털 공정 현황')
a,b,c,d=st.columns(4)
alert={'냉동기 효율 저하':'냉동기 CH-501','압축공기 누설':'공기압축기 CMP-301','최대전력 발생':'MAIN BUS'}.get(scenario,'')
for col,name,sub in [(a,'보일러 BL-101','증기'),(b,'공기압축기 CMP-301','압축공기'),(c,'생산 공정','생산라인'),(d,'냉동기 CH-501','냉각')]:
    status='● 이상' if name==alert else '● 정상'; cls='bad' if name==alert else 'ok'
    col.markdown(f'<div class="equip"><div class="eyebrow">{sub.upper()}</div><h3>{name}</h3><div class="{cls}">{status}</div></div>',unsafe_allow_html=True)

left,right=st.columns([1.8,1])
with left:
    fig=go.Figure(); fig.add_trace(go.Scatter(x=view.timestamp,y=view.total_kw,name='공장 전력',fill='tozeroy')); fig.update_layout(height=330,margin=dict(l=10,r=10,t=25,b=10),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',legend_orientation='h')
    st.plotly_chart(fig,use_container_width=True)
with right:
    st.markdown('### AI 이상 감지')
    if scenario=='정상 운전': st.success('현재 주요 이상 징후가 없습니다.')
    elif scenario=='냉동기 효율 저하': st.error('냉동기 CH-501 · 효율 저하'); st.metric('이상 탐지 신뢰도','94.2%'); st.metric('예상 절감 가능 전력','31.4 kW')
    elif scenario=='압축공기 누설': st.error('공기압축기 CMP-301 · 비정상 기저부하'); st.metric('이상 탐지 신뢰도','91.7%'); st.metric('예상 절감 가능 전력','27.8 kW')
    else: st.error('MAIN BUS · 최대전력 초과 위험'); st.metric('최대전력 초과분','+180 kW'); st.metric('이상 탐지 신뢰도','96.1%')

st.markdown('### 2. AI 기능 확장 데모')
t1,t2,t3,t4=st.tabs(['LLM 해석','RAG 기술지식','Agentic AI 자율진단','AI Copilot'])
with t1:
    if not llm_on:
        st.warning('왼쪽 「LLM 해석」 스위치를 켜면 자연어 해석 기능이 활성화됩니다.')
    else:
        st.success('LLM 활성화: 센서 값과 경보를 자연어로 해석합니다.')
        if scenario=='냉동기 효율 저하': st.write('냉동기 CH-501에서 소비전력 증가와 COP 저하가 함께 나타나 단순 부하 증가보다 효율 저하 가능성이 높습니다.')
        elif scenario=='압축공기 누설': st.write('생산량 변화가 크지 않은 시간대에도 압축기 기저부하가 유지되어 누설 또는 불필요한 무부하 운전 가능성이 있습니다.')
        elif scenario=='최대전력 발생': st.write('여러 설비의 동시 운전으로 단시간 최대전력이 급증했습니다. 운전시점 분산 대상을 검토할 수 있습니다.')
        else: st.write('현재 주요 설비의 에너지 사용 패턴은 기준 운전범위 내에 있습니다.')
        st.caption('강의 포인트: LLM은 데이터를 설명하지만 사내 매뉴얼의 근거를 자동으로 갖고 있는 것은 아닙니다.')
with t2:
    if not rag_on:
        st.warning('왼쪽 「RAG 기술지식 연결」 스위치를 켜면 사내 기술문서 검색이 활성화됩니다.')
    else:
        docs=[(p.name,p.read_text(encoding='utf-8')) for p in (ROOT/'documents').glob('*.md')]
        q=st.text_input('기술지식 검색','냉동기 COP 저하 시 점검 항목')
        terms=set(re.findall(r'[A-Za-z가-힣]+',q.lower()))
        scored=sorted(((sum(t in txt.lower() for t in terms),name,txt) for name,txt in docs),reverse=True)
        for i,(score,name,txt) in enumerate(scored[:3],1):
            excerpt=next((x for x in txt.split('\n\n') if len(x)>60),txt)[:420]
            st.markdown(f'**{i}. {name}** · 관련도 {min(98,68+score*6)}%')
            st.caption(excerpt)
        st.info('RAG 기반 답변: 현재 운전 데이터와 검색된 기술문서를 함께 보면 냉각수 유량, 입출구 온도, 응축기 오염 상태, 센서 교정을 우선 확인하는 흐름이 적절합니다.')
        st.caption('강의 포인트: RAG는 조직의 문서에서 관련 근거를 검색해 LLM 답변에 문맥으로 제공합니다.')
with t3:
    if not agent_on:
        st.warning('왼쪽 「Agentic AI 자율진단」 스위치를 켜면 목표 기반 자율 조사 기능이 활성화됩니다.')
    else:
        goal=st.text_input('Agent에게 목표 부여','현재 공장의 에너지 손실 원인을 찾아 개선계획을 수립하라.')
        if st.button('AI 자율진단 실행',type='primary',use_container_width=True):
            steps=['계획 수립','DATA TOOL · 생산량/전력/센서 조회','ANOMALY TOOL · 이상 설비 탐색','EQUIPMENT TOOL · 상세 운전상태 확인','RAG TOOL · 매뉴얼/지침 검색','CALCULATOR · 절감량 계산','REPORT TOOL · 개선안 생성']
            prog=st.progress(0); box=st.empty(); done=[]
            for i,x in enumerate(steps,1):
                done.append(f'✓ {i}. {x}'); box.code('\n'.join(done)); prog.progress(i/len(steps)); time.sleep(.15)
            st.success('자율진단 완료')
            if scenario=='냉동기 효율 저하': st.markdown('**진단 결과**  \n대상: **냉동기 CH-501** · 우선 원인 후보: **응축기 열방출 성능 저하/오염** · 예상 절감 가능 전력: **31.4 kW**  \n권고: 냉각수 유량 → 응축기 접근온도 → 튜브/스트레이너 오염 → 센서 교정 순으로 점검')
            elif scenario=='압축공기 누설': st.markdown('**진단 결과**  \n대상: **CMP-301** · 우선 원인 후보: 누설 또는 무부하 운전 · 예상 절감 가능 전력: **27.8 kW**')
            elif scenario=='최대전력 발생': st.markdown('**진단 결과**  \n설비 동시기동에 따른 피크 증가 · 초과분 약 **180 kW** · 비핵심 설비 운전시점 분산 권고')
            else: st.markdown('**진단 결과**  \n현재 주요 이상 징후가 없어 예방점검 항목과 정상 기준선 유지 여부를 확인했습니다.')
        st.caption('강의 포인트: Agentic AI는 목표를 받고 DATA/RAG/계산/보고서 도구를 어떤 순서로 쓸지 계획하고 실행합니다.')
with t4:
    prompt=st.text_input('AI Copilot에게 질문','오늘 에너지 사용량이 증가한 이유와 우선 점검할 설비를 알려줘.')
    if st.button('질문하기'):
        if not llm_on: st.warning('LLM 해석을 먼저 켜주세요. 현재는 기존 EMS 모드입니다.')
        else:
            if scenario=='냉동기 효율 저하': ans='현재 계측 데이터 기준으로 냉동기 CH-501의 효율 저하가 가장 뚜렷합니다. 소비전력 증가와 COP 저하가 함께 나타납니다.'
            elif scenario=='압축공기 누설': ans='CMP-301의 비정상 기저부하가 주요 에너지 손실 후보입니다.'
            elif scenario=='최대전력 발생': ans='설비 동시 운전에 따른 최대전력 급증이 확인됩니다.'
            else: ans='현재 주요 이상 징후는 확인되지 않습니다.'
            if rag_on: ans+=' RAG가 활성화되어 관련 기술문서를 근거로 점검 순서를 함께 제시할 수 있습니다.'
            if agent_on: ans+=' Agentic AI를 실행하면 추가 데이터 조회, 문서 검색, 절감량 계산, 개선안 생성을 연속 수행할 수 있습니다.'
            st.write(ans)
st.divider(); st.caption('교육용 프로토타입 · 합성 센서 데이터 · 실제 현장 적용 전 엔지니어링 검증 필요')
