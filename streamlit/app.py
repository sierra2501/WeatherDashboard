import altair as alt
from datetime import datetime
import os
import pandas as pd
import re
import requests
import streamlit as st
import sys
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
weather_dir = os.path.join(current_dir, "..")
sys.path.append(weather_dir)

from main import main as fetch_weather_main  # Weather/main.py の main() 関数をインポート

# app.py から見て一つ上の階層(project/)をパスに追加
sys.path.append(str(Path(__file__).resolve().parent.parent))

from package import db

key_update = 'teiji_choki'

st.set_page_config(
    page_title="お天気ダッシュボード",
    page_icon="☀️",
    initial_sidebar_state="auto",
    layout="wide",
)

hide_menu_style = """
        <style>
            header {visibility: hidden; height: 0px; padding: 0px;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .block-container {
                padding-top: 1rem;
                padding-bottom: 1rem;
                padding-left: 2rem;
                padding-right: 2rem;
            }
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# =================================================
# 文章中のキーワードから代表アイコンを判定(優先順位あり)
def get_weather_icons(text, count=1):
    keywords_to_icon = [
        ("晴れ", "☀️"),
        ("くもり", "☁️"),
        ("雨", "🌧️"),
        ("雪", "❄️"),
        ("雷", "⛈️"),
    ]

    positions = []
    for keyword, icon in keywords_to_icon:
        idx = text.find(keyword)
        if idx != -1:
            positions.append((idx, icon))

    positions.sort(key=lambda x: x[0])
    icons = [icon for _, icon in positions[:count]]

    return " ".join(icons) if icons else "❓"
# =================================================
def makeDF0(data):
    df0 = pd.DataFrame(
        {
            "weather": data[0]["weather"],
            "wind": data[0]["wind"],
            "wave": data[0]["wave"],
        },
        index=pd.to_datetime(data[0]["time"]),
    )
    df0["icon"] = df0["weather"].apply(lambda x: get_weather_icons(x, count=2))

    st.subheader("3日間の天気")

    cols = st.columns(len(df0), gap="large")
    for col, (日付, row) in zip(cols, df0.iterrows()):
        with col:
            st.markdown(f"**{日付.strftime('%m/%d')}**")
            st.markdown(f"<div style='font-size:40px; text-align:center'>{row['icon']}</div>", unsafe_allow_html=True)

            st.markdown(
                f"<div style='height:100px; overflow:hidden; font-size:14px;'>{row['weather']}</div>",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"<div style='height:50px; overflow:hidden; font-size:12px;'>風：{row['wind']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='height:30px; overflow:hidden; font-size:12px;'>波：{row['wave']}</div>",
                unsafe_allow_html=True,
            )

# ---------------------------------------
def makeDF1(data):
    df1 = pd.DataFrame(data[1]["pop"], index=data[1]["time"])
    df1.index = pd.to_datetime(df1.index)
    df1 = df1.reset_index().rename(columns={"index": "time", 0: "pop"})

    # 全角数字→半角数字に変換してから、「パーセント」を取り除く
    df1["pop"] = (
        df1["pop"]
        .astype(float)
    )

    chart = (
        alt.Chart(df1)
        .mark_bar(size=30)
        .encode(
            x=alt.X("time:T",title="日時",axis=alt.Axis(format="%m/%d %H:%M",labelAngle=0,values=df1["time"].tolist())),
            y=alt.Y("pop:Q",title="降水確率（％）",scale=alt.Scale(domain=[0, 100]),axis=alt.Axis(values=list(range(0, 101, 10)))),
        )
    )

    st.subheader("降水確率")
    st.altair_chart(chart, use_container_width=True)

# ---------------------------------------
def makeDF2(data):
    st.subheader("気温")
    n = min(len(data[2]["time"]), len(data[2]["temp_min"]), len(data[2]["temp_max"]), len(data[2]["temp_max2"]))
    cols = st.columns(n)
    for col, dt, mn, mx, mx2 in zip(
        cols,
        data[2]["time"][:n],
        data[2]["temp_min"][:n],
        data[2]["temp_max"][:n],
        data[2]["temp_max2"][:n],
    ):
        with col:
            st.markdown(f"**{pd.to_datetime(dt).strftime('%m/%d')}**")
            st.metric(label="朝の最低気温", value=f"{mn}℃")
            st.metric(label="日中の最高気温", value=f"{mx}℃")
            st.metric(label="最高気温", value=f"{mx2}℃")

# ---------------------------------------
def makeDF3(data):
    df3 = pd.DataFrame(data[3]["weather_3hour"],index=data[3]["time"])
    df3.index = pd.to_datetime(df3.index)
    df3 = df3.reset_index().rename(columns={"index": "time", 0: "weather"})
    df3["icon"] = df3["weather"].apply(lambda x: get_weather_icons(x, count=1))

    st.subheader("卓越天気")
    cols = st.columns(len(df3))

    prev_date = None
    for col, (_, row) in zip(cols, df3.iterrows()):
        current_date = row["time"].date()
        is_new_day = prev_date != current_date
        prev_date = current_date

        with col:
            border_style = "border-left: 2px solid #999; padding-left: 8px;" if is_new_day and col != cols[0] else ""

            date_line = row["time"].strftime("%m/%d") if is_new_day else "&nbsp;"
            time_line = row["time"].strftime("%H:%M")

            st.markdown(
                f"""
                <div style='{border_style}'>
                    <div style='height:20px; font-size:14px;'><strong>{date_line}</strong></div>
                    <div style='height:20px; font-size:14px;'><strong>{time_line}</strong></div>
                    <div style='font-size:32px; text-align:center'>{row['icon']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------------------------------------
def makeDF4(data):
    df4 = pd.DataFrame(data[4]["temp_3hour"],index=data[4]["time"])
    df4 = df4.apply(pd.to_numeric, errors="coerce")  # 文字列→数値に変換
    df4.index = pd.to_datetime(df4.index)  # datetime型のまま保持
    df4 = df4.reset_index().rename(columns={"index": "time", 0: "temp_3hour"})
    chart = (
        alt.Chart(df4)
        .mark_line(point=True)
        .encode(
            x=alt.X("time:T", title="日時", axis=alt.Axis(format="%m/%d %H:%M", labelAngle=0)),
            y=alt.Y("temp_3hour:Q",title="気温（℃）"),
        )
    )
    st.subheader("気温")
    st.altair_chart(chart, use_container_width=True)

# =================================================
def main():
    # ---------------------------------------------
    # 更新ボタン 
    # ---------------------------------------------
    if st.button("更新",type="primary"):
        with st.spinner("取得中..."):
            try:
                fetch_weather_main()
                st.toast("更新が完了しました", icon="✅")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
    # ---------------------------------------------
    # 更新情報の取得
    # ---------------------------------------------
    res = db.getDocumentUpdate()
    if res == {}:
        logger.error("updateのドキュメント取得に失敗しました")
        logger.info('処理終了')
        return
    elif res.status_code >= 400:
        logger.error(str(res.status_code) + ' ' + str(res.json()))
        logger.info('処理終了')
        return
    else:
        dic_update = res.json()
        dt = datetime.fromisoformat(dic_update[key_update]["update"])
    # ---------------------------------------------
    # データの取得
    # ---------------------------------------------
    data = db.getLatestTenki()
    gaikyo = db.getLatestGaikyo()
    # ---------------------------------------------
    # データの表示
    # ---------------------------------------------
    st.title("お天気ダッシュボード")
    st.write(f"更新：{dt.strftime('%Y年%m月%d日 %H時%M分')}")
    st.space(size="small")
    
    st.header("府県天気概況", divider="gray")
    st.write(gaikyo)
    st.space(size="small")
    
    col1, col2 = st.columns(2, gap="xlarge")
    with col1:
        st.header("天気予報", divider="gray")
        makeDF0(data)
        st.space(size="small")
        with st.container():
            col11, col12 = st.columns([1,3])
            with col11:
                makeDF2(data)
            with col12:
                makeDF1(data)
    with col2:
        st.header("3時間毎の予報", divider="gray")
        makeDF3(data)
        st.space(size="small")
        makeDF4(data)

# =================================================
main()