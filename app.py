import base64
import hmac
import io
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st


# ----------------------------------------------------------------------------
# 설정
# ----------------------------------------------------------------------------
PRICE = 10_000  # 반찬 1개당 가격 (원)

GROUPS = [str(n) for n in range(4, 17)] + ["결새모"]  # 4 ~ 16, 결새모

APP_NAME = "인도사랑 반찬가게"
PICKUP_NOTICE = "금요철야 예배 후까지 꼭 수령해주세요!"

# 반찬 이름: (아이콘, 화면에 보일 이름(<br>로 줄바꿈), 사진 파일 이름)
# 사진은 images/<파일이름>.png (누끼 딴 투명 PNG) 에 두면 아이콘 대신 보입니다.
MENU = {
    "총각김치": ("🥬", "총각김치", "kimchi"),
    "새송이버섯계란장조림": ("🍳", "새송이버섯<br>계란장조림", "jangjorim"),
    "제육볶음": ("🍖", "제육볶음", "jeyuk"),
}
DISHES = list(MENU)

COLUMNS = ["주문번호", "주문시간", "전도회", "이름", *DISHES, "금액"]

DATA_FILE = Path(os.environ.get("BANCHAN_DATA_FILE", Path(__file__).parent / "orders.csv"))
KST = ZoneInfo("Asia/Seoul")
IMAGE_DIR = Path(__file__).parent / "images"


@st.cache_data
def _encode_image(path: str, mtime: float, mime: str) -> str:
    # mtime이 캐시 키에 들어가므로, 사진을 바꾸거나 새로 올리면 자동으로 다시 읽음
    return f"data:image/{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def image_uri(f: Path) -> str | None:
    mime = {".png": "png", ".webp": "webp", ".jpg": "jpeg", ".jpeg": "jpeg"}.get(f.suffix.lower())
    if mime and f.exists():
        return _encode_image(str(f), f.stat().st_mtime, mime)
    return None


def dish_image(slug: str) -> str | None:
    """images/ 폴더의 반찬 사진을 data URI로 (없으면 None)."""
    for ext, mime in ((".png", "png"), (".webp", "webp"), (".jpg", "jpeg"), (".jpeg", "jpeg")):
        f = IMAGE_DIR / f"{slug}{ext}"
        if f.exists():
            return _encode_image(str(f), f.stat().st_mtime, mime)
    return None


def dish_visual(dish: str, cls: str = "dish-icon") -> str:
    icon, _, slug = MENU[dish]
    src = dish_image(slug)
    if src:
        return f'<div class="{cls} has-img"><img src="{src}" alt="{dish}"></div>'
    return f'<div class="{cls}">{icon}</div>'


def group_label(g: str) -> str:
    return g if g == "결새모" else f"{g}전도회"


def admin_password() -> str | None:
    """Streamlit Secrets 또는 환경변수의 ADMIN_PASSWORD."""
    try:
        if "ADMIN_PASSWORD" in st.secrets:
            return str(st.secrets["ADMIN_PASSWORD"])
    except Exception:
        pass
    return os.environ.get("ADMIN_PASSWORD")


# ----------------------------------------------------------------------------
# 데이터 처리
# ----------------------------------------------------------------------------
@st.cache_resource
def file_lock() -> threading.Lock:
    """여러 사람이 동시에 주문해도 파일이 꼬이지 않도록 하는 잠금."""
    return threading.Lock()


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[COLUMNS]
    for col in DISHES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0).astype(int)
    for col in ["주문번호", "주문시간", "전도회", "이름"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df = df[df[DISHES].sum(axis=1) > 0]  # 수량이 0인 주문은 제거
    df = df[df["전도회"].isin(GROUPS) & (df["이름"] != "")]  # 전도회·이름 없는 주문은 제거
    df["금액"] = df[DISHES].sum(axis=1).astype(int) * PRICE
    return df.reset_index(drop=True)


def load_orders() -> pd.DataFrame:
    if DATA_FILE.exists():
        try:
            return normalize(pd.read_csv(DATA_FILE, dtype=str))
        except Exception:
            pass
    return normalize(pd.DataFrame(columns=COLUMNS))


def write_orders(df: pd.DataFrame) -> None:
    tmp = DATA_FILE.with_suffix(".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8-sig")
    tmp.replace(DATA_FILE)


def order_problems(group: str | None, name: str, cart: dict[str, int]) -> list[str]:
    """주문 전 필수값 확인. 빠진 항목 이름 목록을 돌려줌 (비어 있으면 통과)."""
    problems = []
    if group not in GROUPS:
        problems.append("전도회")
    if not (name or "").strip():
        problems.append("이름")
    if sum(int(v) for v in cart.values()) <= 0:
        problems.append("반찬")
    return problems


def add_order(group: str, name: str, cart: dict[str, int]) -> dict:
    name = (name or "").strip()
    if order_problems(group, name, cart):  # 화면을 우회해도 저장되지 않도록 서버에서 한 번 더 확인
        raise ValueError("전도회, 이름, 반찬은 필수입니다.")
    order = {
        "주문번호": uuid.uuid4().hex[:6].upper(),
        "주문시간": datetime.now(KST).strftime("%Y-%m-%d %H:%M"),
        "전도회": group,
        "이름": name,
        **{d: int(cart.get(d, 0)) for d in DISHES},
    }
    with file_lock():
        df = load_orders()
        df = normalize(pd.concat([df, pd.DataFrame([order])], ignore_index=True))
        write_orders(df)
    order["금액"] = sum(cart.values()) * PRICE
    return order


def group_order(df: pd.DataFrame) -> pd.DataFrame:
    """전도회 순서(4→16→결새모), 이름순 정렬."""
    rank = df["전도회"].map(lambda g: GROUPS.index(g) if g in GROUPS else len(GROUPS))
    return df.assign(_r=rank).sort_values(["_r", "이름"]).drop(columns="_r").reset_index(drop=True)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    """전도회별 누적 반찬 수량과 금액 (+ 합계 행)."""
    valid = df[df["전도회"].isin(GROUPS)]
    s = valid.groupby("전도회").agg(
        주문인원=("이름", "count"), **{d: (d, "sum") for d in DISHES}, 금액=("금액", "sum")
    )
    s = s.reindex(GROUPS, fill_value=0)
    s.insert(len(DISHES) + 1, "반찬합계", s[DISHES].sum(axis=1))
    s = s.reset_index()
    total = s.drop(columns="전도회").sum()
    total["전도회"] = "합계"
    s = pd.concat([s, total.to_frame().T], ignore_index=True)
    for col in s.columns[1:]:
        s[col] = s[col].astype(int)
    s["전도회"] = s["전도회"].map(lambda g: g if g == "합계" else group_label(g))
    return s


def to_excel(df: pd.DataFrame) -> bytes:
    """[전도회별 집계] + [전체 주문] + 전도회마다 명단 시트가 들어간 엑셀 파일."""
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    sheets = {"전도회별 집계": summarize(df), "전체 주문": group_order(df)}
    for g in GROUPS:
        part = df[df["전도회"] == g]
        if part.empty:
            continue
        part = part.drop(columns=["전도회"])
        total = {c: "" for c in part.columns}
        total.update({"이름": "합계", **{d: int(part[d].sum()) for d in DISHES}, "금액": int(part["금액"].sum())})
        sheets[group_label(g)] = pd.concat([part, pd.DataFrame([total])], ignore_index=True)

    header_fill = PatternFill("solid", fgColor="E9C9A0")
    total_fill = PatternFill("solid", fgColor="FFF1DC")
    thin = Side(style="thin", color="D8C3A5")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for title, data in sheets.items():
            data.to_excel(writer, sheet_name=title[:31], index=False)
            ws = writer.sheets[title[:31]]
            cols = list(data.columns)
            for i, col in enumerate(cols, start=1):
                width = max([len(str(col))] + [len(str(v)) for v in data[col]]) * 1.8 + 4
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = min(max(width, 9), 40)
            for row in ws.iter_rows(min_row=1, max_row=ws.max_row, max_col=len(cols)):
                for cell in row:
                    cell.border = border
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                    if cols[cell.column - 1] == "금액" and cell.row > 1:
                        cell.number_format = "#,##0"
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = Font(bold=True)
            last = ws[ws.max_row]
            if ws.max_row > 1 and any(c.value == "합계" for c in last):
                for cell in last:
                    cell.fill = total_fill
                    cell.font = Font(bold=True)
            ws.freeze_panes = "A2"
    return buf.getvalue()


# ----------------------------------------------------------------------------
# 스타일 (휴대폰 세로 화면 기준)
# ----------------------------------------------------------------------------
st.set_page_config(page_title="수봉산 인도사랑 반찬가게", page_icon="🍱", layout="centered")

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Gowun+Dodum&family=Gowun+Batang:wght@700&display=swap');
      html, body, [class*="css"], .stMarkdown, button, input, textarea, label { font-family: 'Gowun Dodum', sans-serif !important; }
      .stApp {
        background:
          radial-gradient(900px 420px at 85% -10%, #FFE3B8 0%, rgba(255,227,184,0) 60%),
          linear-gradient(180deg, #FFF8EC 0%, #FDF3E1 100%);
      }
      [data-testid="stHeader"] { background: transparent; }
      .block-container { max-width: 560px; padding: 2.4rem 1rem 4rem; }
      h1, h2, h3 { font-family: 'Gowun Batang', serif !important; color: #6B4A2B !important; }

      /* 배너 */
      .hero { position: relative; margin-bottom: .8rem; box-shadow: 0 10px 26px rgba(170,120,60,.18); border-radius: 22px; overflow: hidden; }
      .hero img { display: block; width: 100%; height: auto; }
      .hero-text { background: #FFFDF7; padding: 12px 18px 14px; text-align: center; border-top: 1px solid #F1E2C8; }
      .hero-title { font-family: 'Gowun Batang', serif; font-size: 1.55rem; font-weight: 700; color: #6B4A2B; line-height: 1.3; }
      .hero-sub { margin-top: .15rem; font-size: .88rem; color: #8A5A3B; }

      .step { display: flex; align-items: center; gap: .5rem; margin: 1.2rem 0 .5rem;
              font-family: 'Gowun Batang', serif; font-size: 1.12rem; color: #6B4A2B; font-weight: 700; }
      .step b { display: inline-grid; place-items: center; width: 26px; height: 26px; border-radius: 50%;
                background: #C8743A; color: #FFF8EC; font-size: .88rem; }

      /* 카드 공통 */
      [class*="st-key-card_"], .st-key-cart, .st-key-who, .st-key-done, [class*="st-key-grp_"] {
        background: #FFFDF7; border: 1px solid #EEDCBF; border-radius: 18px;
        box-shadow: 0 5px 16px rgba(170,120,60,.10); padding: 14px 14px;
      }
      [class*="st-key-card_"] { padding: 12px 12px; gap: .2rem; }
      [class*="st-key-card_"].active, [class*="st-key-card_"]:has(.in-cart) { border-color: #D9A06C; background: #FFF9EE; }

      /* 카드 안의 가로 배치는 폰에서도 세로로 쪼개지지 않게 */
      [class*="st-key-card_"] [data-testid="stHorizontalBlock"], .st-key-admin_top [data-testid="stHorizontalBlock"],
      .st-key-admin_metrics [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: .4rem !important; align-items: center; }
      [class*="st-key-card_"] [data-testid="stColumn"], .st-key-admin_top [data-testid="stColumn"],
      .st-key-admin_metrics [data-testid="stColumn"] { min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
      [class*="st-key-card_"] [data-testid="stColumn"]:first-child { flex: 1 1 auto !important; }
      [class*="st-key-card_"] [data-testid="stColumn"]:not(:first-child) { flex: 0 0 auto !important; }
      .st-key-admin_metrics [data-testid="stMetricValue"] { font-size: 1.15rem; }

      .dish { display: flex; align-items: center; gap: .7rem; }
      .dish-icon { flex: 0 0 56px; height: 56px; border-radius: 16px; background: #FFF1DC;
                   display: grid; place-items: center; font-size: 1.8rem; }
      .dish-icon.has-img { background: radial-gradient(circle at 50% 60%, #FFE9C7 0%, #FFF5E4 70%); }
      .dish-icon img { width: 64px; height: 64px; object-fit: contain; filter: drop-shadow(0 3px 4px rgba(120,80,40,.25)); }
      .mini { display: inline-grid; place-items: center; width: 24px; height: 24px; margin-right: .3rem; vertical-align: middle; font-size: 1rem; }
      .mini img { width: 26px; height: 26px; object-fit: contain; }
      [class*="st-key-card_"] [data-testid="stMarkdownContainer"] { margin-bottom: 0 !important; }
      [class*="st-key-card_"] { padding-bottom: 14px !important; }
      .dish-name { font-weight: 700; font-size: 1.05rem; color: #4A3B2A; word-break: keep-all; overflow-wrap: anywhere; line-height: 1.3; }
      .dish > div:last-child { min-width: 0; }
      .field-error { color: #C0392B; font-size: .85rem; font-weight: 700; margin: -.4rem 0 .4rem .2rem; }
      .notice { margin-top: .8rem; padding: .7rem .9rem; border-radius: 14px; background: #FDEBD3;
                border: 1px dashed #D9A06C; color: #8A4A22; font-weight: 700; text-align: center; font-size: .95rem; word-break: keep-all; }
      .qty { min-width: 1.6em; font-size: 1.25rem; font-weight: 700; color: #4A3B2A; text-align: center; }
      .in-cart { display: inline-block; font-size: .72rem; padding: 1px 8px; border-radius: 999px;
                 background: #E8F1D9; color: #4F7A2B; margin-top: .25rem; vertical-align: middle; }

      /* +/- 버튼: 동그랗게 */
      [class*="st-key-minus_"] button, [class*="st-key-plus_"] button {
        width: 38px !important; height: 38px; min-height: 38px; padding: 0 !important; border-radius: 50% !important;
        font-size: 1.3rem !important; line-height: 1; margin: 0 auto; display: block;
      }
      [class*="st-key-plus_"] button { background: #C8743A !important; color: #FFF8EC !important; border: none !important; }

      /* 장바구니 */
      .st-key-cart { background: linear-gradient(180deg, #FFFDF7, #FFF5E4); }
      .cart-line { display: flex; justify-content: space-between; gap: .5rem; padding: .45rem 0; border-bottom: 1px dashed #E8D4B4; color: #4A3B2A; font-size: .95rem; }
      .cart-total { display: flex; justify-content: space-between; align-items: baseline; padding-top: .6rem; color: #6B4A2B; }
      .cart-total span:last-child { font-size: 1.5rem; font-weight: 700; color: #B5563C; }
      .cart-empty { text-align: center; color: #A08A70; padding: .6rem 0; font-size: .92rem; }

      /* 버튼 */
      .stButton > button, .stDownloadButton > button {
        border-radius: 999px; border: 1px solid #E2C59D; background: #FFF3DE; color: #6B4A2B;
      }
      .stButton > button:hover, .stDownloadButton > button:hover { border-color: #C8743A; color: #B5563C; }
      .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
        background: linear-gradient(180deg, #D98A4E, #C0662F); color: #FFF8EC; border: none;
        font-size: 1.05rem; min-height: 3.1rem; box-shadow: 0 6px 16px rgba(192,102,47,.3);
      }
      .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover { color: #FFFFFF; filter: brightness(1.05); }
      .stButton > button:disabled { opacity: .45; }

      /* 주문하기 버튼: 화면 아래에 붙어 있게 */
      .st-key-order_bar { position: sticky; bottom: 10px; z-index: 50; background: rgba(253,243,225,.92);
                          backdrop-filter: blur(6px); border-radius: 999px; padding: 6px; box-shadow: 0 -2px 16px rgba(170,120,60,.12); }

      .receipt { text-align: center; }
      .receipt .big { font-size: 2.6rem; }
      .st-key-admin_btn { display: flex; justify-content: center; margin-top: 2rem; }
      .st-key-admin_btn button { background: transparent !important; border: none !important; color: #C4AE90 !important; font-size: .78rem !important; }

      [data-testid="stMetric"] { background: #FFFDF7; border: 1px solid #EEDCBF; border-radius: 16px; padding: 10px 14px; }
      [data-testid="stMetricValue"] { color: #B5563C; font-size: 1.5rem; }
      .grp-head { display: flex; justify-content: space-between; align-items: baseline; gap: .5rem; flex-wrap: wrap; }
      .grp-head b { font-family: 'Gowun Batang', serif; font-size: 1.1rem; color: #6B4A2B; }
      .grp-head span { color: #B5563C; font-weight: 700; font-size: .9rem; }
      .person { display: flex; justify-content: space-between; gap: .6rem; padding: .5rem 0; border-top: 1px dashed #EEDCBF; font-size: .92rem; }
      .person .who { font-weight: 700; color: #4A3B2A; white-space: nowrap; }
      .person .what { color: #6B4A2B; text-align: right; word-break: keep-all; }
      footer, #MainMenu, [data-testid="stToolbar"] { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def html(markup: str) -> None:
    """들여쓰기가 코드 블록으로 보이지 않도록 한 줄로 합쳐서 출력."""
    st.markdown(" ".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def esc(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def hero(title: str | None = None, subtitle: str = "") -> None:
    """맨 위 포스터 배너. title을 주면 아래에 제목 띠를 붙임."""
    src = image_uri(IMAGE_DIR / "banner.webp")
    banner = f'<img src="{src}" alt="{APP_NAME}">' if src else ""
    band = (
        f'<div class="hero-text"><div class="hero-title">{title}</div><div class="hero-sub">{subtitle}</div></div>'
        if title else ""
    )
    html(f'<div class="hero">{banner}{band}</div>')


def step(num: int | str, text: str) -> None:
    html(f'<div class="step"><b>{num}</b>{text}</div>')


# ----------------------------------------------------------------------------
# 상태
# ----------------------------------------------------------------------------
ss = st.session_state
ss.setdefault("cart", {d: 0 for d in DISHES})
ss.setdefault("last_order", None)
ss.setdefault("is_admin", False)
ss.setdefault("form_ver", 0)


def change_qty(dish: str, delta: int) -> None:
    ss.cart[dish] = max(0, min(99, ss.cart[dish] + delta))


@st.dialog("🔒 관리자 로그인")
def admin_login() -> None:
    pw = admin_password()
    if not pw:
        st.warning("관리자 비밀번호가 아직 설정되지 않았어요. Streamlit Cloud 앱 설정 → **Secrets**에 아래처럼 입력해 주세요.")
        st.code('ADMIN_PASSWORD = "원하는비밀번호"', language="toml")
        return
    with st.form("login", border=False):
        entered = st.text_input("비밀번호", type="password")
        ok = st.form_submit_button("로그인", type="primary", width="stretch")
    if ok:
        if hmac.compare_digest(entered.encode(), pw.encode()):
            ss.is_admin = True
            st.rerun()
        else:
            st.error("비밀번호가 맞지 않아요.")


def admin_entry() -> None:
    if st.button("🔒 관리자", key="admin_btn"):
        admin_login()


# ----------------------------------------------------------------------------
# 주문 화면
# ----------------------------------------------------------------------------
def order_done() -> None:
    o = ss.last_order
    lines = "".join(
        f'<div class="cart-line"><span>{dish_visual(d, "mini")}{d}</span><span>{o[d]}개</span></div>'
        for d in DISHES if o[d]
    )
    with st.container(key="done"):
        html(
            f"""
            <div class="receipt">
              <div class="big">🙏</div>
              <h3>주문이 접수되었어요!</h3>
              <p>{group_label(o['전도회'])} · <b>{esc(o['이름'])}</b> 님, 감사합니다.<br>
              <small style="color:#A08A70">주문번호 {o['주문번호']} · {o['주문시간']}</small></p>
            </div>
            {lines}
            <div class="cart-total"><span>총 금액</span><span>{o['금액']:,}원</span></div>
            <div class="notice">📢 {PICKUP_NOTICE}</div>
            """
        )
    st.write("")
    if st.button("➕ 다른 주문 하기", width="stretch"):
        ss.last_order = None
        st.rerun()


def order_page() -> None:
    hero()

    if ss.last_order:
        order_done()
        admin_entry()
        return

    # 1. 주문자
    step(1, "주문하시는 분")
    tried = ss.get("tried_order", False)
    with st.container(key="who"):
        group = st.selectbox(
            "전도회 (필수)", GROUPS, index=None, placeholder="전도회를 선택해 주세요",
            format_func=group_label, key=f"group_{ss.form_ver}",
        )
        if tried and not group:
            html('<div class="field-error">⚠️ 전도회를 선택해 주세요.</div>')
        name = st.text_input(
            "이름 (필수)", placeholder="이름을 입력해 주세요", max_chars=20, key=f"name_{ss.form_ver}"
        ).strip()
        if tried and not name:
            html('<div class="field-error">⚠️ 이름을 입력해 주세요.</div>')

    # 2. 반찬 담기 (한 줄에 하나씩)
    step(2, "반찬 담기")
    for i, dish in enumerate(DISHES):
        label = MENU[dish][1]
        qty = ss.cart[dish]
        with st.container(key=f"card_{i}"):
            info, minus, num, plus = st.columns([6, 1, 1, 1], vertical_alignment="center")
            with info:
                badge = '<div><span class="in-cart">🧺 담김</span></div>' if qty else ""
                html(
                    f"""
                    <div class="dish">
                      {dish_visual(dish)}
                      <div>
                        <div class="dish-name">{label}</div>
                        {badge}
                      </div>
                    </div>
                    """
                )
            minus.button("−", key=f"minus_{i}", on_click=change_qty, args=(dish, -1), disabled=qty == 0)
            num.markdown(f'<div class="qty">{qty}</div>', unsafe_allow_html=True)
            plus.button("+", key=f"plus_{i}", on_click=change_qty, args=(dish, 1))

    # 3. 장바구니
    step(3, "장바구니")
    total_qty = sum(ss.cart.values())
    with st.container(key="cart"):
        if total_qty == 0:
            html('<div class="cart-empty">🧺 아직 담은 반찬이 없어요.<br><b>+</b> 버튼을 눌러 담아 주세요.</div>')
        else:
            lines = "".join(
                f'<div class="cart-line"><span>{dish_visual(d, "mini")}{d} × {n}</span><span>{n * PRICE:,}원</span></div>'
                for d, n in ss.cart.items() if n
            )
            html(f'{lines}<div class="cart-total"><span>총 {total_qty}개</span><span>{total_qty * PRICE:,}원</span></div>')
        html(f'<div class="notice">📢 {PICKUP_NOTICE}</div>')

    missing = order_problems(group, name, ss.cart)
    if tried and missing:
        st.error(f"**{', '.join(missing)}**을(를) 입력해야 주문할 수 있어요.", icon="✋")

    # 버튼은 항상 누를 수 있게 두고, 누를 때 확인 (폰에서 입력 직후 첫 탭이 무시되는 문제 방지)
    with st.container(key="order_bar"):
        clicked = st.button(
            f"🙏 {total_qty}개 · {total_qty * PRICE:,}원 주문하기" if total_qty else "🧺 반찬을 담아 주세요",
            type="primary", width="stretch",
        )
    if clicked:
        if missing:
            ss.tried_order = True
            st.rerun()
        ss.last_order = add_order(group, name, ss.cart)
        ss.cart = {d: 0 for d in DISHES}
        ss.form_ver += 1
        ss.tried_order = False
        st.balloons()
        st.rerun()

    admin_entry()


# ----------------------------------------------------------------------------
# 관리자 화면
# ----------------------------------------------------------------------------
def admin_page() -> None:
    hero("주문 관리", "전도회별 주문 현황")

    c1, c2 = st.container(key="admin_top").columns(2)
    if c1.button("🔄 새로고침", width="stretch"):
        st.rerun()
    if c2.button("🚪 로그아웃", width="stretch"):
        ss.is_admin = False
        st.rerun()

    orders = load_orders()
    m1, m2, m3 = st.container(key="admin_metrics").columns(3)
    m1.metric("주문", f"{len(orders)}건")
    m2.metric("반찬", f"{int(orders[DISHES].to_numpy().sum())}개")
    m3.metric("금액", f"{int(orders['금액'].sum()):,}원")

    st.download_button(
        "📥 엑셀 다운로드",
        to_excel(orders),
        file_name=f"반찬주문_{datetime.now(KST):%Y%m%d_%H%M}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        width="stretch",
        help="전도회별 집계 · 전체 주문 · 전도회마다 명단 시트가 들어 있어요.",
    )

    tab1, tab2, tab3 = st.tabs(["👥 전도회별 명단", "📊 집계", "✏️ 수정·삭제"])

    with tab1:
        if orders.empty:
            st.info("아직 주문이 없어요.")
        for i, g in enumerate(GROUPS):
            part = group_order(orders[orders["전도회"] == g])
            if part.empty:
                continue
            people = ""
            for _, r in part.iterrows():
                items = " · ".join(f"{d} {r[d]}" for d in DISHES if r[d])
                people += (
                    f'<div class="person"><span class="who">{esc(r["이름"])}</span>'
                    f'<span class="what">{items} · <b>{r["금액"]:,}원</b></span></div>'
                )
            totals = " · ".join(f"{d} {int(part[d].sum())}" for d in DISHES if part[d].sum())
            with st.container(key=f"grp_{i}"):
                html(
                    f"""
                    <div class="grp-head"><b>⛪ {group_label(g)}</b>
                      <span>{len(part)}명 · {int(part['금액'].sum()):,}원</span></div>
                    <div style="color:#8A6B4E;font-size:.82rem;margin:.2rem 0 .4rem">{totals}</div>
                    {people}
                    """
                )
        empty = [group_label(g) for g in GROUPS if g not in set(orders["전도회"])]
        if empty and not orders.empty:
            st.caption("아직 주문 없음: " + ", ".join(empty))

    with tab2:
        summary = summarize(orders)
        st.dataframe(
            summary, hide_index=True, width="stretch", height=(len(summary) + 1) * 35 + 3,
            column_config={"금액": st.column_config.NumberColumn("금액(원)", format="localized")},
        )

    with tab3:
        st.caption("수량을 고치거나, 행 왼쪽 체크 후 🗑️ 로 삭제하고 **저장**을 눌러 주세요.")
        edited = st.data_editor(
            group_order(orders), key="admin_editor", num_rows="dynamic", hide_index=True, width="stretch",
            disabled=["주문번호", "주문시간", "금액"],
            column_config={
                "전도회": st.column_config.SelectboxColumn("전도회", options=GROUPS, required=True),
                "이름": st.column_config.TextColumn("이름", required=True, max_chars=20),
                **{d: st.column_config.NumberColumn(d, min_value=0, step=1, format="%d") for d in DISHES},
                "금액": st.column_config.NumberColumn("금액(원)", format="localized"),
            },
        )
        if st.button("💾 저장", type="primary", width="stretch"):
            e = edited.fillna("")
            bad = e[~e["전도회"].isin(GROUPS) | (e["이름"].astype(str).str.strip() == "")]
            if not bad.empty:
                st.error(f"전도회 또는 이름이 비어 있는 주문이 {len(bad)}건 있어요. 채운 뒤 저장해 주세요.")
                st.stop()
            with file_lock():
                # 편집하는 동안 새로 들어온 주문은 그대로 유지
                latest = load_orders()
                arrived = latest[~latest["주문번호"].isin(orders["주문번호"])]
                write_orders(normalize(pd.concat([edited, arrived], ignore_index=True)))
            st.success("저장했어요.")
            st.rerun()


if ss.is_admin:
    admin_page()
else:
    order_page()
