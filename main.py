import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# --------------------------------------------------------
# 1. 페이지 기본 설정
# --------------------------------------------------------
st.set_page_config(page_title="고주파 전력 변환 효율 시뮬레이터", layout="wide")
st.title("⚡ 고주파 전력 변환 효율 추이 시뮬레이터")
st.markdown("**[심화 탐구] 토로이드-SiC 개념적 모형의 시공간적 물리 한계 및 최적 동작 주파수 분석**")

# --------------------------------------------------------
# 2. 수학적 모델링 함수 정의 (보고서 내용 반영)
# --------------------------------------------------------
# 주파수(f) 단위는 kHz입니다.
def calc_efficiency_si(f):
    # 기존 Si 다이오드 + 일반 솔레노이드 모델
    # 1. 전도 손실 (저주파에서 리플 전류로 인해 발생): ~ 150/f
    # 2. 스위칭 손실 (역회복 시간 trr로 인해 주파수에 비례해 급증): ~ 0.12 * f
    loss = (150 / f) + (0.12 * f)
    eff = 100 - loss
    return max(0, eff) # 효율이 0 이하로 내려가지 않도록 처리

def calc_efficiency_sic(f):
    # 제안 모형: SiC 다이오드 + 토로이드 코어
    # 1. 전도 손실: 기존과 유사 (~ 150/f)
    # 2. 스위칭 손실: 역회복이 없어 획기적으로 줄었으나, 기생 커패시터(Coss) 손실 존재 (~ 0.005 * f)
    # 3. 코어 손실: 토로이드 내부 자성체의 고주파 와전류/히스테리시스 손실 급증 (~ 0.00006 * f^2)
    loss = (150 / f) + (0.005 * f) + (0.00006 * (f ** 2))
    eff = 100 - loss
    return max(0, eff)

# --------------------------------------------------------
# 3. 사이드바 (입력부)
# --------------------------------------------------------
st.sidebar.header("⚙️ 시뮬레이션 변수 설정")
st.sidebar.markdown("슬라이더를 움직여 **작동 주파수**를 조절해 보세요.")

# 사용자가 주파수를 조절하는 슬라이더 (10kHz ~ 1000kHz)
current_freq = st.sidebar.slider(
    "작동 주파수 (kHz)", 
    min_value=10, 
    max_value=1000, 
    value=150, 
    step=10
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **탐구 주안점**\n\n"
    "단순히 주파수를 높인다고 좋은 것이 아닙니다. "
    "기생 정전용량과 자성체 발열(열역학적 딜레마)로 인한 "
    "**최적 동작 주파수(Optimal Frequency)**를 찾아보세요."
)

# --------------------------------------------------------
# 4. 데이터 생성 (그래프용)
# --------------------------------------------------------
freqs = np.linspace(10, 1000, 200) # 10부터 1000까지 200개의 구간 생성
si_effs = [calc_efficiency_si(f) for f in freqs]
sic_effs = [calc_efficiency_sic(f) for f in freqs]

# 현재 슬라이더 값에 대한 효율 계산
curr_si_eff = calc_efficiency_si(current_freq)
curr_sic_eff = calc_efficiency_sic(current_freq)

# --------------------------------------------------------
# 5. 메인 화면 출력 (출력부)
# --------------------------------------------------------
# 5-1. 핵심 지표(Metrics) 표시
col1, col2, col3 = st.columns(3)
col1.metric("현재 설정 주파수", f"{current_freq} kHz")
col2.metric("기존 모델 (Si+솔레노이드) 효율", f"{curr_si_eff:.1f} %")
col3.metric("제안 모델 (SiC+토로이드) 효율", f"{curr_sic_eff:.1f} %", f"{curr_sic_eff - curr_si_eff:.1f}% p 향상")

# 5-2. 동적 상태 분석 메시지
st.subheader("🔍 현재 주파수 대역 물리적 해석")
if current_freq < 50:
    st.warning("⚠️ **저주파 구간**: 주파수가 너무 낮아 리플(Ripple) 전류가 큽니다. 코일의 크기가 커져야 하므로 공간적 제약(소형화)에 불리하며, 전도 손실이 큽니다.")
elif 50 <= current_freq <= 300:
    st.success(f"✅ **최적 동작 구간 (Sweet Spot)**: 제안 모형의 효율이 가장 극대화되는 지점입니다. SiC 소자의 빠른 스위칭 특성이 잘 발휘되며 코어 발열도 안정적입니다.")
else:
    st.error("🔥 **고주파 열역학적 딜레마 구간**: 기생 정전용량($C_{oss}$) 충방전 손실과 토로이드 코어의 자성체 손실이 급증하여 효율이 꺾입니다. 방열 설계(Thermal Management)가 필수적입니다.")

# 5-3. Plotly 그래프 렌더링
st.markdown("---")
st.subheader("📈 주파수 변화에 따른 모듈 효율 추이 그래프")

fig = go.Figure()

# 기존 모델 선 그래프
fig.add_trace(go.Scatter(
    x=freqs, y=si_effs, 
    mode='lines', 
    name='기존 모델 (Si + 솔레노이드)', 
    line=dict(color='gray', width=3, dash='dash')
))

# 제안 모델 선 그래프
fig.add_trace(go.Scatter(
    x=freqs, y=sic_effs, 
    mode='lines', 
    name='제안 모델 (SiC + 토로이드)', 
    line=dict(color='blue', width=4)
))

# 사용자가 선택한 주파수에 점(Marker) 찍기
fig.add_trace(go.Scatter(
    x=[current_freq, current_freq], 
    y=[curr_si_eff, curr_sic_eff],
    mode='markers',
    name='현재 설정값',
    marker=dict(color='red', size=12, symbol='circle')
))

fig.update_layout(
    xaxis_title="스위칭 주파수 (kHz)",
    yaxis_title="전력 변환 효율 (%)",
    yaxis=dict(range=[0, 105]), # Y축을 0~105%로 고정
    legend=dict(x=0.6, y=0.9),
    margin=dict(l=0, r=0, t=30, b=0),
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------------
# 6. 수학적 모델링 공식 안내 (학술적 깊이 강조)
# --------------------------------------------------------
with st.expander("📝 본 시뮬레이터에 적용된 물리/수학적 모델링 공식 보기"):
    st.markdown("본 시뮬레이터는 문헌 연구를 바탕으로 다음의 손실 모델을 근사하여 시각화하였습니다.")
    st.latex(r"P_{\text{total}} = P_{\text{cond}} + P_{\text{sw}} + P_{\text{core}}")
    
    st.markdown("- **전도 손실 ($P_{\text{cond}}$)**: 리플 전류에 반비례 (저주파에서 큼)")
    st.latex(r"P_{\text{cond}} \propto \frac{1}{f}")
    
    st.markdown("- **스위칭 손실 ($P_{\text{sw}}$)**: 역회복 지연 시간($t_{rr}$) 및 기생 커패시턴스($C_{oss}$) 충방전")
    st.latex(r"P_{\text{sw}} \propto C_{oss} \cdot V^2 \cdot f")
    
    st.markdown("- **자성체 코어 손실 ($P_{\text{core}}$)**: 와전류 및 히스테리시스 손실 (고주파에서 급증)")
    st.latex(r"P_{\text{core}} \propto f^2")
