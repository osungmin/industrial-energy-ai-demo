import os, re
from pathlib import Path
import numpy as np, pandas as pd, plotly.graph_objects as go, streamlit as st

ROOT=Path(__file__).parent
st.set_page_config(page_title='Industrial Energy Intelligence', page_icon='⚡', layout='wide')

st.markdown('''<style>
.block-container{padding-top:1.3rem;max-width:1500px}.metric-card{background:linear-gradient(145deg,#0c1a2b,#0a1422);border:1px solid #1c3850;border-radius:14px;padding:16px;box-shadow:0 8px 30px #0005}.eyebrow{font-size:.72rem;letter-spacing:.18em;color:#6f91aa}.big{font-size:1.75rem;font-weight:700}.ok{color:#45e0a8}.warn{color:#ffbd59}.bad{color:#ff667a}.equip{border:1px solid #24445d;border-radius:14px;padding:18px;text-align:center;background:#0b1827}.agent{border-left:3px solid #00d4ff;padding-left:14px}.small{color:#8aa5b9;font-size:.82rem}</style>''',unsafe_allow_html=True)

df=pd.read_csv(ROOT/'data/factory_energy.csv',parse_dates=['timestamp'])
scenario=st.sidebar.radio('DEMO SCENARIO',['Normal operation','Chiller efficiency drop','Compressor air leak','Peak demand event'],index=1)
st.sidebar.caption('Synthetic-data educational prototype')

view=df.tail(72).copy()
if scenario=='Normal operation':
    view['chiller_kw']-=np.where(np.arange(len(view))<42,34,0); view['compressor_kw']-=np.where((np.arange(len(view))>=44)&(np.arange(len(view))<60),27,0)
elif scenario=='Compressor air leak': view.loc[view.index[-24:],'compressor_kw']+=35
elif scenario=='Peak demand event': view.loc[view.index[-8:-4],'other_kw']+=180
view['total_kw']=view[['compressor_kw','chiller_kw','boiler_kw','other_kw']].sum(axis=1)

st.markdown('<div class="eyebrow">INDUSTRIAL ENERGY INTELLIGENCE PLATFORM / LIVE DEMO</div>',unsafe_allow_html=True)
st.title('AI Operations Center')
st.caption('Digital process view · energy analytics · RAG · agentic investigation')

c1,c2,c3,c4=st.columns(4)
metrics=[('PLANT STATUS','OPERATIONAL','ok'),('CURRENT LOAD',f"{view.total_kw.iloc[-1]:,.0f} kW",''),('ENERGY INTENSITY',f"{(view.total_kw/view.production_kg_h).iloc[-1]:.3f} kWh/kg",''),('ACTIVE ALERTS','1' if scenario!='Normal operation' else '0','warn' if scenario!='Normal operation' else 'ok')]
for c,(a,b,cl) in zip([c1,c2,c3,c4],metrics): c.markdown(f'<div class="metric-card"><div class="eyebrow">{a}</div><div class="big {cl}">{b}</div></div>',unsafe_allow_html=True)

st.subheader('Digital Factory Overview')
a,b,c,d=st.columns(4)
alert={'Chiller efficiency drop':'CHILLER #01','Compressor air leak':'COMPRESSOR #02','Peak demand event':'MAIN BUS'}.get(scenario,'')
for col,name,sub in [(a,'BOILER #01','Steam'),(b,'COMPRESSOR #02','Compressed air'),(c,'PROCESS LINE','Production'),(d,'CHILLER #01','Cooling')]:
    status='● ALERT' if name==alert else '● NORMAL'; cls='bad' if name==alert else 'ok'
    col.markdown(f'<div class="equip"><div class="eyebrow">{sub.upper()}</div><h3>{name}</h3><div class="{cls}">{status}</div></div>',unsafe_allow_html=True)

left,right=st.columns([1.8,1])
with left:
    fig=go.Figure(); fig.add_trace(go.Scatter(x=view.timestamp,y=view.total_kw,name='Plant kW',fill='tozeroy')); fig.update_layout(height=330,margin=dict(l=10,r=10,t=25,b=10),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',legend_orientation='h')
    st.plotly_chart(fig,use_container_width=True)
with right:
    st.markdown('### AI Detected')
    if scenario=='Normal operation': st.success('No significant anomaly detected.')
    elif scenario=='Chiller efficiency drop': st.error('CHILLER #01 · efficiency degradation'); st.metric('Anomaly confidence','94.2%'); st.metric('Estimated avoidable load','31.4 kW')
    elif scenario=='Compressor air leak': st.error('COMPRESSOR #02 · abnormal base load'); st.metric('Anomaly confidence','91.7%'); st.metric('Estimated avoidable load','27.8 kW')
    else: st.error('MAIN BUS · peak demand excursion'); st.metric('Peak excursion','+180 kW'); st.metric('Anomaly confidence','96.1%')

st.subheader('Equipment Investigation')
t1,t2,t3=st.tabs(['Equipment zoom','RAG evidence','AI Copilot'])
with t1:
    if scenario=='Chiller efficiency drop':
        x=view.tail(54); fig=go.Figure(); fig.add_trace(go.Scatter(x=x.timestamp,y=x.chiller_kw,name='Chiller kW')); fig.add_trace(go.Scatter(x=x.timestamp,y=x.chiller_cop,name='COP',yaxis='y2')); fig.update_layout(height=340,yaxis2=dict(overlaying='y',side='right'),margin=dict(l=10,r=10,t=25,b=10),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)'); st.plotly_chart(fig,use_container_width=True); st.error('Suspected zone: condenser heat-rejection performance'); st.caption('Sensor analytics identifies the equipment; the UI highlights the suspected zone. This is not a trained vision fault detector.')
    else: st.info('Select “Chiller efficiency drop” for the full equipment zoom scenario.')
with t2:
    docs=[]
    for p in (ROOT/'documents').glob('*.md'):
        txt=p.read_text(encoding='utf-8'); docs.append((p.name,txt))
    q=st.text_input('Knowledge search','condenser fouling efficiency COP')
    terms=set(re.findall(r'[A-Za-z가-힣]+',q.lower()))
    scored=sorted(((sum(t in txt.lower() for t in terms),name,txt) for name,txt in docs),reverse=True)
    for score,name,txt in scored[:2]:
        st.markdown(f'**{name}** · relevance {min(99,55+score*8)}%'); st.write(txt.split('\n\n')[1][:500] if '\n\n' in txt else txt[:500])
with t3:
    st.markdown('<div class="agent"><b>Agent workflow</b><br>✓ Read telemetry<br>✓ Compare baseline<br>✓ Detect abnormal equipment<br>✓ Retrieve technical guidance<br>✓ Estimate avoidable energy<br>✓ Generate engineering recommendation</div>',unsafe_allow_html=True)
    prompt=st.text_input('Ask the Energy Copilot','왜 칠러 전력 사용량이 증가했어?')
    if st.button('RUN AI INVESTIGATION',type='primary'):
        api_key=None
        try: api_key=st.secrets.get('OPENAI_API_KEY')
        except Exception: pass
        evidence=(ROOT/'documents/chiller_guide.md').read_text(encoding='utf-8')
        if api_key:
            try:
                from openai import OpenAI
                client=OpenAI(api_key=api_key)
                resp=client.responses.create(model='gpt-5-mini',input=f'''You are an industrial energy copilot for an educational synthetic-data demo. Be concise, cautious, and distinguish evidence from hypotheses. User: {prompt}\nScenario: {scenario}. Latest chiller power {view.chiller_kw.iloc[-1]:.1f} kW, COP {view.chiller_cop.iloc[-1]:.2f}. Retrieved guide: {evidence[:1800]}''')
                st.write(resp.output_text)
            except Exception as e: st.warning(f'API call unavailable; showing deterministic demo response. ({type(e).__name__})'); api_key=None
        if not api_key:
            if scenario=='Chiller efficiency drop': st.write('최근 부하 대비 Chiller #01의 소비전력이 높고 COP가 저하된 패턴이 확인됩니다. RAG 문서에서는 condenser-side fouling 또는 열방출 성능 저하를 점검 후보로 제시합니다. 우선 냉각수 유량·입출구 온도·튜브/스트레이너·센서 교정을 확인하고, 정비 전후 동일 부하 기준으로 COP를 재비교하는 것이 적절합니다. 데모 추정 회피 가능 부하는 약 31 kW입니다.')
            else: st.write('선택된 시나리오의 센서 패턴을 기준선과 비교해 이상 설비와 에너지 손실 후보를 표시합니다. 실제 현장 적용 전에는 계측 신뢰성 및 엔지니어링 검증이 필요합니다.')

st.divider(); st.caption('Educational prototype · Synthetic telemetry · Recommendations require engineering verification before real-world use.')
