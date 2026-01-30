import streamlit as st
import pandas as pd
import ast
import math

# 页面配置（网页标题、图标）
st.set_page_config(
    page_title="终末地量化计算器",
    page_icon="🔧",
    layout="centered"
)

# 全局配置
DEFAULT_PRODUCTION_SECONDS = 60
formula_list = []
power_dict = {}
basic_materials = set()


# 加载Excel数据（修改为Streamlit缓存，加快加载）
@st.cache_resource
def load_data():
    try:
        # 注意：Excel文件要和app.py放在同一文件夹，这里填你的Excel文件名
        df_product = pd.read_excel("终末地产品.xlsx", sheet_name='产物')
        df_product = df_product[df_product['产物'].notna()].reset_index(drop=True)

        def parse_array_dict(cell_value):
            if pd.isna(cell_value):
                return None
            try:
                return ast.literal_eval(str(cell_value).strip())
            except:
                return None

        df_product['机器'] = df_product['机器'].apply(parse_array_dict)
        df_product['材料'] = df_product['材料'].apply(parse_array_dict)

        global basic_materials
        basic_materials = set(df_product[df_product['机器'].isna()]['产物'].tolist())

        # 读取电力表
        df_power = pd.read_excel("终末地产品.xlsx", sheet_name='电力表')
        df_power = df_power[df_power['机器'].notna()].reset_index(drop=True)
        df_power['电力'] = df_power['电力'].astype(int)
        power_dict.update(dict(zip(df_power['机器'], df_power['电力'])))

        df_product['产量'] = df_product['产量'].fillna(1).astype(int)
        df_product['时间'] = df_product['时间'].fillna(1).astype(int)

        formula_list.extend(df_product.to_dict(orient='records'))
        return True
    except Exception as e:
        st.error(f"❌ 加载Excel失败：{str(e)}")
        return False


# 获取配方
def get_formula(product_name):
    for formula in formula_list:
        if formula['产物'] == product_name:
            return formula
    return None


# 递归计算（核心逻辑不变）
def calculate_full_load(product_name, target_qty, machine_summary=None, material_summary=None):
    if machine_summary is None:
        machine_summary = {}
    if material_summary is None:
        material_summary = {}

    formula = get_formula(product_name)
    if formula is None:
        return machine_summary, material_summary, 0

    if product_name in basic_materials:
        consume_qty = int(target_qty)
        material_summary[product_name] = material_summary.get(product_name, 0) + consume_qty
        return machine_summary, material_summary, consume_qty

    machine_array = formula['机器'] or []
    material_array = formula['材料'] or []
    time_per_cycle = formula['时间']
    output_per_cycle = formula['产量']

    cycles_per_machine = DEFAULT_PRODUCTION_SECONDS / time_per_cycle
    single_machine_capacity = cycles_per_machine * output_per_cycle
    machine_count = math.ceil(target_qty / single_machine_capacity) if single_machine_capacity > 0 else 1
    actual_output = int(machine_count * single_machine_capacity)

    for machine_item in machine_array:
        m_type = machine_item['机器']
        m_per_cycle = machine_item.get('数量', 0)
        total_m = int(m_per_cycle * machine_count)
        machine_summary[m_type] = machine_summary.get(m_type, 0) + total_m

    mat_per_cycle_total = (actual_output / output_per_cycle)
    for material_item in material_array:
        mat_name = material_item['材料']
        mat_per_cycle = material_item.get('数量', 0)
        mat_total_need = mat_per_cycle_total * mat_per_cycle
        calculate_full_load(mat_name, mat_total_need, machine_summary, material_summary)

    return machine_summary, material_summary, actual_output


# 网页界面（核心）
def main():
    st.title("🔧 终末地生产计算器")
    st.divider()

    # 第一步：加载数据
    load_success = load_data()
    if not load_success:
        return

    # 第二步：获取所有产物名称（下拉选择，避免手动输入错误）
    all_products = [f['产物'] for f in formula_list]
    if not all_products:
        st.error("❌ 未找到任何产物配方")
        return

    # 第三步：用户输入（网页表单）
    col1, col2 = st.columns(2)
    with col1:
        selected_product = st.selectbox("选择要生产的产物", all_products)
    with col2:
        target_qty = st.number_input("输入目标产量", min_value=1, value=60, step=1)

    # 第四步：计算并显示结果
    if st.button("开始计算", type="primary"):
        total_machines, total_materials, actual_output = calculate_full_load(selected_product, target_qty)
        total_power = int(sum(count * power_dict.get(m, 0) for m, count in total_machines.items()))
        overflow_qty = actual_output - target_qty

        # 显示结果（美化排版）
        st.divider()
        st.subheader("📊 计算结果")
        col3, col4 = st.columns(2)
        with col3:
            st.write("**所需机器**：")
            if total_machines:
                for m, c in total_machines.items():
                    st.write(f"- {m}：{c}台")
            else:
                st.write("- 无")

            st.write(f"**总电力需求**：{total_power}")
        with col4:
            st.write("**基础原料消耗**：")
            if total_materials:
                for mat, qty in total_materials.items():
                    st.write(f"- {mat}：{qty}个")
            else:
                st.write("- 无")

            st.write(f"**溢出产量**：{overflow_qty}个")

        st.info(f"💡 说明：机器按1分钟满载运行，实际产量{actual_output}个（目标{target_qty}个）")


if __name__ == "__main__":
    main()