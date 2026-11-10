import os
from pathlib import Path

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------------
# 설정
# ----------------------------------------------------------------------------
PRICE = 10_000  # 반찬 1개당 가격 (원)

GROUPS = [str(n) for n in range(4, 17)] + ["결새모"]  # 4 ~ 16, 결새모

DISHES = ["총각김치", "새송이버섯계란장조림", "제육볶음"]

COLUMNS = ["전도회", "이름", *DISHES, "금액", "비고"]

DATA_FILE = Path(os.environ.get("BANCHAN_DATA_FILE", Path(__file__).parent / "orders.csv"))


# ----------------------------------------------------------------------------
# 데이터 처리
# ----------------------------------------------------------------------------
def empty_orders() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """빈 행 제거, 타입 정리, 금액 재계산."""
    df = df.copy()
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[COLUMNS]

    for col in DISHES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0).astype(int)
    for col in ["전도회", "이름", "비고"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df.loc[~df["전도회"].isin(GROUPS), "전도회"] = ""

    # 아무것도 입력되지 않은 행은 제거
    blank = (df["전도회"] == "") & (df["이름"] == "") & (df[DISHES].sum(axis=1) == 0) & (df["비고"] == "")
    df = df[~blank]

    df["금액"] = df[DISHES].sum(axis=1).astype(int) * PRICE
    return df.reset_index(drop=True)


def load_orders() -> pd.DataFrame:
    if DATA_FILE.exists():
        try:
            return normalize(pd.read_csv(DATA_FILE, dtype={"전도회": str}))
        except Exception:
            pass
    return empty_orders()


def save_orders(df: pd.DataFrame) -> None:
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """전도회별 누적 반찬 수량과 금액."""
    valid = df[df["전도회"].isin(GROUPS)]
    summary = valid.groupby("전도회")[[*DISHES, "금액"]].sum()
    summary = summary.reindex(GROUPS, fill_value=0)
    summary.insert(len(DISHES), "반찬 합계", summary[DISHES].sum(axis=1))
    summary = summary.reset_index()
    total = summary[[*DISHES, "반찬 합계", "금액"]].sum()
    total["전도회"] = "합계"
    summary = pd.concat([summary, total.to_frame().T], ignore_index=True)
    for col in [*DISHES, "반찬 합계", "금액"]:
        summary[col] = summary[col].astype(int)
    return summary


# ----------------------------------------------------------------------------
# 화면
# ----------------------------------------------------------------------------
st.set_page_config(page_title="반찬 주문", page_icon="⛪", layout="wide")

CHURCH_BANNER = """
<svg viewBox="0 0 1200 300" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice"
     style="width:100%;height:240px;display:block;border-radius:22px;">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#FFD9A8"/>
      <stop offset="0.55" stop-color="#FFEBCB"/>
      <stop offset="1" stop-color="#FFF6E4"/>
    </linearGradient>
    <radialGradient id="sun" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#FFF4C2"/>
      <stop offset="0.6" stop-color="#FFD27A" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#FFB45C" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="hillBack" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#B9D58C"/><stop offset="1" stop-color="#9CC173"/>
    </linearGradient>
    <linearGradient id="hillFront" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#9BC46A"/><stop offset="1" stop-color="#7BAA4E"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.5">
      <stop offset="0" stop-color="#FFE7A0" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#FFE7A0" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1200" height="300" fill="url(#sky)"/>
  <circle cx="930" cy="95" r="90" fill="url(#sun)"/>
  <circle cx="930" cy="95" r="34" fill="#FFF1B8"/>

  <!-- 구름 -->
  <g fill="#FFFFFF" opacity="0.85">
    <ellipse cx="190" cy="70" rx="55" ry="16"/><ellipse cx="225" cy="60" rx="35" ry="16"/>
    <ellipse cx="640" cy="50" rx="45" ry="12"/><ellipse cx="670" cy="43" rx="28" ry="12"/>
  </g>

  <!-- 새 -->
  <g fill="none" stroke="#8A6B4E" stroke-width="2" stroke-linecap="round">
    <path d="M760 105 q7 -7 14 0 q7 -7 14 0"/>
    <path d="M795 88 q5 -5 10 0 q5 -5 10 0"/>
  </g>

  <!-- 뒷 동산 -->
  <path d="M0 230 C 200 170, 380 190, 560 215 S 950 160, 1200 205 L1200 300 L0 300 Z" fill="url(#hillBack)"/>
  <!-- 앞 동산 (교회가 있는 언덕) -->
  <path d="M0 270 C 180 250, 330 175, 520 160 C 700 150, 820 230, 1200 255 L1200 300 L0 300 Z" fill="url(#hillFront)"/>

  <!-- 오솔길 -->
  <path d="M470 300 C 490 260, 520 220, 530 196 L548 196 C 548 225, 545 262, 560 300 Z" fill="#E8CFA0" opacity="0.9"/>

  <!-- 교회 -->
  <circle cx="540" cy="120" r="85" fill="url(#glow)"/>
  <g transform="translate(490,60)">
    <!-- 첨탑 -->
    <rect x="38" y="40" width="24" height="60" fill="#FFFDF7" stroke="#C9B79C" stroke-width="1.5"/>
    <polygon points="34,42 50,10 66,42" fill="#B5563C"/>
    <rect x="48.5" y="-14" width="3" height="26" fill="#8A5A3B"/>
    <rect x="41" y="-6" width="18" height="3" fill="#8A5A3B"/>
    <circle cx="50" cy="60" r="6" fill="#F2C46B" stroke="#C9B79C"/>
    <!-- 본당 -->
    <polygon points="0,92 50,62 100,92" fill="#C2603F"/>
    <rect x="6" y="90" width="88" height="48" fill="#FFFDF7" stroke="#C9B79C" stroke-width="1.5"/>
    <path d="M42 138 V116 a8 8 0 0 1 16 0 V138 Z" fill="#9C6B45"/>
    <path d="M16 112 a6 6 0 0 1 12 0 V124 H16 Z" fill="#F7CF7A"/>
    <path d="M72 112 a6 6 0 0 1 12 0 V124 H72 Z" fill="#F7CF7A"/>
  </g>

  <!-- 나무 -->
  <g>
    <rect x="378" y="190" width="6" height="18" fill="#8A6B4E"/><circle cx="381" cy="182" r="16" fill="#6E9E45"/>
    <rect x="660" y="182" width="6" height="18" fill="#8A6B4E"/><circle cx="663" cy="172" r="19" fill="#6A9A42"/>
    <rect x="695" y="194" width="5" height="14" fill="#8A6B4E"/><circle cx="697" cy="187" r="12" fill="#7FAE52"/>
  </g>

  <!-- 꽃 -->
  <g>
    <circle cx="300" cy="258" r="3.5" fill="#FFFFFF"/><circle cx="320" cy="250" r="3.5" fill="#F7B8C4"/>
    <circle cx="760" cy="262" r="3.5" fill="#FFE07A"/><circle cx="790" cy="270" r="3.5" fill="#FFFFFF"/>
    <circle cx="850" cy="268" r="3.5" fill="#F7B8C4"/><circle cx="240" cy="272" r="3.5" fill="#FFE07A"/>
  </g>
</svg>
"""

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Gowun+Batang:wght@700&display=swap');
      html, body, [class*="css"], .stMarkdown, .stDataFrame, button, input { font-family: 'Gowun Dodum', sans-serif; }
      .stApp {
        background:
          radial-gradient(1200px 500px at 85% -10%, #FFE3B8 0%, rgba(255,227,184,0) 60%),
          linear-gradient(180deg, #FFF8EC 0%, #FDF3E1 100%);
      }
      .block-container { padding-top: 3.2rem; max-width: 1150px; }
      .hero { position: relative; margin-bottom: 1.4rem; box-shadow: 0 10px 30px rgba(170,120,60,.18); border-radius: 22px; }
      .hero-text {
        position: absolute; left: 36px; top: 26px; text-align: left;
        color: #6B4A2B; text-shadow: 0 1px 6px rgba(255,248,230,.9);
      }
      .hero-text h1 { font-family: 'Gowun Batang', serif; font-size: 2.2rem; margin: 0; padding: 0; color: #6B4A2B; }
      .hero-text p { margin: .3rem 0 0; font-size: 1rem; color: #8A5A3B; }
      @media (max-width: 640px) {
        .hero-text { left: 16px; top: 14px; }
        .hero-text h1 { font-size: 1.5rem; }
        .hero-text p { font-size: .85rem; }
      }
      h2, h3 { font-family: 'Gowun Batang', serif !important; color: #6B4A2B !important; }
      .verse {
        text-align: center; color: #8A6B4E; font-size: .95rem; margin: -.4rem 0 1.2rem;
      }
      [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        background: #FFFDF7; border-radius: 14px; padding: 6px;
        box-shadow: 0 4px 16px rgba(170,120,60,.12); border: 1px solid #EEDCBF;
      }
      [data-testid="stMetric"] {
        background: #FFFDF7; border: 1px solid #EEDCBF; border-radius: 16px;
        padding: 14px 18px; box-shadow: 0 4px 14px rgba(170,120,60,.10);
      }
      [data-testid="stMetricValue"] { color: #B5563C; }
      .stButton > button, .stDownloadButton > button {
        border-radius: 999px; border: 1px solid #E2C59D; background: #FFF3DE; color: #6B4A2B;
      }
      .stButton > button:hover, .stDownloadButton > button:hover { border-color: #C8743A; color: #B5563C; }
      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

HERO_HTML = f"""
    <div class="hero">
      {CHURCH_BANNER}
      <div class="hero-text">
        <h1>사랑의 반찬 나눔</h1>
        <p>반찬 1개당 {PRICE:,}원 · 정성으로 준비합니다</p>
      </div>
    </div>
    <div class="verse">“주는 것이 받는 것보다 복이 있다” — 사도행전 20:35</div>
    """
# 마크다운이 들여쓰기를 코드 블록으로 보지 않도록 한 줄로 합침
st.markdown(" ".join(line.strip() for line in HERO_HTML.splitlines()), unsafe_allow_html=True)
st.caption("➕ 표 아래쪽을 눌러 행을 추가하고, 전도회 선택 → 이름 입력 → 반찬 수량을 적으면 금액이 자동으로 계산됩니다.")

if "orders" not in st.session_state:
    st.session_state.orders = load_orders()
    st.session_state.editor_version = 0

# 다른 사람이 저장한 내용 불러오기
if st.button("🔄 최신 내용 불러오기"):
    st.session_state.orders = load_orders()
    st.session_state.editor_version += 1
    st.rerun()

# ---------------- 테이블 1: 주문 입력 ----------------
st.subheader("🧺 1. 주문 입력")

dish_columns = {
    dish: st.column_config.NumberColumn(dish, min_value=0, step=1, default=0, format="%d")
    for dish in DISHES
}

edited = st.data_editor(
    st.session_state.orders,
    key=f"orders_editor_{st.session_state.editor_version}",
    num_rows="dynamic",
    hide_index=True,
    width="stretch",
    column_order=COLUMNS,
    column_config={
        "전도회": st.column_config.SelectboxColumn("전도회", options=GROUPS, required=True),
        "이름": st.column_config.TextColumn("이름", required=True),
        **dish_columns,
        "금액": st.column_config.NumberColumn("금액(원)", format="localized", disabled=True),
        "비고": st.column_config.TextColumn("비고"),
    },
)

new_orders = normalize(edited)
if not new_orders.equals(st.session_state.orders):
    st.session_state.orders = new_orders
    save_orders(new_orders)
    # 금액 열을 즉시 갱신하기 위해 편집기를 새로 그림
    st.session_state.editor_version += 1
    st.rerun()

orders = st.session_state.orders
missing = orders[(orders["전도회"] == "") | (orders["이름"] == "")]
if not missing.empty:
    st.warning(f"전도회 또는 이름이 비어 있는 행이 {len(missing)}개 있습니다. (전도회가 없으면 집계에서 빠집니다)")

# ---------------- 테이블 2: 전도회별 집계 ----------------
st.subheader("🌿 2. 전도회별 집계")

summary = summarize(orders)
st.dataframe(
    summary,
    hide_index=True,
    width="stretch",
    height=(len(summary) + 1) * 35 + 3,
    column_config={
        "금액": st.column_config.NumberColumn("금액(원)", format="localized"),
    },
)

c1, c2, c3 = st.columns(3)
c1.metric("총 주문 건수", f"{len(orders)}건")
c2.metric("총 반찬 수량", f"{int(orders[DISHES].to_numpy().sum())}개")
c3.metric("총 금액", f"{int(orders['금액'].sum()):,}원")

# ---------------- 다운로드 ----------------
d1, d2 = st.columns(2)
d1.download_button(
    "⬇️ 주문표 CSV 다운로드",
    orders.to_csv(index=False).encode("utf-8-sig"),
    file_name="반찬_주문표.csv",
    mime="text/csv",
)
d2.download_button(
    "⬇️ 전도회별 집계 CSV 다운로드",
    summary.to_csv(index=False).encode("utf-8-sig"),
    file_name="반찬_전도회별_집계.csv",
    mime="text/csv",
)
