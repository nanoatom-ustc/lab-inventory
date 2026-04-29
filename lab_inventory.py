import streamlit as st
import pandas as pd
from datetime import date
import uuid
from streamlit_gsheets import GSheetsConnection

# ---------- 页面配置 ----------
st.set_page_config(page_title="8004 实验室耗材管理系统", layout="wide")

# ---------- Google 表格连接配置 ----------
# ⚠️ 务必将下方的网址替换为你真实的 8004_Lab_System 表格网址
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1itHa5TE2WnZcCVneuEwaFcHr8c4AzpD2L-WmrJ3dGZQ/edit"

# 建立与 Google Sheets 的连接
conn = st.connection("gsheets", type=GSheetsConnection)

# ---------- 数据读取逻辑 ----------
def load_inventory():
    try:
        # ttl=0 确保每次刷新页面都会从云端拉取最新数据，防止多人同时操作时数据滞后
        df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="inventory", ttl=0)
        return df.dropna(how="all")
    except Exception as e:
        st.error(f"读取库存表失败，请检查链接和 Secrets 配置: {e}")
        return pd.DataFrame(columns=["产品名称", "当前数目", "分类"])

def load_records():
    try:
        # 注意：这里 worksheet 参数为 record，与你 Google 表格下方的标签页名称完全对应
        df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="record", ttl=0)
        return df.dropna(how="all")
    except Exception as e:
        st.error(f"读取流水表失败: {e}")
        return pd.DataFrame(columns=["记录ID", "产品名称", "操作类型", "数量", "填表人", "日期", "备注", "变更后库存"])

# 初始化 Session State
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()
if "records" not in st.session_state:
    st.session_state.records = load_records()

# ---------- 核心功能函数 ----------
def update_inventory(product_name, operation, quantity, user, note):
    idx = st.session_state.inventory[st.session_state.inventory["产品名称"] == product_name].index
    if len(idx) == 0:
        st.error("未找到该耗材")
        return False
    
    current_qty = st.session_state.inventory.loc[idx[0], "当前数目"]
    
    if operation == "购买" or operation == "回收":
        new_qty = current_qty + quantity
    elif operation == "使用":
        if quantity > current_qty:
            st.warning(f"库存不足！当前仅剩 {current_qty}")
            return False
        new_qty = current_qty - quantity
    
    # 1. 更新本地缓存
    st.session_state.inventory.loc[idx[0], "当前数目"] = new_qty
    
    # 2. 推送库存更新到 Google 表格
    conn.update(spreadsheet=SPREADSHEET_URL, worksheet="inventory", data=st.session_state.inventory)
    
    # 3. 增加流水记录
    new_record = pd.DataFrame([{
        "记录ID": str(uuid.uuid4())[:8],
        "产品名称": product_name,
        "操作类型": operation,
        "数量": quantity,
        "填表人": user,
        "日期": date.today().strftime("%Y-%m-%d"),
        "备注": note,
        "变更后库存": new_qty
    }])
    st.session_state.records = pd.concat([st.session_state.records, new_record], ignore_index=True)
    
    # 4. 推送流水更新到 Google 表格
    conn.update(spreadsheet=SPREADSHEET_URL, worksheet="record", data=st.session_state.records)
    
    return True

def add_new_product(name, category, qty):
    if name in st.session_state.inventory["产品名称"].values:
        st.error("该产品已存在！")
        return False
    new_item = pd.DataFrame([{"产品名称": name, "当前数目": qty, "分类": category}])
    st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
    
    # 推送新产品到云端 Google 表格
    conn.update(spreadsheet=SPREADSHEET_URL, worksheet="inventory", data=st.session_state.inventory)
    return True

# ---------- 侧边栏交互 ----------
with st.sidebar:
    st.header("📝 快速记录")
    selected_product = st.selectbox("选择零件", st.session_state.inventory["产品名称"])
    op = st.radio("操作", ["使用", "购买", "回收"], horizontal=True)
    num = st.number_input("数量", min_value=1, value=1)
    user = st.text_input("填表人")
    note = st.text_area("备注")
    
    if st.button("提交记录", use_container_width=True):
        if user and update_inventory(selected_product, op, num, user, note):
            st.success("记录已成功同步至云端！")
            st.rerun()
        elif not user:
            st.error("请输入填表人")

    st.divider()
    st.header("✨ 新增产品")
    new_name = st.text_input("零件名称")
    new_cat = st.text_input("分类", value="光学元件")
    new_qty = st.number_input("初始库存", min_value=0, value=0)
    if st.button("添加至库存系统"):
        if new_name and add_new_product(new_name, new_cat, new_qty):
            st.success(f"已添加 {new_name} 并同步至云端")
            st.rerun()

# ---------- 主界面展示 ----------
st.title("🧪 8004 实验室耗材管理")

st.info("📱 **手机用户**：请点击左上角的 **>>** 菜单按钮，打开「快速记录」表单！")

# 低库存报警
low_stock = st.session_state.inventory[st.session_state.inventory["当前数目"] < 3]
if not low_stock.empty:
    for _, row in low_stock.iterrows():
        st.error(f"🚨 缺货预警：{row['产品名称']} 仅剩 {row['当前数目']} 个！")

st.subheader("📊 当前库存")     
st.dataframe(st.session_state.inventory, use_container_width=True)

st.subheader("📜 历史流水")
st.dataframe(st.session_state.records.sort_index(ascending=False), use_container_width=True)

st.subheader("🛠️ 库存后台管理")
with st.expander("点击展开管理面板（仅限修正错误或更改零件名称）"):
    st.info("""
    💡 **功能说明**：
    1. **修正名称**：若发现零件型号录入有误，可直接在此修改产品名称或分类。
    2. **库存校准**：若物理库存与系统数值不符，可手动修改“当前数目”进行强制对齐。
    3. **行操作**：选中行后按 `Delete` 键可删除该产品。
    
    ⚠️ **注意**：修改后务必点击下方按钮保存至云端，否则刷新后会丢失。日常领用请优先使用侧边栏。
    """)
    
    edited_df = st.data_editor(
        st.session_state.inventory,
        num_rows="dynamic",
        use_container_width=True,
        key="inventory_editor"
    )
    
    if st.button("💾 确认并覆盖云端数据", use_container_width=True):
        st.session_state.inventory = edited_df
        # 将后台管理面板的修改强制同步至云端
        conn.update(spreadsheet=SPREADSHEET_URL, worksheet="inventory", data=edited_df)
        st.success("云端基础数据库已成功更新！")
        st.rerun()
