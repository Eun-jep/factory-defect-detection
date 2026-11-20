# app_new.py: 공장 HMI 스타일의 불량 판정 대시보드 (기존 app.py는 그대로 둔 채 따로 실행해 볼 수 있음)
import base64
import html
import inspect
import io

import pandas as pd
import streamlit as st
from PIL import Image

from db import get_history, save_result
from model import gradcam_overlay, predict

st.set_page_config(page_title="병 입구 불량 판정 콘솔", layout="wide")

GOOD, BAD, WARN = "#34D399", "#F87171", "#FBBF24"

st.markdown(
    """
<style>
.stApp {
  background:
    linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px) 0 0 / 42px 42px,
    linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px) 0 0 / 42px 42px,
    radial-gradient(1300px 640px at 18% -8%, #0E3A45 0%, #08151A 58%), #050E12;
  color: #E5E7EB;
}
.block-container { padding-top: 1.0rem; max-width: 1400px; }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stToolbar"], .stDeployButton { visibility: hidden; }
[class*="st-key-panel_"] {
  background: linear-gradient(160deg, #12303A 0%, #09181D 100%);
  border: 1px solid #1F4A57 !important; border-radius: 14px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.07);
}
/* 상단 바 */
.hmi-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;
  padding: 12px 20px; border-radius: 14px; border: 1px solid #1F4A57;
  background: linear-gradient(180deg, #17404B 0%, #0B222A 100%);
  box-shadow: 0 10px 24px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.08); }
.brand { display: flex; align-items: center; gap: 14px; }
.hexw { filter: drop-shadow(0 3px 6px rgba(37,99,235,0.6)); }
.hex { width: 40px; height: 44px; background: linear-gradient(145deg, #67E8F9, #0E7490); clip-path: polygon(50% 0, 100% 25%, 100% 75%, 50% 100%, 0 75%, 0 25%); }
.ttl { font-size: 1.55rem; font-weight: 800; color: #F9FAFB; letter-spacing: 0.01em; }
.sub { color: #94A3B8; font-size: 0.88rem; margin-top: 1px; }
.chip { display: inline-block; background: linear-gradient(180deg, #173E49, #0C2830); border: 1px solid #2A5B6B; color: #CBD5E1;
  padding: 5px 12px; border-radius: 8px; font-size: 0.8rem; margin-left: 8px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.06); }
.chip .led { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #34D399; box-shadow: 0 0 8px #34D399; margin-right: 7px; }
/* 요약 카드 */
.kpi { position: relative; overflow: hidden; border: 1px solid #1F4A57; border-radius: 14px; padding: 14px 18px 12px 24px; margin-bottom: 14px;
  background: linear-gradient(160deg, #143440 0%, #09181D 100%);
  box-shadow: 0 10px 22px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.07); }
.kpi::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 6px; background: #64748B; }
.kpi.k-ok::before { background: #34D399; box-shadow: 0 0 14px #34D399; }
.kpi.k-ng::before { background: #F87171; box-shadow: 0 0 14px #F87171; }
.kpi.k-nt::before { background: #67E8F9; box-shadow: 0 0 14px #67E8F9; }
.kl { color: #94A3B8; font-size: 0.82rem; letter-spacing: 0.04em; }
.kv { font-family: Consolas, 'D2Coding', 'Courier New', monospace; font-size: 2.4rem; font-weight: 700; line-height: 1.15; text-shadow: 0 0 8px currentColor; }
.ks { color: #64748B; font-size: 0.8rem; }
.ok { color: #34D399; } .ng { color: #F87171; } .nt { color: #E5E7EB; }
/* 패널 제목 */
.ph { font-weight: 700; font-size: 1.0rem; color: #E5E7EB; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
.ph span:first-child::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #22D3EE; box-shadow: 0 0 9px #22D3EE; margin-right: 9px; }
.live { font-weight: 600; font-size: 0.8rem; color: #94A3B8; }
/* 검사 화면 */
.viewer { position: relative; background: linear-gradient(180deg, #0C1424, #050E12); border: 2px solid #1F4A57; border-radius: 12px; padding: 10px; text-align: center; min-height: 260px; margin-bottom: 4px;
  box-shadow: inset 0 0 26px rgba(0,0,0,0.65); }
.viewer img { width: 100%; aspect-ratio: 1 / 1; object-fit: contain; background: #0A101C; border-radius: 8px; display: block; }
.viewer::after { content: ""; position: absolute; inset: 10px; border-radius: 8px; pointer-events: none;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.035) 0 1px, transparent 1px 3px); }
.viewer .c { position: absolute; width: 22px; height: 22px; border: 0 solid currentColor; z-index: 3; }
.c.tl { top: 5px; left: 5px; border-top-width: 3px; border-left-width: 3px; border-top-left-radius: 6px; }
.c.tr { top: 5px; right: 5px; border-top-width: 3px; border-right-width: 3px; border-top-right-radius: 6px; }
.c.bl { bottom: 5px; left: 5px; border-bottom-width: 3px; border-left-width: 3px; border-bottom-left-radius: 6px; }
.c.br { bottom: 5px; right: 5px; border-bottom-width: 3px; border-right-width: 3px; border-bottom-right-radius: 6px; }
.viewer.good { border-color: #1F7A5A; color: #34D399; box-shadow: 0 0 22px rgba(52,211,153,0.28), inset 0 0 26px rgba(0,0,0,0.65); }
.viewer.bad { border-color: #8F3A3A; color: #F87171; box-shadow: 0 0 24px rgba(248,113,113,0.42), inset 0 0 26px rgba(0,0,0,0.65); }
.viewer.cam { border-color: #8A6A12; color: #FBBF24; box-shadow: 0 0 20px rgba(251,191,36,0.25), inset 0 0 26px rgba(0,0,0,0.65); }
.viewer.idle { display: flex; align-items: center; justify-content: center; color: #64748B; border-style: dashed; font-size: 0.95rem; }
@keyframes glowbad { 0%,100% { box-shadow: 0 0 14px rgba(248,113,113,0.25), inset 0 0 26px rgba(0,0,0,0.65); } 50% { box-shadow: 0 0 32px rgba(248,113,113,0.65), inset 0 0 26px rgba(0,0,0,0.65); } }
.tag { position: absolute; top: 16px; left: 16px; padding: 3px 12px; border-radius: 6px; font-weight: 800; font-size: 0.92rem; z-index: 4;
  box-shadow: 0 3px 8px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.35); }
.tag.good { background: linear-gradient(180deg, #4ADE9B, #1FA971); color: #04130C; }
.tag.bad { background: linear-gradient(180deg, #FB8A8A, #DC3F3F); color: #1A0707; }
.tag.cam { background: linear-gradient(180deg, #FCD34D, #D99A06); color: #1F1600; }
.vcap { color: #94A3B8; font-size: 0.78rem; margin-top: 7px; position: relative; z-index: 4; }
.strip { display: flex; gap: 10px; margin-top: 10px; overflow-x: auto; padding-bottom: 4px; }
.thumb { width: 96px; flex: 0 0 auto; border: 2px solid #1F4A57; border-radius: 8px; padding: 3px; background: #0A101C; text-align: center; box-shadow: 0 5px 12px rgba(0,0,0,0.45); }
.thumb.good { border-color: #1F7A5A; } .thumb.bad { border-color: #8F3A3A; }
.thumb img { width: 100%; border-radius: 5px; display: block; }
.thumb span { font-size: 0.72rem; font-weight: 800; }
/* 판정 패널: 경광등 + 판정 표시 + 게이지 */
.vrow { display: flex; gap: 14px; align-items: stretch; margin-bottom: 4px; }
.tower { width: 58px; flex: 0 0 58px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 9px; padding: 10px 0;
  border-radius: 12px; background: linear-gradient(90deg, #0A101C, #1A2438 50%, #0A101C); border: 1px solid #1F4A57; box-shadow: inset 0 0 14px rgba(0,0,0,0.7); }
.lamp { width: 30px; height: 30px; border-radius: 50%; border: 2px solid rgba(0,0,0,0.55); }
.lamp.red { background: radial-gradient(circle at 35% 30%, #5B2A2A, #2A1010); }
.lamp.yel { background: radial-gradient(circle at 35% 30%, #5B4A1C, #2A2008); }
.lamp.grn { background: radial-gradient(circle at 35% 30%, #1D5A44, #0B2A1F); }
.lamp.red.on { background: radial-gradient(circle at 35% 30%, #FFB4B4, #EF4444 55%, #991B1B); box-shadow: 0 0 20px #EF4444, 0 0 40px rgba(239,68,68,0.55); }
.lamp.yel.on { background: radial-gradient(circle at 35% 30%, #FFF1B0, #FBBF24 55%, #A16207); box-shadow: 0 0 18px #FBBF24, 0 0 34px rgba(251,191,36,0.45); }
.lamp.grn.on { background: radial-gradient(circle at 35% 30%, #BBF7D0, #34D399 55%, #047857); box-shadow: 0 0 20px #34D399, 0 0 40px rgba(52,211,153,0.5); }
.vbox { flex: 1; border-radius: 12px; padding: 12px 14px; border: 1px solid #1F4A57; text-align: center; display: flex; flex-direction: column; justify-content: center;
  box-shadow: inset 0 2px 10px rgba(0,0,0,0.5), 0 6px 14px rgba(0,0,0,0.35); }
.vbox .vk { font-size: 0.85rem; font-weight: 800; letter-spacing: 0.18em; opacity: 0.95; }
.vbox .vv { font-size: 2.3rem; font-weight: 800; line-height: 1.15; text-shadow: 0 0 7px currentColor; }
.vbox.good { background: linear-gradient(180deg, rgba(52,211,153,0.22), rgba(52,211,153,0.07)); border-color: #1F7A5A; color: #34D399; }
.vbox.bad { background: linear-gradient(180deg, rgba(248,113,113,0.24), rgba(248,113,113,0.07)); border-color: #8F3A3A; color: #F87171; box-shadow: 0 0 24px rgba(248,113,113,0.42), inset 0 0 26px rgba(0,0,0,0.65); }
.vbox.idle { background: #0F172A; color: #64748B; border-style: dashed; }
.sg { position: relative; width: 230px; height: 128px; margin: 12px auto 0 auto; }
.sg-arc { position: absolute; left: 0; top: 0; width: 230px; height: 115px; border-radius: 115px 115px 0 0;
  background: conic-gradient(from -90deg at 50% 100%, #34D399 0deg, #34D399 87deg, #FBBF24 89deg, #FBBF24 91deg, #F87171 93deg, #F87171 180deg, transparent 180deg);
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.5)); }
.sg-arc.off { background: #1F2A44; }
.sg-hole { position: absolute; left: 32px; top: 32px; width: 166px; height: 83px; border-radius: 83px 83px 0 0; background: #0E1626; box-shadow: inset 0 4px 10px rgba(0,0,0,0.6); }
.sg-needle { position: absolute; left: 113px; top: 14px; width: 4px; height: 101px; border-radius: 2px; background: linear-gradient(#FFFFFF, #9CA3AF); transform-origin: 50% 100%; box-shadow: 0 0 6px rgba(255,255,255,0.5); }
.sg-hub { position: absolute; left: 105px; top: 105px; width: 20px; height: 20px; border-radius: 50%; background: radial-gradient(circle at 35% 30%, #F3F4F6, #6B7280); box-shadow: 0 2px 6px rgba(0,0,0,0.7); }
.sg-lab { position: absolute; bottom: -2px; font-size: 0.7rem; color: #64748B; }
.sg-lab.l { left: 8px; } .sg-lab.r { right: 6px; } .sg-lab.m { left: 50%; top: -14px; transform: translateX(-50%); color: #FBBF24; }
.sg-val { text-align: center; margin-top: 2px; }
.sg-val b { font-family: Consolas, 'D2Coding', 'Courier New', monospace; font-size: 1.9rem; text-shadow: 0 0 12px currentColor; }
.sg-val span { display: block; color: #94A3B8; font-size: 0.76rem; }
.row2 { display: flex; justify-content: space-between; padding: 6px 0; border-top: 1px solid #1B4452; font-size: 0.85rem; color: #94A3B8; }
.row2 b { color: #E5E7EB; font-weight: 600; max-width: 62%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
/* 분포, 막대 */
.donutwrap { display: flex; align-items: center; gap: 18px; justify-content: center; padding: 6px 0; }
.donut { width: 132px; height: 132px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 0 6px #0C1424, 0 10px 22px rgba(0,0,0,0.6); }
.dhole { width: 88px; height: 88px; border-radius: 50%; background: radial-gradient(circle at 40% 30%, #143440, #0C1424); display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: inset 0 3px 8px rgba(0,0,0,0.6); }
.dhole b { font-family: Consolas, 'D2Coding', 'Courier New', monospace; font-size: 1.5rem; } .dhole span { color: #94A3B8; font-size: 0.72rem; }
.leg { font-size: 0.86rem; color: #CBD5E1; line-height: 1.9; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px currentColor; }
.pbar { margin: 11px 0; } .pbar .pl { display: flex; justify-content: space-between; font-size: 0.85rem; color: #CBD5E1; margin-bottom: 5px; }
.pbar .trk { height: 11px; background: #0A101C; border: 1px solid #1B4452; border-radius: 6px; padding: 1px; box-shadow: inset 0 2px 5px rgba(0,0,0,0.7); }
.pbar .fil { height: 7px; border-radius: 4px; background: repeating-linear-gradient(90deg, #34D399 0 9px, transparent 9px 12px); filter: drop-shadow(0 0 4px #34D399); }
.note { color: #64748B; font-size: 0.77rem; }
/* 입체 버튼 */
.stButton > button { background: linear-gradient(180deg, #22D3EE, #0891B2); color: #031316; font-weight: 800; border: 1px solid #0E7490; border-radius: 10px;
  box-shadow: 0 5px 0 #155E75, 0 10px 18px rgba(0,0,0,0.45); transition: transform 0.06s, box-shadow 0.06s; }
.stButton > button:hover { filter: brightness(1.08); }
.stButton > button:active { transform: translateY(4px); box-shadow: 0 1px 0 #155E75, 0 4px 8px rgba(0,0,0,0.45); }

/* ---- 정밀 검사 장비 스타일 ---- */
.instr { display: flex; gap: 8px; }
.ib { background: linear-gradient(180deg, #0A1E25, #07141A); border: 1px solid #1F4A57; border-radius: 8px; padding: 5px 12px; min-width: 92px;
  box-shadow: inset 0 2px 6px rgba(0,0,0,0.6); }
.il { display: block; color: #4B8A99; font-size: 0.62rem; letter-spacing: 0.14em; font-weight: 700; }
.iv { display: block; color: #CFFAFE; font-family: Consolas, 'D2Coding', 'Courier New', monospace; font-size: 0.92rem; font-weight: 700; }
.iv.on { color: #34D399; text-shadow: 0 0 8px #34D399; }
.imgbox { position: relative; border-radius: 8px; overflow: hidden; }
.rule { position: absolute; z-index: 5; pointer-events: none; }
.rule.rt { top: 0; left: 0; right: 0; height: 9px; background: repeating-linear-gradient(90deg, rgba(103,232,249,0.75) 0 1px, transparent 1px 14px); }
.rule.rl { top: 0; bottom: 0; left: 0; width: 9px; background: repeating-linear-gradient(0deg, rgba(103,232,249,0.75) 0 1px, transparent 1px 14px); }
.cross { position: absolute; inset: 0; z-index: 4; pointer-events: none;
  background: linear-gradient(rgba(103,232,249,0.30), rgba(103,232,249,0.30)) center / 1px 100% no-repeat,
              linear-gradient(rgba(103,232,249,0.30), rgba(103,232,249,0.30)) center / 100% 1px no-repeat; }
.vlabel { position: absolute; top: 18px; right: 18px; z-index: 6; color: #67E8F9; font-family: Consolas, 'D2Coding', 'Courier New', monospace; font-size: 0.72rem;
  background: rgba(5,14,18,0.7); border: 1px solid #1F4A57; border-radius: 5px; padding: 2px 8px; letter-spacing: 0.04em; }
.sg-ticks { position: absolute; left: 0; top: 0; width: 230px; height: 115px; border-radius: 115px 115px 0 0;
  background: repeating-conic-gradient(from -90deg at 50% 100%, rgba(5,14,18,0.85) 0deg 1.1deg, transparent 1.1deg 9deg);
  -webkit-mask: radial-gradient(circle at 50% 100%, transparent 0 84px, #000 85px 115px, transparent 116px);
  mask: radial-gradient(circle at 50% 100%, transparent 0 84px, #000 85px 115px, transparent 116px); }
.rds { margin-top: 8px; border: 1px solid #1F4A57; border-radius: 10px; background: linear-gradient(180deg, #08171D, #050E12); padding: 4px 12px;
  box-shadow: inset 0 2px 8px rgba(0,0,0,0.65); }
.rd { display: flex; justify-content: space-between; align-items: baseline; padding: 5px 0; border-bottom: 1px dashed #17404B; font-size: 0.8rem; color: #6FA8B8; }
.rd:last-child { border-bottom: 0; }
.rd b { font-family: Consolas, 'D2Coding', 'Courier New', monospace; font-size: 1.02rem; color: #E0F7FA; }
</style>
""",
    unsafe_allow_html=True,
)

top_area = st.container()


def to_b64(img, size=640, quality=85):
    im = img.convert("RGB")
    im.thumbnail((size, size))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode()


CORNERS = '<i class="c tl"></i><i class="c tr"></i><i class="c bl"></i><i class="c br"></i>'


def viewer(b64, cls, tag, caption):
    label = "CAM 7×7 확대" if cls == "cam" else "입력 224×224"
    return (f'<div class="viewer {cls}">{CORNERS}<span class="tag {cls}">{tag}</span><span class="vlabel">{label}</span>'
            f'<div class="imgbox"><div class="rule rt"></div><div class="rule rl"></div>'
            f'<img src="data:image/jpeg;base64,{b64}"><div class="cross"></div></div>'
            f'<div class="vcap">{html.escape(caption)}</div></div>')


def idle_viewer(text):
    return f'<div class="viewer idle">{CORNERS}<div>{text}</div></div>'


kpi_area = st.container()
col_main, col_side = st.columns([8, 4], gap="medium")

with col_main:
    with st.container(border=True, key="panel_inspect"):
        status_area = st.container()
        uploaded = st.file_uploader("병 입구 사진 (png, jpg, jpeg)", type=["png", "jpg", "jpeg"])
        view_area = st.container()
        strip_area = st.container()

with col_side:
    with st.container(border=True, key="panel_verdict"):
        st.markdown('<div class="ph"><span>판정 결과</span></div>', unsafe_allow_html=True)
        verdict_area = st.container()
        save_area = st.container()

# ---- 판정 ----
img, result = None, None
if uploaded is not None:
    img = Image.open(uploaded)
    result = predict(img)
    prob = float(result["defect_prob"])
    is_bad = result["label"] == "불량"
    key = f"{uploaded.name}:{uploaded.size}"
    if st.session_state.get("last_key") != key:  # 같은 사진은 한 번만 세션 목록에 추가
        st.session_state["last_key"] = key
        items = st.session_state.setdefault("session_items", [])
        items.append({"name": uploaded.name, "bad": is_bad, "thumb": to_b64(img, 160)})
        del items[:-8]

with status_area:
    state = "● 판정 완료" if result is not None else "● 대기"
    st.markdown(f'<div class="ph"><span>검사 화면</span><span class="live">{state}</span></div>', unsafe_allow_html=True)

with view_area:
    a, b = st.columns(2)
    if img is None:
        a.markdown(idle_viewer("검사할 사진을 올려 주세요"), unsafe_allow_html=True)
        b.markdown(idle_viewer("판정 근거(Grad-CAM)가 여기에 표시됩니다"), unsafe_allow_html=True)
    elif is_bad:
        a.markdown(viewer(to_b64(img), "bad", "NG", f"원본 · {uploaded.name}"), unsafe_allow_html=True)
        b.markdown(viewer(to_b64(gradcam_overlay(img)), "cam", "Grad-CAM", "판정 근거 (대략적 영역, 위치 검출 아님)"), unsafe_allow_html=True)
    else:
        a.markdown(viewer(to_b64(img), "good", "PASS", f"원본 · {uploaded.name}"), unsafe_allow_html=True)
        b.markdown(idle_viewer("정상으로 판정되어<br>Grad-CAM은 표시하지 않습니다"), unsafe_allow_html=True)

with strip_area:
    items = st.session_state.get("session_items", [])
    if items:
        cards = "".join(
            f'<div class="thumb {"bad" if it["bad"] else "good"}"><img src="data:image/jpeg;base64,{it["thumb"]}">'
            f'<span class="{"ng" if it["bad"] else "ok"}">{"NG" if it["bad"] else "PASS"}</span></div>'
            for it in reversed(items)
        )
        st.markdown(f'<div class="note" style="margin-top:10px">이번 접속에서 검사한 사진 (저장 여부와 무관, 새로고침하면 사라짐)</div><div class="strip">{cards}</div>',
                    unsafe_allow_html=True)

with verdict_area:
    if result is None:
        lamps = '<div class="lamp red"></div><div class="lamp yel on"></div><div class="lamp grn"></div>'
        st.markdown(
            f'<div class="vrow"><div class="tower">{lamps}</div><div class="vbox idle"><div class="vk">STATUS</div><div class="vv">대기 중</div></div></div>'
            '<div class="sg"><div class="sg-arc off"></div><div class="sg-ticks"></div><div class="sg-hole"></div><div class="sg-hub"></div>'
            '<div class="sg-lab l">0</div><div class="sg-lab r">1.0</div></div>'
            '<div class="sg-val"><b class="nt">-</b><span>불량확률</span></div>',
            unsafe_allow_html=True)
    else:
        cls, tag, word, color = ("bad", "NG", "불량", BAD) if is_bad else ("good", "PASS", "정상", GOOD)
        lamps = ('<div class="lamp red on"></div><div class="lamp yel"></div><div class="lamp grn"></div>' if is_bad
                 else '<div class="lamp red"></div><div class="lamp yel"></div><div class="lamp grn on"></div>')
        angle = -90 + min(max(prob, 0.0), 1.0) * 180
        st.markdown(
            f'<div class="vrow"><div class="tower">{lamps}</div><div class="vbox {cls}"><div class="vk">{tag}</div><div class="vv">{word}</div></div></div>'
            f'<div class="sg"><div class="sg-arc"></div><div class="sg-ticks"></div><div class="sg-hole"></div><div class="sg-needle" style="transform: rotate({angle}deg)"></div><div class="sg-hub"></div>'
            f'<div class="sg-lab l">0</div><div class="sg-lab m">0.5</div><div class="sg-lab r">1.0</div></div>'
            f'<div class="sg-val"><b style="color:{color}">{prob:.1%}</b><span>불량확률 (0.5 이상이면 불량)</span></div>'
            f'<div class="rds"><div class="rd"><span>P(불량)</span><b>{prob:.4f}</b></div><div class="rd"><span>기준값</span><b>0.5000</b></div><div class="rd"><span>기준과의 차이</span><b style="color:{color}">{prob - 0.5:+.4f}</b></div></div>'
            f'<div class="row2"><span>사진</span><b>{html.escape(uploaded.name)}</b></div>',
            unsafe_allow_html=True,
        )

with save_area:
    if result is not None:
        st.write("")
        if st.button("결과를 DB에 저장", type="primary", width="stretch"):
            save_result(uploaded.name, result["label"], result["defect_prob"])
            st.success("저장했어요")

# ---- 이력 (저장이 끝난 뒤 읽기) ----
kwargs = {"limit": 1000} if "limit" in inspect.signature(get_history).parameters else {}
rows = list(get_history(**kwargs))
names = ["번호", "검사시각", "설비", "사진", "판정", "불량확률"]
if rows:
    df = pd.DataFrame(rows).rename(columns={"id": "번호", "inspected_at": "검사시각", "machine_id": "설비",
                                            "image_name": "사진", "label": "판정", "defect_prob": "불량확률"})
    if all(isinstance(c, int) for c in df.columns):
        df.columns = names[: len(df.columns)]
else:
    df = pd.DataFrame(columns=names)

total = len(df)
bad = int((df["판정"] == "불량").sum()) if total else 0
good = total - bad
rate = bad / total if total else 0.0

with top_area:
    st.markdown(
        '<div class="hmi-top"><div class="brand"><div class="hexw"><div class="hex"></div></div>'
        '<div><div class="ttl">병 입구 불량 판정 콘솔</div>'
        '<div class="sub">사진 한 장으로 정상/불량을 판정하고, 판정 근거와 검사 이력을 확인합니다</div></div></div>'
        '<div class="instr">'
        '<div class="ib"><span class="il">MODEL</span><span class="iv">ResNet18</span></div>'
        '<div class="ib"><span class="il">INPUT</span><span class="iv">224 × 224</span></div>'
        '<div class="ib"><span class="il">THRESHOLD</span><span class="iv">0.500</span></div>'
        '<div class="ib"><span class="il">DB</span><span class="iv on">● ONLINE</span></div>'
        '<div class="ib"><span class="il">MODE</span><span class="iv">사진 업로드</span></div></div></div>',
        unsafe_allow_html=True)

with kpi_area:
    cards = [("전체 검사", f"{total}", "nt", "k-nt", "저장된 판정 기준"), ("PASS (정상)", f"{good}", "ok", "k-ok", f"{(1 - rate):.1%}" if total else "-"),
             ("NG (불량)", f"{bad}", "ng", "k-ng", f"{rate:.1%}" if total else "-"), ("불량률", f"{rate:.1%}", "ng" if bad else "nt", "k-ng" if bad else "k-nt", "불량 ÷ 전체")]
    for col, (label, value, cls, kcls, sub) in zip(st.columns(4), cards):
        col.markdown(f'<div class="kpi {kcls}"><div class="kl">{label}</div><div class="kv {cls}">{value}</div><div class="ks">{sub}</div></div>',
                     unsafe_allow_html=True)

c1, c2, c3 = st.columns(3, gap="medium")
with c1:
    with st.container(border=True, key="panel_dist", height=275):
        st.markdown('<div class="ph"><span>판정 분포</span></div>', unsafe_allow_html=True)
        if total:
            pg = good / total * 100
            bg = f"conic-gradient({GOOD} 0 {pg}%, {BAD} {pg}% 100%)"
        else:
            bg = "#1F2A44"
        st.markdown(
            f'<div class="donutwrap"><div class="donut" style="background:{bg}"><div class="dhole"><b>{total}</b><span>전체</span></div></div>'
            f'<div class="leg"><div><span class="dot" style="background:{GOOD};color:{GOOD}"></span>정상 {good}건</div>'
            f'<div><span class="dot" style="background:{BAD};color:{BAD}"></span>불량 {bad}건</div></div></div>',
            unsafe_allow_html=True)
with c2:
    with st.container(border=True, key="panel_trend", height=275):
        st.markdown('<div class="ph"><span>불량확률 추이</span></div>', unsafe_allow_html=True)
        if total >= 2:
            trend = df[["번호", "불량확률"]].copy()
            trend["불량확률(%)"] = pd.to_numeric(trend["불량확률"], errors="coerce") * 100
            st.line_chart(trend.sort_values("번호").set_index("번호")["불량확률(%)"], height=170, color=BAD)
        else:
            st.markdown('<div class="note" style="padding:50px 0;text-align:center">이력이 2건 이상이면 표시됩니다</div>', unsafe_allow_html=True)
with c3:
    with st.container(border=True, key="panel_perf", height=275):
        st.markdown('<div class="ph"><span>모델 평가</span><span class="live">테스트 45장, 고정값</span></div>', unsafe_allow_html=True)
        bars = [("불량 재현율 (9/10)", 90.0), ("불량 정밀도", 100.0), ("정확도 (44/45)", 97.8)]
        st.markdown(
            "".join(f'<div class="pbar"><div class="pl"><span>{n}</span><b>{v:.1f}%</b></div><div class="trk"><div class="fil" style="width:{v}%"></div></div></div>' for n, v in bars)
            + '<div class="note">※ 첫 학습 모델 기준. 같은 코드로 재학습한 모델은 재현율 0.800이었습니다.</div>',
            unsafe_allow_html=True)

with st.container(border=True, key="panel_hist"):
    h1, h2 = st.columns([4, 1])
    h1.markdown('<div class="ph"><span>최근 검사 이력</span></div>', unsafe_allow_html=True)
    only_bad = h2.checkbox("불량만 보기")
    view = df[df["판정"] == "불량"] if only_bad else df
    show = view.head(50).copy()
    if len(show):
        show["불량확률"] = (show["불량확률"].astype(float) * 100).round(1).astype(str) + "%"
    styled = show.style.map(
        lambda v: f"color:{BAD};font-weight:700" if v == "불량" else (f"color:{GOOD};font-weight:700" if v == "정상" else ""),
        subset=["판정"],
    )
    st.dataframe(styled, width="stretch", hide_index=True)

st.caption("데이터: MVTec AD bottle (공개 데이터셋, 실제 설비 데이터 아님) · 히트맵은 판정 근거의 대략적 시각화입니다.")
