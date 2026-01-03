import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import time

# ---------------------------------------------------------
# 1. 页面配置
# ---------------------------------------------------------
st.set_page_config(
    page_title="团队提示词库",
    page_icon="☁️",
    layout="wide"
)

# 标题
st.title("☁️ 团队提示词库 (自动同步 Google Sheets)")
st.markdown("---")

# ---------------------------------------------------------
# 2. 连接 Google Sheets
# ---------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

# 定义分类
CATEGORIES = ["🌱 自我成长", "💰 投资理财", "📝 文案撰写", "🎨 图片生成", "💻 编程开发", "🌍 语言翻译", "📊 办公效率", "🗑️ 未分类"]

# 读取数据函数 (加缓存，但也允许手动强制刷新)
def get_data():
    try:
        df = conn.read(worksheet="Sheet1", usecols=[0, 1, 2, 3], ttl=0)
        # 确保列名正确，防止空表报错
        if df.empty:
            return pd.DataFrame(columns=["category", "title", "tags", "content"])
        # 处理可能存在的空值，避免报错
        df = df.fillna("")
        return df
    except Exception as e:
        st.error(f"无法连接到表格，请检查网络或配置: {e}")
        return pd.DataFrame(columns=["category", "title", "tags", "content"])

# 获取当前数据
df = get_data()

# ---------------------------------------------------------
# 3. 侧边栏：功能区 (新增 vs 修改)
# ---------------------------------------------------------
st.sidebar.header("🛠️ 操作面板")
mode = st.sidebar.radio("选择模式：", ["➕ 新增提示词", "🔧 修改/删除已存"])

st.sidebar.markdown("---")

if mode == "➕ 新增提示词":
    st.sidebar.subheader("📝 添加新内容")
    
    # 输入框
    new_category = st.sidebar.selectbox("分类", CATEGORIES)
    new_title = st.sidebar.text_input("标题", placeholder="例如：赛博朋克风格")
    new_tags = st.sidebar.text_input("标签", placeholder="例如：科幻, 霓虹灯")
    new_content = st.sidebar.text_area("内容 (Prompt)", height=200, placeholder="在这里粘贴你的提示词...")

    # 保存按钮
    if st.sidebar.button("💾 保存并同步", type="primary"):
        if not new_title or not new_content:
            st.sidebar.warning("⚠️ 标题和内容不能为空！")
        else:
            # 构造新数据
            new_data = pd.DataFrame([{
                "category": new_category,
                "title": new_title,
                "tags": new_tags,
                "content": new_content
            }])
            
            # 合并并更新
            updated_df = pd.concat([df, new_data], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.sidebar.success("✅ 保存成功！")
            time.sleep(1)
            st.rerun()

elif mode == "🔧 修改/删除已存":
    st.sidebar.subheader("🔍 查找并编辑")
    
    # 下拉菜单：选择要修改的条目
    # 这里的逻辑是生成一个列表供用户选择： "标题 (分类)"
    if df.empty:
        st.sidebar.warning("表格是空的，没法修改哦。")
    else:
        select_options = [f"{row['title']} ({row['category']})" for index, row in df.iterrows()]
        selected_option = st.sidebar.selectbox("选择要修改的提示词", select_options)
        
        # 找到用户选的是哪一行
        # 这种匹配方式简单有效，只要标题不完全重复
        selected_index = select_options.index(selected_option)
        selected_row = df.iloc[selected_index]

        st.sidebar.markdown("---")
        st.sidebar.write("👇 **在此修改内容**")

        # 预填充旧数据
        edit_category = st.sidebar.selectbox("分类", CATEGORIES, index=CATEGORIES.index(selected_row['category']) if selected_row['category'] in CATEGORIES else 7)
        edit_title = st.sidebar.text_input("标题", value=selected_row['title'])
        edit_tags = st.sidebar.text_input("标签", value=selected_row['tags'])
        edit_content = st.sidebar.text_area("内容", value=selected_row['content'], height=200)

        col1, col2 = st.sidebar.columns(2)
        
        # 更新按钮
        with col1:
            if st.button("🔄 确认更新", type="primary"):
                # 直接修改 DataFrame 中对应行的数据
                df.at[selected_index, 'category'] = edit_category
                df.at[selected_index, 'title'] = edit_title
                df.at[selected_index, 'tags'] = edit_tags
                df.at[selected_index, 'content'] = edit_content
                
                # 推送回 Google Sheets
                conn.update(worksheet="Sheet1", data=df)
                st.sidebar.success("已更新！")
                time.sleep(1)
                st.rerun()
        
        # 删除按钮
        with col2:
            if st.button("🗑️ 删除此条"):
                # 删除对应行
                df = df.drop(selected_index)
                conn.update(worksheet="Sheet1", data=df)
                st.sidebar.error("已删除！")
                time.sleep(1)
                st.rerun()

# ---------------------------------------------------------
# 4. 主界面：展示与搜索
# ---------------------------------------------------------
search_term = st.text_input("🔍 搜索...", placeholder="输入关键词查找...")

# 过滤逻辑
if search_term:
    mask = df.apply(lambda x: x.astype(str).str.contains(search_term, case=False).any(), axis=1)
    display_df = df[mask]
else:
    display_df = df

# 展示数据
if display_df.empty:
    st.info("👋 还没有数据，或者没有搜到结果。快去左侧添加一条吧！")
else:
    for index, row in display_df.iterrows():
        with st.expander(f"📌 {row['title']}  |  🏷️ {row['category']}"):
            st.code(row['content'], language="markdown")
            st.caption(f"标签: {row['tags']}")