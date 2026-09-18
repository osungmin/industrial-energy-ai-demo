import json, os, re
from pathlib import Path
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st
ROOT=Path(__file__).parent
st.set_page_config(page_title='산업 에너지 AI 관제센터',page_icon='⚡',layout='wide')
st.markdown('''<style>.block-container{padding-top:1.2rem;max-width:1550px}.metric-card{background:linear-gradient(145deg,#0c1a2b,#0a1422);border:1px solid #1c3850;border-radius:14px;padding:15px}.eyebrow{font-size:.72rem;letter-spacing:.12em;color:#6f91aa}.big{font-size:1.55rem;font-weight:700}.ok{color:#45e0a8}.warn{color:#ffbd59}.bad{color:#ff667a}</style>''',unsafe_allow_html=True)
def secret(n,d=None):
    try:return st.secrets.get(n,d)
    except:return os.getenv(n,d)
API_KEY=secret('OPENAI_API_KEY'); MODEL=secret('OPENAI_MODEL','gpt-5.6-luna')
def client():
    if not API_KEY:return None
    from openai import OpenAI
    return OpenAI(api_key=API_KEY)
def llm(prompt,inst='당신은 산업 에너지 관리 AI입니다. 제공된 데이터에만 근거해 한국어로 간결하고 전문적으로 답하세요.'):
    r=client().responses.create(model=MODEL,instructions=inst,input=prompt,store=False); return r.output_text
@st.cache_data
def docs():return [(p.name,p.read_text(encoding='utf-8')) for p in sorted((ROOT/'documents').glob('*.md'))]
def tokens(s):return [x.lower() for x in re.findall(r'[A-Za-z0-9가-힣]+',s) if len(x)>1]
def retrieve(q,k=3):
    ts=tokens(q); rows=[]
    for name,txt in docs():
        for chunk in [c.strip() for c in re.split(r'\n(?=## )|\n\n+',txt) if len(c.strip())>30]:
            low=chunk.lower(); score=sum(low.count(t) for t in ts)
            if any(x in low for x in ['ch-501','cmp-301']) and any(x in q.lower() for x in ['ch-501','cmp-301']):score+=4
            rows.append((score,name,chunk))
    return sorted(rows,key=lambda x:x[0],reverse=True)[:k]
df=pd.read_csv(ROOT/'data/factory_energy.csv',parse_dates=['timestamp'])
scenario=st.sidebar.radio('시연 시나리오',['정상 운전','냉동기 효율 저하','압축공기 누설','최대전력 발생'],index=1)
mode=st.sidebar.radio('화면 모드',['강의 모드','실제 운영 모드'],horizontal=True)
st.sidebar.caption('합성 센서 데이터 기반 교육용 프로토타입')
llm_on=rag_on=agent_on=True
if mode=='강의 모드':
    st.sidebar.divider(); st.sidebar.markdown('### AI 기능 제어'); llm_on=st.sidebar.toggle('LLM 해석'); rag_on=st.sidebar.toggle('RAG 기술지식 연결'); agent_on=st.sidebar.toggle('Agentic AI 자율진단')
else:st.sidebar.info('운영 모드에서는 LLM · RAG · Agent 기능이 백그라운드에서 자동으로 사용됩니다.')
view=df.tail(72).copy()
if scenario=='정상 운전':view['chiller_kw']-=np.where(np.arange(len(view))<42,34,0);view['compressor_kw']-=np.where((np.arange(len(view))>=44)&(np.arange(len(view))<60),27,0)
elif scenario=='압축공기 누설':view.loc[view.index[-24:],'compressor_kw']+=35
elif scenario=='최대전력 발생':view.loc[view.index[-8:-4],'other_kw']+=180
view['total_kw']=view[['compressor_kw','chiller_kw','boiler_kw','other_kw']].sum(axis=1)
def snap():return {'시나리오':scenario,'현재전력_kW':round(float(view.total_kw.iloc[-1]),1),'생산량_kg_h':round(float(view.production_kg_h.iloc[-1]),1),'에너지원단위_kWh_kg':round(float((view.total_kw/view.production_kg_h).iloc[-1]),3),'CH501_kW':round(float(view.chiller_kw.iloc[-1]),1),'CMP301_kW':round(float(view.compressor_kw.iloc[-1]),1),'최근72시간_최대전력_kW':round(float(view.total_kw.max()),1),'데모_COP':3.2 if scenario=='냉동기 효율 저하' else 4.35,'이상탐지':{'냉동기 효율 저하':'CH-501 효율 저하','압축공기 누설':'CMP-301 비정상 기저부하','최대전력 발생':'MAIN BUS 최대전력 위험'}.get(scenario,'주요 이상 없음')}
def saving(eq):
    kw=31.4 if 'CH' in eq.upper() else 27.8 if 'CMP' in eq.upper() else 18.; h=3200; rate=150
    return {'설비':eq,'절감가능전력_kW':kw,'가정운전시간_h_y':h,'가정전력단가_원_kWh':rate,'예상연간절감량_MWh':round(kw*h/1000,1),'예상연간절감액_만원':round(kw*h*rate/10000,1)}
st.markdown('<div class="eyebrow">INDUSTRIAL ENERGY AI / LIVE DEMO</div>',unsafe_allow_html=True); st.title('산업 에너지 AI 관제센터'); st.caption('공정 모니터링 · LLM · RAG · Agentic AI · AI Copilot')
if mode=='강의 모드':
    cols=st.columns(4)
    for c,n,on in zip(cols,['기존 EMS','LLM','RAG','Agentic AI'],[True,llm_on,rag_on,agent_on]):c.markdown(f'<div class="metric-card"><div class="eyebrow">{n}</div><div class="big {"ok" if on else ""}">● {"ON" if on else "OFF"}</div></div>',unsafe_allow_html=True)
cols=st.columns(4); vals=[('공장 운영 상태','정상 가동','ok'),('현재 전력부하',f'{view.total_kw.iloc[-1]:,.0f} kW',''),('에너지 원단위',f'{(view.total_kw/view.production_kg_h).iloc[-1]:.3f} kWh/kg',''),('활성 경보','1' if scenario!='정상 운전' else '0','warn' if scenario!='정상 운전' else 'ok')]
for c,(a,b,cl) in zip(cols,vals):c.markdown(f'<div class="metric-card"><div class="eyebrow">{a}</div><div class="big {cl}">{b}</div></div>',unsafe_allow_html=True)
st.subheader('공정 설비도'); alert={'냉동기 효율 저하':'CH-501','압축공기 누설':'CMP-301'}.get(scenario,'')
svg=f'''<svg viewBox="0 0 1100 225" width="100%" xmlns="http://www.w3.org/2000/svg"><style>.b{{fill:#0b1827;stroke:#31536c;stroke-width:2}}.t{{fill:#d8e8f2;font:600 17px sans-serif}}.s{{fill:#86a5ba;font:13px sans-serif}}.p{{stroke:#3f7896;stroke-width:7;fill:none}}.n{{fill:#45e0a8}}.a{{fill:#ff5369}} @keyframes blink{{50%{{opacity:.2}}}} .blink{{animation:blink 1s infinite}}</style><path class="p" d="M155 110 H335 M465 110 H635 M765 110 H945"/><rect class="b" x="30" y="60" rx="15" width="125" height="100"/><text class="t" x="55" y="100">BL-101</text><text class="s" x="52" y="127">보일러</text><circle class="n" cx="135" cy="78" r="8"/><rect class="b" x="335" y="60" rx="15" width="130" height="100"/><text class="t" x="358" y="100">CMP-301</text><text class="s" x="362" y="127">공기압축기</text><circle class="{'a blink' if alert=='CMP-301' else 'n'}" cx="445" cy="78" r="9"/><rect class="b" x="635" y="60" rx="15" width="130" height="100"/><text class="t" x="665" y="100">공정라인</text><text class="s" x="666" y="127">생산 공정</text><circle class="n" cx="745" cy="78" r="8"/><rect class="b" x="945" y="60" rx="15" width="125" height="100"/><text class="t" x="970" y="100">CH-501</text><text class="s" x="978" y="127">냉동기</text><circle class="{'a blink' if alert=='CH-501' else 'n'}" cx="1050" cy="78" r="9"/><text class="s" x="470" y="205">에너지·유틸리티 흐름 / 합성 공정</text></svg>'''
st.components.v1.html(svg,height=235)
left,right=st.columns([1.8,1])
with left:
    fig=go.Figure();fig.add_trace(go.Scatter(x=view.timestamp,y=view.total_kw,name='공장 전력',fill='tozeroy'));fig.update_layout(height=300,margin=dict(l=10,r=10,t=25,b=10),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)');st.plotly_chart(fig,use_container_width=True)
with right:
    st.markdown('### 이상 감지')
    if scenario=='정상 운전':st.success('현재 주요 이상 징후가 없습니다.')
    elif scenario=='냉동기 효율 저하':st.error('냉동기 CH-501 · 효율 저하');st.metric('이상 탐지 신뢰도','94.2%');st.metric('예상 절감 가능 전력','31.4 kW')
    elif scenario=='압축공기 누설':st.error('공기압축기 CMP-301 · 비정상 기저부하');st.metric('이상 탐지 신뢰도','91.7%');st.metric('예상 절감 가능 전력','27.8 kW')
    else:st.error('MAIN BUS · 최대전력 초과 위험');st.metric('최대전력 초과분','+180 kW');st.metric('이상 탐지 신뢰도','96.1%')
def rag_answer(q):
    hits=retrieve(q); ctx='\n\n'.join(f'[{n}]\n{c}' for _,n,c in hits)
    if not API_KEY:return None,hits
    ans=llm(f'질문: {q}\n현재 공정 데이터: {json.dumps(snap(),ensure_ascii=False)}\n검색된 사내문서:\n{ctx}\n문서에 없는 내용은 추측하지 말고 답변 끝에 사용한 문서명을 적으세요.')
    return ans,hits

def run_agent(goal):
    tools=[
      {'type':'function','name':'get_process_data','description':'현재 공정 센서와 에너지 요약 데이터를 조회한다.','parameters':{'type':'object','properties':{},'additionalProperties':False},'strict':True},
      {'type':'function','name':'search_internal_documents','description':'사내 매뉴얼, SOP, 장애사례에서 관련 근거를 검색한다.','parameters':{'type':'object','properties':{'query':{'type':'string'}},'required':['query'],'additionalProperties':False},'strict':True},
      {'type':'function','name':'calculate_energy_savings','description':'특정 설비의 데모용 에너지 절감 잠재량과 연간 절감액을 계산한다.','parameters':{'type':'object','properties':{'equipment':{'type':'string'}},'required':['equipment'],'additionalProperties':False},'strict':True}]
    inp=[{'role':'user','content':goal+f'\n현재 시나리오: {scenario}. 필요한 도구를 실제로 사용해 조사하고, 근거와 가정을 구분해 한국어 보고서로 작성하라.'}]; trace=[]
    for _ in range(6):
        r=client().responses.create(model=MODEL,instructions='당신은 산업 에너지 진단 Agent입니다. 목표 달성을 위해 제공된 도구를 사용하세요. 합성데이터와 데모 가정은 명시하세요.',tools=tools,input=inp,store=False); inp+=r.output
        calls=[x for x in r.output if x.type=='function_call']
        if not calls:return r.output_text,trace
        for call in calls:
            args=json.loads(call.arguments or '{}')
            if call.name=='get_process_data':result=snap()
            elif call.name=='search_internal_documents':result=[{'문서':n,'내용':c[:900]} for _,n,c in retrieve(args['query'])]
            else:result=saving(args['equipment'])
            trace.append((call.name,args,result));inp.append({'type':'function_call_output','call_id':call.call_id,'output':json.dumps(result,ensure_ascii=False)})
    return 'Agent 최대 실행 단계에 도달했습니다.',trace

if mode=='강의 모드':
    st.markdown('### AI 기능 단계별 확인');t1,t2,t3,t4=st.tabs(['LLM 해석','RAG 기술지식','Agentic AI 자율진단','AI Copilot'])
    with t1:
        if not llm_on:st.warning('왼쪽 「LLM 해석」을 켜면 현재 공정 데이터를 실제 LLM에 전달합니다.')
        elif not API_KEY:st.error('OpenAI API 키가 아직 연결되지 않았습니다. Streamlit Secrets에 OPENAI_API_KEY를 등록하세요.')
        elif st.button('현재 공정 데이터 LLM 분석',type='primary'):
            with st.spinner('LLM이 현재 공정 데이터를 분석하고 있습니다...'):st.write(llm('현재 합성 공정 데이터입니다. 관찰되는 현상과 우선 확인할 사항을 4~6문장으로 설명하세요.\n'+json.dumps(snap(),ensure_ascii=False)))
    with t2:
        if not rag_on:st.warning('왼쪽 「RAG 기술지식 연결」을 켜면 사내 기술문서 검색이 활성화됩니다.')
        else:
            q=st.text_input('사내 기술지식 검색','CH-501 COP 저하 시 우선 점검 항목은?')
            if st.button('문서 검색 및 근거 기반 답변'):
                ans,hits=rag_answer(q);st.markdown('#### 검색된 사내자료')
                for _,n,c in hits:st.markdown(f'**{n}**');st.caption(c[:500])
                if ans:st.markdown('#### RAG 답변');st.write(ans)
                else:st.info('문서 검색은 실제로 수행되었습니다. LLM 종합 답변을 생성하려면 API 키를 연결하세요.')
    with t3:
        if not agent_on:st.warning('왼쪽 「Agentic AI 자율진단」을 켜면 목표 기반 Tool Calling이 활성화됩니다.')
        else:
            goal=st.text_input('Agent에게 목표 부여','현재 공장의 에너지 손실 원인을 조사하고 근거와 예상 절감효과를 포함한 개선안을 작성하라.')
            if st.button('Agentic AI 실행',type='primary',use_container_width=True):
                if not API_KEY:st.error('Agentic AI 실행에는 OpenAI API 키가 필요합니다.')
                else:
                    with st.spinner('Agent가 필요한 도구를 선택해 조사하고 있습니다...'):final,trace=run_agent(goal)
                    st.markdown('#### 실제 Tool 호출 기록')
                    names={'get_process_data':'DATA TOOL · 공정 데이터 조회','search_internal_documents':'RAG TOOL · 사내문서 검색','calculate_energy_savings':'CALCULATOR · 절감효과 계산'}
                    for i,(n,a,r) in enumerate(trace,1):st.success(f'{i}. {names.get(n,n)}')
                    st.markdown('#### Agent 최종 결과');st.write(final)
    with t4:
        st.info('Copilot은 LLM · RAG · Agent 기능을 사용자가 자연어로 이용하는 통합 창구입니다. 아래 「실제 운영 모드」에서 완성형 화면을 확인할 수 있습니다.')
else:
    st.markdown('### AI Copilot')
    if 'chat' not in st.session_state:st.session_state.chat=[]
    for role,msg in st.session_state.chat:
        with st.chat_message(role):st.markdown(msg)
    q=st.chat_input('예: 오늘 에너지 낭비가 가장 큰 설비를 찾아 원인과 조치방안을 알려줘.')
    if q:
        st.session_state.chat.append(('user',q));
        with st.chat_message('user'):st.markdown(q)
        with st.chat_message('assistant'):
            if not API_KEY:ans='OpenAI API 키가 연결되지 않았습니다. Streamlit Secrets에 OPENAI_API_KEY를 등록하면 실제 Copilot이 작동합니다.'
            else:
                with st.spinner('공정 데이터와 사내 지식을 분석하고 있습니다...'):
                    hits=retrieve(q);ctx='\n\n'.join(f'[{n}] {c}' for _,n,c in hits)
                    ans=llm(f'사용자 질문: {q}\n현재 공정 데이터: {json.dumps(snap(),ensure_ascii=False)}\n관련 사내자료: {ctx}\n필요하면 절감효과는 데모 가정임을 명시하세요. 답변에는 판단 근거와 다음 조치를 포함하세요.')
            st.markdown(ans);st.session_state.chat.append(('assistant',ans))
st.divider();st.caption('교육용 프로토타입 · 합성 센서 데이터 · 사내문서는 데모용 가상 자료 · 실제 현장 적용 전 데이터·안전·보안·엔지니어링 검증 필요')
