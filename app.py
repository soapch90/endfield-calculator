import streamlit as st
import pandas as pd
import os
import ast

# ---------------------- 1. 初始化会话状态 ----------------------
if "show_result" not in st.session_state:
    st.session_state.show_result = False

# ---------------------- 2. 读取Excel文件（适配Codespaces路径） ----------------------
excel_file_path = "终末地产品.xlsx"
if os.path.exists("/workspaces/endfield-calculator/终末地产品.xlsx"):
    excel_file_path = "/workspaces/endfield-calculator/终末地产品.xlsx"

try:
    df = pd.read_excel(excel_file_path, sheet_name="产物")
    required_columns = ["产物", "机器", "材料", "时间", "产量"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"Excel文件缺少必要字段：{', '.join(missing_cols)}")
        st.stop()
except FileNotFoundError:
    st.error(f"未找到Excel文件！请确认文件路径：{excel_file_path}")
    st.stop()
except Exception as e:
    st.error(f"读取Excel失败：{str(e)}")
    st.stop()

# ---------------------- 3. 页面主体逻辑 ----------------------
st.title("终末地生产计算器")

# 初始选择界面
if not st.session_state.show_result:
    product_list = df["产物"].dropna().tolist()
    if not product_list:
        st.warning("Excel中未找到产物数据！")
        st.stop()
    
    selected_product = st.selectbox("选择要生产的产物", product_list)
    target_output = st.number_input("输入目标产量", min_value=1, value=60, step=1)
    
    if st.button("开始计算", type="primary"):
        product_info = df[df["产物"] == selected_product].iloc[0]
        
        # 处理时间为空的情况
        if pd.isna(product_info["时间"]):
            st.error(f"产物「{selected_product}」的生产时间为空，无法计算！请检查Excel数据")
            st.stop()
        
        # 解析机器和材料的字典格式
        machine_dict = ast.literal_eval(product_info["机器"]) if pd.notna(product_info["机器"]) else {}
        material_dict = ast.literal_eval(product_info["材料"]) if pd.notna(product_info["材料"]) else {}
        
        # 计算逻辑
        production_time = product_info["时间"]
        single_machine_output = 1 / production_time
        machine_count = target_output / single_machine_output
        # 用 math.ceil 安全向上取整，避免 NaN 问题
        import math
        actual_machine = math.ceil(machine_count)
        actual_total_output = actual_machine * single_machine_output
        overflow_output = actual_total_output - target_output
        
        # 存储结果
        st.session_state.result = {
            "product": selected_product,
            "target_output": target_output,
            "machine_dict": machine_dict,
            "material_dict": material_dict,
            "production_time": production_time,
            "single_machine_output": single_machine_output,
            "actual_machine": actual_machine,
            "overflow_output": overflow_output
        }
        st.session_state.show_result = True

# 计算结果界面
else:
    res = st.session_state.result
    st.subheader(f"「{res['product']}」生产计算结果")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"📌 目标产量：{res['target_output']} 个/分钟")
        st.write(f"⏱️ 单产物生产时间：{res['production_time']} 分钟/个")
        st.write(f"🖥️ 实际需要机器：{res['actual_machine']} 台")
        st.write(f"⚠️ 溢出产量：{res['overflow_output']:.1f} 个/分钟")
    with col2:
        st.write("🔧 所需机器：")
        for k, v in res["machine_dict"].items():
            st.write(f"- {k} × {v}")
        st.write("🧰 所需材料：")
        for k, v in res["material_dict"].items():
            st.write(f"- {k} × {v} × {res['target_output']} 个")
    
    # 返回按钮
    st.divider()
    if st.button("🔙 返回重新选择", type="secondary"):
        st.session_state.show_result = False
        st.rerun()

# 重置按钮
st.divider()
if st.button("♻️ 重置所有选择"):
    st.session_state.clear()
    st.rerun()
