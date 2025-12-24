import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# --- 页面设置 ---
st.set_page_config(page_title="提示词云同步版", layout="wide", page_icon="☁️")
st.title("☁️ 团队提示词库 (自动同步 Google Sheets)")

# --- 连接谷歌表格 ---
# 建立连接
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 函数：读取数据 ---
def fetch_data():
    try:
        # ttl=0 代表不缓存，每次强制拉取最新数据
        df = conn.read(ttl=0)
        # 如果是空表，初始化列名
        if df.empty:
            return pd.DataFrame(columns=["category", "title", "tags", "content"])
        # 填充空值防止报错
        return df.fillna("")
    except:
        return pd.DataFrame(columns=["category", "title", "tags", "content"])

# --- 侧边栏：新增 ---
CATEGORIES = ["🤖 AI绘画", "📝 文案写作", "💻 编程辅助", "🎬 视频脚本", "🗑️ 未分类"]

with st.sidebar:
    st.header("➕ 新增")
    new_cat = st.selectbox("分类", CATEGORIES)
    new_title = st.text_input("标题")
    new_tags = st.text_input("标签")
    new_content = st.text_area("内容", height=200)
    
    if st.button("💾 保存并同步", type="primary"):
        if new_title and new_content:
            with st.spinner("正在同步到 Google Sheets..."):
                # 1.以此为基础读取旧数据
                current_df = fetch_data()
                # 2.创建新行
                new_row = pd.DataFrame([{
                    "category": new_cat,
                    "title": new_title,
                    "tags": new_tags,
                    "content": new_content
                }])
                # 3.合并
                updated_df = pd.concat([current_df, new_row], ignore_index=True)
                # 4.写入
                conn.update(data=updated_df)
                st.success("✅ 保存成功！")
                time.sleep(1)
                st.rerun()
        else:
            st.error("写点东西再保存嘛")

# --- 主界面：展示 ---
st.divider()
df = fetch_data()

# 搜索
search = st.text_input("🔍 搜索...", placeholder="输入关键词")
if search:
    mask = df["title"].str.contains(search, case=False) | df["tags"].str.contains(search, case=False)
    display_df = df[mask]
else:
    display_df = df

# 展示列表
if display_df.empty:
    st.info("表格是空的，快去左侧添加第一条数据！")
else:
    # 倒序展示
    for index, row in display_df.iloc[::-1].iterrows():
        with st.expander(f"[{row['category']}] {row['title']}"):
            st.code(row['content'])
            st.caption(f"标签: {row['tags']}")
            # 删除功能
            if st.button("🗑️ 删除此条", key=f"del_{index}"):
                with st.spinner("正在删除..."):
                    df_dropped = df.drop(index)
                    conn.update(data=df_dropped)
                    st.rerun()
