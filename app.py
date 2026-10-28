# app.py: 검사 이력 확인 + 사진 업로드 판정 대시보드
import streamlit as st
import pandas as pd
from PIL import Image

from model import predict, gradcam_overlay
from db import save_result, get_history

st.set_page_config(page_title="제조 불량 판정 대시보드", layout="wide")
st.title("제조 불량 판정 대시보드")

# 1) 사진 업로드 -> 판정 -> DB 저장
st.subheader("사진 판정")
uploaded = st.file_uploader("병 입구 사진을 올려 주세요", type=["png", "jpg", "jpeg"])

if uploaded is not None:
    img = Image.open(uploaded)
    result = predict(img)

    if result["label"] == "불량":
        st.error(f"판정: 불량 (불량확률 {result['defect_prob']:.1%})")
    else:
        st.success(f"판정: 정상 (불량확률 {result['defect_prob']:.1%})")

    if result["label"] == "불량":
        c_a, c_b = st.columns(2)
        c_a.image(img, caption=uploaded.name, width=380)
        c_b.image(
            gradcam_overlay(img),
            caption="판정 근거 시각화 (Grad-CAM, 대략적 영역이며 정확한 위치 검출이 아님)",
            width=380,
        )
    else:
        st.image(img, caption=uploaded.name, width=380)

    if st.button("결과를 DB에 저장"):
        save_result(uploaded.name, result["label"], result["defect_prob"])
        st.success("저장했어요")

# 2) 요약 숫자
rows = get_history(limit=1000)
df = pd.DataFrame(
    rows,
    columns=["번호", "검사시각", "설비", "사진", "판정", "불량확률"],
)

st.subheader("요약")
total = len(df)
defects = int((df["판정"] == "불량").sum()) if total else 0
rate = defects / total if total else 0
c1, c2, c3 = st.columns(3)
c1.metric("전체 검사", total)
c2.metric("불량", defects)
c3.metric("불량률", f"{rate:.1%}")

# 3) 최근 이력 (퍼센트 표시 + 불량만 보기)
st.subheader("최근 검사 이력")
df["불량확률"] = (df["불량확률"] * 100).round(1).astype(str) + "%"
only_defect = st.checkbox("불량만 보기")
view = df[df["판정"] == "불량"] if only_defect else df
st.dataframe(view.head(50), width="stretch", hide_index=True)