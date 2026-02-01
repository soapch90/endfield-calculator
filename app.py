import streamlit as st
import pandas as pd
import os
import ast
import math

# ---------------------- 1. 初始化会话状态 ----------------------
if "show_result" not in st.session_state:
    st.session_state.show_result = False
if "result" not in st.session_state:
    st.session_state.result = {}

# ---------------------- 2. 读取Excel文件并构建映射 ----------------------
excel_file_path = "终末地产品.xlsx"
product_info = {}  # 存储所有产物的生产信息
power_dict = {}    # 存储机器电力数据

try:
    if os.path.exists(excel_file_path):
        # 1. 读取产物表并构建映射
        df_product = pd.read_excel(excel_file_path, sheet_name="产物")
        for idx, row in df_product.iterrows():
            product_name = row["产物"]
            if pd.notna(row["机器"]) and pd.notna(row["时间"]):
                # 解析机器和材料信息
                def parse_dict(s):
                    if pd.notna(s):
                        try:
                            lst = ast.literal_eval(s)
                            return lst
                        except:
                            return {}
                    return {}
                
                machine = parse_dict(row["机器"])
                if isinstance(machine, list) and len(machine) > 0:
                    machine = machine[0]
                
                materials = parse_dict(row["材料"]) if pd.notna(row["材料"]) else []
                
                product_info[product_name] = {
                    "time_per_unit": row["时间"],
                    "machine": machine,
                    "materials": materials
                }
        
        # 2. 读取电力表
        df_power = pd.read_excel(excel_file_path, sheet_name="电力表")
        power_dict = df_power.set_index("机器")["电力"].to_dict()
    else:
        st.error(f"未找到Excel文件：{excel_file_path}")
except Exception as e:
    st.error(f"读取Excel失败：{e}")

# ---------------------- 3. 递归计算全链消耗 ----------------------
def calculate_full_chain(product_name, target_output):
    total_machines = {}
    total_materials = {}
    total_power = 0

    def recursive_calculate(current_product, required_output):
        nonlocal total_machines, total_materials, total_power
        
        # 如果是原始材料（不在product_info中）
        if current_product not in product_info:
            total_materials[current_product] = total_materials.get(current_product, 0) + required_output
            return
        
        # 获取当前产物的生产参数
        info = product_info[current_product]
        time_per_unit = info["time_per_unit"]
        machine = info["machine"]
        materials = info["materials"]

        # 计算当前产物的产能和机器需求
        single_capacity = 60 / time_per_unit
        required_machines = math.ceil(required_output / single_capacity)
        actual_capacity = required_machines * single_capacity

        # 累计机器和电力
        machine_name = machine.get("机器", "未知机器")
        machine_qty = machine.get("数量", 1) * required_machines
        total_machines[machine_name] = total_machines.get(machine_name, 0) + machine_qty
        total_power += machine_qty * power_dict.get(machine_name, 0)

        # 递归计算上游材料（确保遍历所有材料分支）
        for mat in materials:
            if isinstance(mat, dict) and "材料" in mat and "数量" in mat:
                mat_name = mat["材料"]
                mat_qty = mat["数量"]
                mat_total = actual_capacity * mat_qty
                recursive_calculate(mat_name, mat_total)
    
    # 启动递归计算
    recursive_calculate(product_name, target_output)
    
    # 计算当前产物的实际产能和溢出
    info = product_info[product_name]
    time_per_unit = info["time_per_unit"]
    single_capacity = 60 / time_per_unit
    required_machines = math.ceil(target_output / single_capacity)
    actual_capacity = required_machines * single_capacity
    overflow = actual_capacity - target_output

    return {
        "actual_capacity": actual_capacity,
        "overflow": overflow,
        "machines": total_machines,
        "materials": total_materials,
        "total_power": total_power
    }

# ---------------------- 4. 页面交互逻辑 ----------------------
st.title("终末地量化计算器")

# 产物选择（自动读取Excel中的可生产产物）
if product_info:
    product_list = list(product_info.keys())
    selected_product = st.selectbox(
        "选择要生产的产物", 
        product_list, 
        index=None,
        placeholder="请选择要生产的产物"
    )
else:
    st.warning("未读取到有效的产物信息，请检查Excel文件。")
    st.stop()

# 产量输入
target_output = st.number_input(
    "输入目标产量（个/分钟）", 
    min_value=1, 
    value=1, 
    step=1
)

# 计算按钮
if st.button("开始计算", type="primary"):
    if selected_product is None:
        st.warning("请先选择要生产的产物！")
        st.stop()
    
    if selected_product not in product_info:
        st.warning(f"「{selected_product}」的生产信息未找到，请检查Excel表。")
        st.stop()
    
    # 执行自动化递归计算
    result = calculate_full_chain(selected_product, target_output)
    
    # 存储结果
    st.session_state.result = {
        "product": selected_product,
        "target_output": target_output,
        "actual_total_capacity": result["actual_capacity"],
        "overflow_output": result["overflow"],
        "total_power": result["total_power"],
        "full_machines": result["machines"],
        "full_raw_materials": result["materials"]
    }
    st.session_state.show_result = True
    st.rerun()

# ---------------------- 5. 结果展示 ----------------------
if st.session_state.show_result and st.session_state.result:
    res = st.session_state.result
    st.subheader(f"「{res['product']}」生产量化结果")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"📌 目标产量：{res['target_output']} 个/分钟")
        st.write(f"🎯 实际总产能：{res['actual_total_capacity']:.0f} 个/分钟")
        st.write(f"⚠️ 溢出产量：{res['overflow_output']:.0f} 个/分钟")
        st.write(f"⚡ 总电力消耗：{res['total_power']:.0f}")
    with col2:
        st.write(f"🔧 所需机器：")
        for machine_name, qty in res["full_machines"].items():
            st.write(f"- {machine_name} × {qty:.0f} 台")
    
    st.write(f"🔗 所需材料：")
    for mat_name, qty in res["full_raw_materials"].items():
        st.write(f"- {mat_name} × {qty:.0f} 个/分钟")
