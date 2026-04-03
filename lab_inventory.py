import streamlit as st
import pandas as pd
from datetime import date
import uuid
import os

# ---------- 页面配置 ----------
st.set_page_config(
    page_title="8004 实验室耗材管理系统", 
    page_icon="🔬",
    layout="wide"
)

# ---------- 自定义CSS - 量子光学主题（仅视觉，不改文字）----------
st.markdown("""
<style>
    /* 主背景 - 深邃星空蓝黑渐变 */
    .stApp {
        background: linear-gradient(135deg, #0a0f1e 0%, #0d1525 50%, #0a0f1e 100%);
    }
    
    /* 主标题样式 - 冷光科技感 */
    h1 {
        color: #00d4ff !important;
        text-shadow: 0 0 20px rgba(0,212,255,0.3);
        font-weight: bold !important;
        border-bottom: 2px solid rgba(0,212,255,0.3);
        padding-bottom: 15px;
    }
    
    /* 子标题 */
    h2, h3 {
        color: #7c3aed !important;
        border-left: 4px solid #00d4ff;
        padding-left: 15px;
    }
    
    /* 卡片效果 - 玻璃态 */
    .stDataFrame, .stExpander, .element-container {
        background: rgba(15, 25, 45, 0.6);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(0,212,255,0.2);
    }
    
    /* 侧边栏 - 深邃风格 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1e 0%, #0d1525 100%);
        border-right: 1px solid rgba(0,212,255,0.2);
    }
    
    /* 按钮 - 科技感 */
    .stButton > button {
        background: linear-gradient(90deg, #1e2a4a, #2d3a5a);
        color: #00d4ff;
        border: 1px solid #00d4ff;
        border-radius: 25px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(90deg, #00d4ff, #7c3aed);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0,212,255,0.4);
    }
    
    /* 预警框 */
    .stAlert {
        background: linear-gradient(90deg, rgba(255,50,50,0.2), rgba(255,0,0,0.1));
        border-left: 4px solid #ff3366;
    }
    
    /* 信息框 */
    .stInfo {
        background: linear-gradient(90deg, rgba(0,212,255,0.1), rgba(124,58,237,0.1));
        border-left: 4px solid #00d4ff;
    }
    
    /* 指标卡片数值 */
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-size: 2rem !important;
        font-weight: bold;
    }
    
    /* 指标卡片标签 */
    [data-testid="stMetricLabel"] {
        color: #a855f7 !important;
    }
    
    /* 选择框 */
    .stSelectbox > div > div {
        background: rgba(20, 30, 50, 0.8);
        border: 1px solid #00d4ff;
        border-radius: 10px;
    }
    
    /* 分割线 - 激光效果 */
    hr {
        background: linear-gradient(90deg, transparent, #00d4ff, #7c3aed, #00d4ff, transparent);
        height: 2px;
        border: none;
    }
    
    /* 数据表格文字颜色 */
    .dataframe {
        background: rgba(10, 15, 30, 0.5) !important;
        color: #e0e0e0 !important;
    }
    
    /* 表格表头 */
    .dataframe th {
        background: rgba(0, 212, 255, 0.2) !important;
        color: #00d4ff !important;
    }
    
    /* 输入框 */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background: rgba(20, 30, 50, 0.8);
        border: 1px solid #00d4ff;
        color: white;
    }
    
    /* 数字输入框 */
    .stNumberInput > div > div > input {
        background: rgba(20, 30, 50, 0.8);
        border: 1px solid #00d4ff;
        color: white;
    }
    
    /* radio按钮 */
    .stRadio > div {
        color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

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

# ---------- 顶部指标卡片 ----------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📦 耗材种类", len(st.session_state.inventory))
with col2:
    st.metric("📊 总库存量", st.session_state.inventory["当前数目"].sum())
with col3:
    low_count = len(st.session_state.inventory[st.session_state.inventory["当前数目"] < 3])
    st.metric("⚠️ 低库存预警", low_count)
with col4:
    st.metric("📝 今日操作", len(st.session_state.records[st.session_state.records["日期"] == date.today().strftime("%Y-%m-%d")]))

st.markdown("---")

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
            st.warning(f"库存不足！当前仅剩 {current_qty} 个")
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
st.title("🔬 8004 实验室耗材管理")

# 移动端引导提示
st.info("📱 **手机用户**：请点击左上角的 **☰** 菜单按钮，打开「快速记录」表单！")

# 低库存报警
low_stock = st.session_state.inventory[st.session_state.inventory["当前数目"] < 3]
if not low_stock.empty:
    for _, row in low_stock.iterrows():
        st.error(f"🚨 缺货预警：{row['产品名称']} 仅剩 {row['当前数目']} 个！")

st.subheader("📊 当前库存")
st.subheader("🛠️ 库存后台管理")
with st.expander("点击展开管理面板（仅限修正错误或更改零件名称）"):
    st.info("""
    💡 **功能说明**：
    1. **修正名称**：若发现零件型号录入有误，可直接在此修改产品名称或分类。
    2. **库存校准**：若物理库存与系统数值不符，可手动修改“当前数目”进行强制对齐。
    3. **行操作**：选中行后按 `Delete` 键可删除该产品。
    
    ⚠️ **注意**：日常的领用或采购请优先使用侧边栏的“快速记录”，以便保留操作流水。
    """)
    
    edited_df = st.data_editor(
        st.session_state.inventory,
        num_rows="dynamic",
        use_container_width=True,
        key="inventory_editor"
    )
    
    if st.button("💾 确认并覆盖原始数据", use_container_width=True):
        st.session_state.inventory = edited_df
        st.session_state.inventory.to_csv(INVENTORY_FILE, index=False)
        st.success("基础数据库已成功更新！")
        st.rerun()
        
st.dataframe(st.session_state.inventory, use_container_width=True)

st.subheader("📜 历史流水")
st.dataframe(st.session_state.records.sort_index(ascending=False), use_container_width=True)
