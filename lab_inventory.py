import streamlit as st
import pandas as pd
from datetime import date
import uuid
import os

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="8004 实验室耗材管理系统", 
    layout="wide", 
    page_icon="⚛️"
)

# ---------- 自定义 UI 样式 (量子精密测量主题) ----------
def inject_theme():
    st.markdown("""
        <style>
        /* 全局深色背景，模拟暗室环境 */
        .stApp {
            background: radial-gradient(circle at top right, #0a192f, #00050a);
            color: #e0e0e0;
        }
        
        /* 标题与副标题：激光荧光感 */
        h1, h2, h3 {
            color: #00f2ff !important;
            text-shadow: 0 0 12px rgba(0, 242, 255, 0.4);
            font-family: 'Courier New', monospace;
        }

        /* 侧边栏：磨砂质感 */
        [data-testid="stSidebar"] {
            background-color: rgba(20, 30, 48, 0.9);
            border-right: 1px solid #00f2ff33;
        }

        /* 按钮：金属/科技感 */
        .stButton>button {
            background-color: rgba(0, 242, 255, 0.1);
            color: #00f2ff;
            border: 1px solid #00f2ff;
            border-radius: 4px;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #00f2ff;
            color: #000;
            box-shadow: 0 0 20px #00f2ff;
        }

        /* 数据编辑器与表格优化 */
        .stDataFrame {
            border: 1px solid #1e293b;
        }

        /* 提示框颜色微调 */
        .stAlert {
            background-color: rgba(0, 0, 0, 0.3);
            border: 1px solid #30363d;
        }
        </style>
    """, unsafe_allow_index=True)

inject_theme()

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
            st.warning(f"库存不足！当前仅剩 {current_qty}")
            return False
        new_qty = current_qty - quantity
    
    st.session_state.inventory.loc[idx[0], "当前数目"] = new_qty
    st.session_state.inventory.to_csv(INVENTORY_FILE, index=False)
    
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
    st.markdown("### ⚛️ 实验员操作台")
    st.header("⚡ 快速记录")
    selected_product = st.selectbox("选择零件", st.session_state.inventory["产品名称"])
    op = st.radio("操作类型", ["使用", "购买", "回收"], horizontal=True)
    num = st.number_input("数量", min_value=1, value=1)
    user = st.text_input("填表人 (User ID)")
    note = st.text_area("备注 (Experimental Note)")
    
    if st.button("🛰️ 提交数据更新", use_container_width=True):
        if user and update_inventory(selected_product, op, num, user, note):
            st.success("系统参数已更新")
            st.rerun()
        elif not user:
            st.error("请输入填表人")

    st.divider()
    st.header("🔭 新增准直/机械件")
    new_name = st.text_input("零件名称")
    new_cat = st.text_input("分类", value="机械件")
    new_qty = st.number_input("初始库存", min_value=0, value=0)
    if st.button("➕ 录入系统"):
        if new_name and add_new_product(new_name, new_cat, new_qty):
            st.success(f"已录入: {new_name}")
            st.rerun()

# ---------- 主界面展示 ----------
# 顶部装饰栏
st.markdown("""
    <div style="background-color: rgba(0, 242, 255, 0.1); padding: 10px; border-radius: 5px; border-left: 5px solid #00f2ff; margin-bottom: 20px;">
        <small>📡 系统状态: <b>相干锁定 (Coherent Locked)</b> | 💡 环境光压: <b>正常</b> | ❄️ 原子俘获: <b>运行中</b></small>
    </div>
""", unsafe_allow_index=True)

st.title("🧪 8004 实验室耗材管理")

# 移动端引导
st.info("📱 **Mobile Tip**：点击左上角 **>>** 按钮进入快速操作面板。")

# 低库存报警 (红色呼吸感)
low_stock = st.session_state.inventory[st.session_state.inventory["当前数目"] < 3]
if not low_stock.empty:
    for _, row in low_stock.iterrows():
        st.error(f"🚨 **库存能级过低预警**：{row['产品名称']} 仅剩 **{row['当前数目']}** 个！", icon="⚠️")

# 数据看板区
tab1, tab2 = st.tabs(["📊 实时库存状态", "📜 实验流水日志"])

with tab1:
    st.subheader("🛠️ 库存后台管理")
    with st.expander("⚙️ 系统校准面板 (仅用于修正原始数据)"):
        st.info("💡 日常领用请使用左侧操作台。手动修改此处将强制对齐物理库存。")
        edited_df = st.data_editor(
            st.session_state.inventory,
            num_rows="dynamic",
            use_container_width=True,
            key="inventory_editor"
        )
        if st.button("💾 确认并写入数据库", use_container_width=True):
            st.session_state.inventory = edited_df
            st.session_state.inventory.to_csv(INVENTORY_FILE, index=False)
            st.success("原始数据库已重置。")
            st.rerun()
            
    st.dataframe(st.session_state.inventory, use_container_width=True)

with tab2:
    st.subheader("📑 历史记录记录")
    st.dataframe(st.session_state.records.sort_index(ascending=False), use_container_width=True)

# 底部页脚
st.markdown("---")
st.markdown("<center><small>8004 Laboratory | Quantum Precision Measurement Group</small></center>", unsafe_allow_index=True)
