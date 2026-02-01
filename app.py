import streamlit as st
import pandas as pd
import os

# ---------------------- 1. 初始化会话状态 ----------------------
if "show_result" not in st.session_state:
    st.session_state.show_result = False

# ---------------------- 2. 读取Excel文件（适配Codespaces路径） ----------------------
# 优先使用绝对路径（Codespaces），兼容本地路径
excel_file_path = "终末地产品.xlsx"
# 检测Codespaces环境，自动切换路径
if os.path.exists("/workspaces/endfield-calculator/终末地产品.xlsx"):
    excel_file_path = "/workspaces/endfield-calculator/终末地产品.xlsx"

# 读取Excel数据（添加异常处理，避免文件不存在报错）
try:
    df = pd.read_excel(excel_file_path)
    # 检查必要字段是否存在（根据你的Excel表头调整）
    required_columns = ["产物名称", "机器类型", "基础产量", "电力消耗", "原料1", "原料1消耗"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"Excel文件缺少必要字段：{', '.join(missing_cols)}")
        st.stop()
except FileNotFoundError:
    st.error(f"未找到Excel文件！请确认文件路径：{excel_file_path}")
    st.info("提示：请将'终末地产品.xlsx'放在和app.py同一目录下")
    st.stop()
except Exception as e:
    st.error(f"读取Excel失败：{str(e)}")
    st.stop()

# ---------------------- 3. 页面主体逻辑 ----------------------
st.title("终末地生产计算器")

# 初始选择界面
if not st.session_state.show_result:
    # 产物选择下拉框
    product_list = df["产物名称"].dropna().tolist()
    if not product_list:
        st.warning("Excel中未找到产物数据！")
        st.stop()
    
    selected_product = st.selectbox("请选择需要计算的产物", product_list)
    
    # 目标产量输入（最小值1，默认60）
    target_output = st.number_input(
        "请输入目标产量（个/分钟）",
        min_value=1,
        value=60,
        step=1
    )
    
    # 计算按钮
    if st.button("开始计算", type="primary"):
        # 获取选中产物的详细信息
        product_info = df[df["产物名称"] == selected_product].iloc[0]
        
        # 核心计算逻辑（包含溢出产量）
        single_machine_output = product_info["基础产量"]  # 单台机器基础产量（Excel中需有此字段）
        machine_count = target_output / single_machine_output  # 理论需要机器数
        # 向上取整（处理非整数机器数）
        actual_machine = int(machine_count) if machine_count.is_integer() else int(machine_count) + 1
        actual_total_output = actual_machine * single_machine_output  # 实际总产量
        overflow_output = actual_total_output - target_output  # 溢出产量
        
        # 其他计算
        total_power = product_info["电力消耗"] * actual_machine  # 总电力消耗
        total_material = product_info["原料1消耗"] * target_output  # 总原料消耗
        
        # 存储计算结果到会话状态
        st.session_state.result = {
            "product": selected_product,
            "target_output": target_output,
            "machine_type": product_info["机器类型"],
            "single_machine_output": single_machine_output,
            "actual_machine": actual_machine,
            "actual_total_output": actual_total_output,
            "overflow_output": overflow_output,
            "total_power": total_power,
            "material_name": product_info["原料1"],
            "total_material": total_material
        }
        
        # 切换到结果界面
        st.session_state.show_result = True

# 计算结果界面
else:
    res = st.session_state.result
    st.subheader(f"「{res['product']}」生产计算结果")
    
    # 分栏显示结果（更清晰）
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"📌 目标产量：{res['target_output']} 个/分钟")
        st.write(f"🔧 机器类型：{res['machine_type']}")
        st.write(f"🖥️ 实际需要机器：{res['actual_machine']} 台")
        st.write(f"⚡ 总电力消耗：{res['total_power']} kW")
    with col2:
        st.write(f"📊 单台机器产量：{res['single_machine_output']} 个/分钟")
        st.write(f"🎯 实际总产量：{res['actual_total_output']} 个/分钟")
        st.write(f"⚠️ 溢出产量：{res['overflow_output']} 个/分钟")
        st.write(f"🧰 原料消耗：{res['material_name']} × {res['total_material']} 个/分钟")
    
    # 返回按钮（核心）
    st.divider()
    if st.button("🔙 返回重新选择", type="secondary"):
        st.session_state.show_result = False
        st.rerun()

# 底部重置按钮
st.divider()
if st.button("♻️ 重置所有选择"):
    st.session_state.clear()
    st.rerun()
