import streamlit as st
import pandas as pd
import os
import math

# ---------------------- 1. 初始化会话状态 ----------------------
if "show_result" not in st.session_state:
    st.session_state.show_result = False
if "result" not in st.session_state:
    st.session_state.result = {}

# ---------------------- 2. 读取电力表 ----------------------
excel_file_path = "终末地产品.xlsx"
power_dict = {}
try:
    if os.path.exists(excel_file_path):
        df_power = pd.read_excel(excel_file_path, sheet_name="电力表")
        power_dict = df_power.set_index("机器")["电力"].to_dict()
    else:
        power_dict = {
            "封装机": 50,
            "配件机": 40,
            "精炼炉": 60,
            "粉碎机": 30
        }
except Exception as e:
    st.warning(f"读取电力表失败，使用默认电力数据：{e}")
    power_dict = {
        "封装机": 50,
        "配件机": 40,
        "精炼炉": 60,
        "粉碎机": 30
    }

# ---------------------- 3. 计算函数 ----------------------
# 中容谷地电池
def calculate_battery_chain(target_output):
    time_per_battery = 10
    single_battery_cap = 60 / time_per_battery
    required_packager = math.ceil(target_output / single_battery_cap)
    actual_battery = required_packager * single_battery_cap

    iron_part_need = actual_battery * 10
    dust_need = actual_battery * 15

    time_per_iron = 2
    single_iron_cap = 60 / time_per_iron
    required_fitter = math.ceil(iron_part_need / single_iron_cap)
    iron_ingot_need = actual_battery * 10

    time_per_ingot = 2
    single_ingot_cap = 60 / time_per_ingot
    required_refiner = math.ceil(iron_ingot_need / single_ingot_cap)
    iron_ore_need = actual_battery * 10

    time_per_dust = 2
    single_dust_cap = 60 / time_per_dust
    required_crusher = math.ceil(dust_need / single_dust_cap)
    ore_need = actual_battery * 15

    machines = {
        "封装机": required_packager,
        "配件机": required_fitter,
        "精炼炉": required_refiner,
        "粉碎机": required_crusher
    }

    total_power = 0
    for machine, qty in machines.items():
        total_power += qty * power_dict.get(machine, 0)

    materials = {
        "蓝铁矿": iron_ore_need,
        "源矿": ore_need
    }

    overflow = actual_battery - target_output

    return {
        "actual": actual_battery,
        "overflow": overflow,
        "machines": machines,
        "materials": materials,
        "total_power": total_power
    }

# 铁制零件
def calculate_iron_part_chain(target_output):
    time_per_part = 2
    single_part_cap = 60 / time_per_part
    required_fitter = math.ceil(target_output / single_part_cap)
    actual_part = required_fitter * single_part_cap

    iron_ingot_need = actual_part * 1
    time_per_ingot = 2
    single_ingot_cap = 60 / time_per_ingot
    required_refiner = math.ceil(iron_ingot_need / single_ingot_cap)
    iron_ore_need = actual_part * 1

    machines = {
        "配件机": required_fitter,
        "精炼炉": required_refiner
    }

    total_power = 0
    for machine, qty in machines.items():
        total_power += qty * power_dict.get(machine, 0)

    materials = {
        "蓝铁矿": iron_ore_need
    }

    overflow = actual_part - target_output

    return {
        "actual": actual_part,
        "overflow": overflow,
        "machines": machines,
        "materials": materials,
        "total_power": total_power
    }

# ---------------------- 4. 页面交互逻辑 ----------------------
st.title("终末地量化计算器")

# 产物选择（恢复空初始化 + placeholder提示）
product_list = ["中容谷地电池", "铁制零件", "源石粉末", "蓝铁块"]
selected_product = st.selectbox(
    "选择要生产的产物", 
    product_list, 
    index=None,  # 关键：初始化为空
    placeholder="请选择要生产的产物"  # 提示文案
)

# 产量输入
target_output = st.number_input(
    "输入目标产量（个/分钟）", 
    min_value=1, 
    value=1, 
    step=1
)

# 计算按钮逻辑
if st.button("开始计算", type="primary"):
    # 先判断是否选择了产物
    if selected_product is None:
        st.warning("请先从下拉框选择要生产的产物！")
        st.stop()
    
    # 根据选择的产物计算
    if selected_product == "中容谷地电池":
        result = calculate_battery_chain(target_output)
    elif selected_product == "铁制零件":
        result = calculate_iron_part_chain(target_output)
    else:
        st.warning(f"「{selected_product}」的计算逻辑尚未添加，目前仅支持中容谷地电池和铁制零件。")
        st.stop()

    # 存储结果
    st.session_state.result = {
        "product": selected_product,
        "target_output": target_output,
        "actual_total_capacity": result["actual"],
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
