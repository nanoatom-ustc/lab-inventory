import streamlit as st
import pandas as pd
from datetime import date
import uuid
import os

# ---------- 页面配置 ----------
st.set_page_config(page_title="实验室耗材管理系统", layout="wide")

# ---------- 数据文件路径（云端持久化）----------
DATA_DIR = "data"
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.csv")
RECORDS_FILE = os.path.join(DATA_DIR, "records.csv")

# 创建数据目录
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------- 加载/初始化库存数据 ----------
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    else:
        # 初始数据
        return pd.DataFrame({
            "产品ID": ["FC001", "FC002", "ADJ001", "SLV001"],
            "产品名称": ["lbtek PRADFCD-11-B-APC", "lbtek PRADFCD-12-B-APC", 
                         "精密调整架", "M3套筒"],
            "规格": ["APC接口", "APC接口", "5轴", "不锈钢"],
            "分类": ["光纤准直器", "光纤准直器", "调整架", "套筒"],
            "当前数目": [8, 2, 12, 3]
        })

def load_records():
    if os.path.exists(RECORDS_FILE):
        return pd.read_csv(RECORDS_FILE)
    else:
        return pd.DataFrame(columns=[
            "记录ID", "耗材名称", "规格", "操作类型", "数量", 
            "填表人", "日期", "备注", "变更后库存"
        ])

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

def save_records(df):
    df.to_csv(RECORDS_FILE, index=False)

# 初始化 session_state
if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()
if "records" not in st.session_state:
    st.session_state.records = load_records()

# ---------- 辅助函数 ----------
def update_inventory(product_name, spec, operation, quantity):
    idx = st.session_state.inventory[
        (st.session_state.inventory["产品名称"] == product_name) & 
        (st.session_state.inventory["规格"] == spec)
    ].index
    
    if len(idx) == 0:
        st.error("未找到该耗材")
        return False
    
    current_qty = st.session_state.inventory.loc[idx[0], "当前数目"]
    
    if operation == "购买":
        new_qty = current_qty + quantity
    elif operation == "使用":
        if quantity > current_qty:
            st.warning(f"库存不足！当前只有 {current_qty} 个")
            return False
        new_qty = current_qty - quantity
    elif operation == "回收":
        new_qty = current_qty + quantity
    else:
        return False
    
    st.session_state.inventory.loc[idx[0], "当前数目"] = new_qty
    save_inventory(st.session_state.inventory)  # 保存到文件
    
    new_record = pd.DataFrame([{
        "记录ID": str(uuid.uuid4())[:8],
        "耗材名称": product_name,
        "规格": spec,
        "操作类型": operation,
        "数量": quantity,
        "填表人": st.session_state.get("username", "匿名"),
        "日期": date.today().strftime("%Y-%m-%d"),
        "备注": st.session_state.get("remark", ""),
        "变更后库存": new_qty
    }])
    st.session_state.records = pd.concat([st.session_state.records, new_record], ignore_index=True)
    save_records(st.session_state.records)  # 保存到文件
    return True

# ---------- 侧边栏：快速输入 ----------
with st.sidebar:
    st.header("📝 快速记录")
    
    product_options = st.session_state.inventory["产品名称"] + " (" + st.session_state.inventory["规格"] + ")"
    selected = st.selectbox("耗材", product_options, key="product_select")
    selected_name = selected.split(" (")[0]
    selected_spec = selected.split(" (")[1].rstrip(")")
    
    operation = st.radio("操作类型", ["➕ 购买", "➖ 使用", "♻️ 回收"], horizontal=True)
    operation_type = operation.split()[1]
    
    quantity = st.number_input("数量", min_value=1, value=1, step=1)
    username = st.text_input("填表人", value="", placeholder="例如：张三")
    remark = st.text_area("备注（选填）", placeholder="如：实验消耗、供应商等")
    
    if st.button("✅ 确认提交", use_container_width=True):
        if not username:
            st.error("请填写填表人")
        else:
            st.session_state["username"] = username
            st.session_state["remark"] = remark
            if update_inventory(selected_name, selected_spec, operation_type, quantity):
                st.success("记录成功！")
                st.rerun()

# ---------- 主界面 ----------
st.title("🧪 实验室耗材管理")

low_stock = st.session_state.inventory[st.session_state.inventory["当前数目"] < 5]
if not low_stock.empty:
    st.error("⚠️ **待采购提醒** 以下耗材库存低于5个，请及时采购！")
    for _, row in low_stock.iterrows():
        st.warning(f"• {row['产品名称']}（{row['规格']}）：仅剩 {row['当前数目']} 个")

def highlight_low_stock(row):
    if row["当前数目"] < 5:
        return ["background-color: #ffcccc"] * len(row)
    return [""] * len(row)

st.subheader("📊 当前库存概览")
styled_df = st.session_state.inventory.style.apply(highlight_low_stock, axis=1)
st.dataframe(styled_df, use_container_width=True, height=300)

st.subheader("📜 历史操作记录")
col1, col2 = st.columns(2)
with col1:
    filter_person = st.text_input("按填表人筛选", placeholder="输入姓名")
with col2:
    filter_date = st.date_input("按日期筛选", value=None)

filtered_records = st.session_state.records.copy()
if filter_person:
    filtered_records = filtered_records[filtered_records["填表人"].str.contains(filter_person, na=False)]
if filter_date:
    filtered_records = filtered_records[filtered_records["日期"] == filter_date.strftime("%Y-%m-%d")]

st.dataframe(filtered_records, use_container_width=True)

csv = filtered_records.to_csv(index=False).encode('utf-8-sig')
st.download_button("📥 导出筛选结果为CSV", csv, "lab_records.csv", "text/csv")