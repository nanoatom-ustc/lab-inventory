import streamlit as st
import pandas as pd
from datetime import date
import uuid
import os

# ---------- 页面配置 ----------
st.set_page_config(page_title="8004 实验室耗材管理系统", layout="wide")

# ---------- 数据文件路径 ----------
DATA_DIR = "data"
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.csv")
RECORDS_FILE = os.path.join(DATA_DIR, "records.csv")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------- 数据初始化逻辑 ----------
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    else:
        # 基于上传文件计算的初始库存数据
        initial_data = {
            "产品名称": [
                "lbtek PRADFCD-11-B-APC", "lbtek MT-AM05S3", "OMPH12D-20M", "OMPH12D-40M",
                "Y形压板", "圆形底座", "z轴", "笼板 SM05", "笼板 SM1", "笼板 25.4通孔",
                "笼式玻片架", "笼式45度反射镜架", "笼式90度反射镜架", "BD架", "PBS架 M05",
                "PBS 10M", "反射镜架（新）", "可变光阑"
            ],
            "当前数目": [8, 11, 21, 45, 27, 5, 12, 2, 30, 1, 2, 8, 6, 20, 5, 20, 39, 8],
            "分类": ["光纤准直器", "准直器调整架", "套筒", "套筒", "压板", "底座", "位移台", "笼板", "笼板", "笼板", "架子", "架子", "架子", "架子", "架子", "架子", "架子", "光阑"]
        }
        df = pd.DataFrame(initial_data)
        df.to_csv(INVENTORY_FILE, index=False)
        return df

def load_records():
    if os.path.exists(RECORDS_FILE):
        return pd.read_csv(RECORDS_FILE)
    else:
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
            st.warning(f"库存不足！当前仅剩 {current_qty} [cite: 1, 2]")
            return False
        new_qty = current_qty - quantity
    
    # 更新库存
    st.session_state.inventory.loc[idx[0], "当前数目"] = new_qty
    st.session_state.inventory.to_csv(INVENTORY_FILE, index=False)
    
    # 增加记录
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
    st.session_state.records.to_csv(RECORDS_FILE, index=False)
    return True

def add_new_product(name, category, qty):
    if name in st.session_state.inventory["产品名称"].values:
        st.error("该产品已存在！")
        return False
    new_item = pd.DataFrame([{"产品名称": name, "当前数目": qty, "分类": category}])
    st.session_state.inventory = pd.concat([st.session_state.inventory, new_item], ignore_index=True)
    st.session_state.inventory.to_csv(INVENTORY_FILE, index=False)
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
            st.success("记录已更新")
            st.rerun()
        elif not user:
            st.error("请输入填表人")

    st.divider()
    st.header("✨ 新增产品")
    new_name = st.text_input("零件名称")
    new_cat = st.text_input("分类", value="机械件")
    new_qty = st.number_input("初始库存", min_value=0, value=0)
    if st.button("添加至库存系统"):
        if new_name and add_new_product(new_name, new_cat, new_qty):
            st.success(f"已添加 {new_name}")
            st.rerun()

# ---------- 主界面展示 ----------
st.title("🧪 8004 实验室耗材管理")

# 移动端引导提示（让用户知道侧边栏在哪）
st.info("📱 **手机用户**：请点击左上角的 **☰** 菜单按钮，打开「快速记录」表单！")

# 低库存报警
low_stock = st.session_state.inventory[st.session_state.inventory["当前数目"] < 3]
if not low_stock.empty:
    for _, row in low_stock.iterrows():
        st.error(f"🚨 缺货预警：{row['产品名称']} 仅剩 {row['当前数目']} 个！")

st.subheader("📊 当前库存")
st.subheader("🛠️ 库存后台管理")
with st.expander("点击展开管理面板（仅限修正错误或更改零件名称）"):
    # 添加醒目的功能提示
    st.info("""
    💡 **功能说明**：
    1. **修正名称**：若发现零件型号录入有误，可直接在此修改产品名称或分类。
    2. **库存校准**：若物理库存与系统数值不符，可手动修改“当前数目”进行强制对齐。
    3. **行操作**：选中行后按 `Delete` 键可删除该产品。
    
    ⚠️ **注意**：日常的领用或采购请优先使用侧边栏的“快速记录”，以便保留操作流水。
    """)
    
    # 使用 data_editor
    edited_df = st.data_editor(
        st.session_state.inventory,
        num_rows="dynamic",
        use_container_width=True,
        key="inventory_editor"
    )
    
    # 确认保存按钮
    if st.button("💾 确认并覆盖原始数据", use_container_width=True):
        st.session_state.inventory = edited_df
        st.session_state.inventory.to_csv(INVENTORY_FILE, index=False)
        st.success("基础数据库已成功更新！")
        st.rerun()
        
st.dataframe(st.session_state.inventory, use_container_width=True)

st.subheader("📜 历史流水")
st.dataframe(st.session_state.records.sort_index(ascending=False), use_container_width=True)
