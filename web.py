import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from functools import reduce

st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] > .main {
        padding: 1rem !important;
    }
    .block-container {
        max-width: 90% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def home_page():
    st.title("\U0001F331 Hệ thống dự đoán khả năng ô nhiễm không khí")

    option = st.radio("Chọn cách nhập dữ liệu:", ["🔢 Nhập thủ công", "📂 Tải lên file CSV"])

    if option == "🔢 Nhập thủ công":
        col1, col2 = st.columns(2)
        with col1:
            co = st.number_input("💨 CO(GT)", value=0.0, format="%.3f")
            st.markdown("🔹 **CO (Carbon Monoxide):** Khí không màu, không mùi, gây độc khi hít phải với nồng độ cao.")

            no2 = st.number_input("🌫 NO2(GT)", value=0.0, format="%.3f")
            st.markdown("🔹 **NO2 (Nitrogen Dioxide):** Khí độc gây viêm đường hô hấp và ô nhiễm môi trường.")

        with col2:
            nox = st.number_input("🌪 NOx(GT)", value=0.0, format="%.3f")
            st.markdown(
                "🔹 **NOx (Nitrogen Oxides):** Hợp chất của Nitơ và Oxy, góp phần gây mưa axit và ô nhiễm không khí.")

            c6h6 = st.number_input("☁️ C6H6(GT)", value=0.0, format="%.3f")
            st.markdown("🔹 **C6H6 (Benzene):** Hợp chất hữu cơ dễ bay hơi, có thể gây ung thư khi tiếp xúc lâu dài.")
        if st.button("🚀 Dự đoán"):
            data = {"CO(GT)": co, "NO2(GT)": no2, "NOx(GT)": nox, "C6H6(GT)": c6h6}
            try:
                response = requests.post("http://127.0.0.1:5000/predict", json=data)
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"✅ Dự đoán mức độ ô nhiễm: {result['prediction']}")
                else:
                    st.error(f"❌ API trả về lỗi: {response.text}")
            except Exception as e:
                st.error(f"⚠️ Có lỗi xảy ra khi gọi API: {e}")

    elif option == "📂 Tải lên file CSV":
        uploaded_file = st.file_uploader("📂 Chọn file CSV", type=["csv"])

        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            required_columns = ["CO(GT)", "NO2(GT)", "NOx(GT)", "C6H6(GT)"]
            if not all(col in df.columns for col in required_columns):
                st.error("⚠️ File CSV phải chứa các cột: CO(GT), NO2(GT), NOx(GT), C6H6(GT)")
            else:
                st.write("📌 **Dữ liệu từ file CSV:**")
                st.dataframe(df)

                if st.button("🚀 Dự đoán từ CSV"):
                    predictions = []
                    for _, row in df.iterrows():
                        data = {
                            "CO(GT)": row["CO(GT)"],
                            "NO2(GT)": row["NO2(GT)"],
                            "NOx(GT)": row["NOx(GT)"],
                            "C6H6(GT)": row["C6H6(GT)"],
                        }
                        try:
                            response = requests.post("http://127.0.0.1:5000/predict", json=data)
                            if response.status_code == 200:
                                result = response.json()
                                predictions.append(result["prediction"])
                            else:
                                predictions.append("Lỗi API")
                        except:
                            predictions.append("Lỗi xử lý")

                    df["Dự đoán"] = predictions
                    st.write("✅ **Kết quả dự đoán:**")
                    st.dataframe(df)

                    csv = df.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Tải xuống kết quả (CSV)", csv, "predictions.csv", "text/csv")


def stats_page():
    st.header("🔍 Tìm kiếm dữ liệu ô nhiễm với MapReduce")

    @st.cache_data
    def load_data():
        df = pd.read_csv("timkiem.csv", sep=",")
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
        return df

    data = load_data()
    filter_option = st.sidebar.radio("Lọc theo:", ["Ngày", "Chỉ số ô nhiễm"])
    pollutant_options = ["CO(GT)", "NO2(GT)", "NOx(GT)", "C6H6(GT)"]

    def map_group(record):
        return ((record["Date"].date(), record["Time"]), record)

    mapped_pairs = list(map(map_group, data.to_dict(orient="records")))
    final_results = []

    def reduce_group(acc, pair):
        key, record = pair
        if key not in acc:
            acc[key] = []
        acc[key].append(record)
        return acc

    grouped = reduce(reduce_group, mapped_pairs, {})

    if filter_option == "Ngày":
        start_date = st.sidebar.date_input("Ngày bắt đầu", data["Date"].min())
        end_date = st.sidebar.date_input("Ngày kết thúc", data["Date"].max())

        if start_date > end_date:
            st.sidebar.error("Ngày bắt đầu không thể lớn hơn ngày kết thúc!")
        else:
            filtered_groups = {k: v for k, v in grouped.items() if start_date <= k[0] <= end_date}
            for recs in filtered_groups.values():
                final_results.extend(recs)

    elif filter_option == "Chỉ số ô nhiễm":
        selected_pollutant = st.sidebar.selectbox("Chọn chất ô nhiễm", pollutant_options)
        min_value = float(data[selected_pollutant].min())
        max_value = float(data[selected_pollutant].max())
        min_pollution = st.sidebar.number_input(f"Giá trị tối thiểu của {selected_pollutant}", value=min_value)
        max_pollution = st.sidebar.number_input(f"Giá trị tối đa của {selected_pollutant}", value=max_value)

        if min_pollution > max_pollution:
            st.sidebar.error("Giá trị tối thiểu không thể lớn hơn giá trị tối đa!")
        else:
            for k, recs in grouped.items():
                valid_records = [r for r in recs if min_pollution <= r[selected_pollutant] <= max_pollution]
                if valid_records:
                    final_results.extend(valid_records)

    if final_results:
        df_filtered = pd.DataFrame(final_results)
        st.write(f"📌 Tổng số bản ghi tìm thấy: {df_filtered.shape[0]}")
        st.dataframe(df_filtered)
        csv = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Tải xuống kết quả (CSV)", csv, "filtered_data.csv", "text/csv")
    else:
        st.warning("❌ Không tìm thấy dữ liệu phù hợp.")


def statistic_page():
    st.header("📊 Trang Thống Kê")

    @st.cache_data
    def load_data():
        df = pd.read_csv("thongke.csv")
        df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")

        # Kiểm tra nếu "PollutionIndex" chưa tồn tại, thì tính toán
        if "PollutionIndex" not in df.columns:
            df["PollutionIndex"] = df[["CO(GT)", "NO2(GT)", "NOx(GT)", "C6H6(GT)"]].mean(axis=1)

        return df

    data = load_data()

    # Nếu cột PollutionLevel có các giá trị 0,1,2, chuyển thành nhãn
    data["PollutionLevel"] = data["PollutionLevel"].replace({
        0: "Tốt",
        1: "Trung bình",
        2: "Xấu"
    })

    # 📌 Thống kê tổng quan
    st.subheader("📈 Thống kê tổng quan")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📅 Số ngày có dữ liệu", data.shape[0])

    with col2:
        max_pollution_date = data.loc[data["PollutionIndex"].idxmax(), "Date"]
        st.metric("🔥 Ngày ô nhiễm cao nhất", max_pollution_date.strftime("%Y-%m-%d"))

    with col3:
        min_pollution_date = data.loc[data["PollutionIndex"].idxmin(), "Date"]
        st.metric("🌱 Ngày ô nhiễm thấp nhất", min_pollution_date.strftime("%Y-%m-%d"))

    # 📌 Trung bình các chất ô nhiễm
    st.write("### 📊 Trung bình các chất ô nhiễm:")
    st.write(data[["CO(GT)", "NO2(GT)", "NOx(GT)", "C6H6(GT)"]].mean().to_frame().T)

    # 📉 Biểu đồ xu hướng ô nhiễm theo ngày
    st.subheader("📉 Xu hướng ô nhiễm theo thời gian")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(x="Date", y="PollutionIndex", data=data, ax=ax, marker="o")
    ax.set_title("📉 Xu hướng ô nhiễm theo thời gian")
    ax.set_xlabel("Ngày")
    ax.set_ylabel("Chỉ số ô nhiễm")
    st.pyplot(fig)


    # 📊 Biểu đồ số lượng ngày theo mức độ ô nhiễm
    st.subheader("📊 Số ngày theo mức độ ô nhiễm")
    fig, ax = plt.subplots(figsize=(8, 4))
    sns.countplot(x="PollutionLevel", data=data, palette="coolwarm", ax=ax)
    ax.set_title("📊 Số lượng ngày theo mức độ ô nhiễm")
    st.pyplot(fig)


# --- Quản lý điều hướng trang với sidebar đẹp hơn ---
st.sidebar.markdown(
    """
    <h1 style='text-align: center; color: #2E86C1; font-size: 24px;'>
        🌍 Menu Chính
    </h1>
    <hr style='border: 1px solid #2E86C1; margin-bottom: 20px;'>  <!-- Đường phân cách -->
    <p style='text-align: center; font-size: 14px; margin-bottom: 20px;'>Chọn trang để khám phá:</p>
    <style>
    /* Nhắm vào các nút trong sidebar */
    [data-testid="stSidebar"] div.stButton > button {
        width: 200px !important;  /* Chiều rộng cố định */
        border: 2px solid #2E86C1 !important;  /* Khung màu xanh */
        border-radius: 8px !important;  /* Bo góc */
        padding: 5px !important;  /* Khoảng cách bên trong */
        background-color: #F5F6F5 !important;  /* Màu nền nhạt */
        color: #2E86C1 !important;  /* Màu chữ xanh đậm */
        margin-bottom: 10px !important;  /* Khoảng cách giữa các nút */
        display: block !important;  /* Đảm bảo nút chiếm toàn bộ chiều rộng */
        margin-left: auto !important;  /* Căn giữa */
        margin-right: auto !important;  /* Căn giữa */
        text-align: center !important;  /* Căn giữa nội dung */
        font-size: 16px !important;  /* Kích thước chữ */
        font-weight: bold !important;  /* Chữ đậm */
    }
    /* Đảm bảo nút không bị ẩn */
    [data-testid="stSidebar"] div.stButton > button:hover {
        background-color: #E0E7FF !important;  /* Màu nền khi hover */
        color: #1E3A8A !important;  /* Màu chữ khi hover */
    }
    </style>
    """,
    unsafe_allow_html=True
)

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Trang chủ"

if st.sidebar.button("🏠 Trang chủ"):
    st.session_state.current_page = "Trang chủ"
if st.sidebar.button("🔍 Tìm kiếm"):
    st.session_state.current_page = "Tìm kiếm"
if st.sidebar.button("📊 Thống kê"):
    st.session_state.current_page = "Thống kê"

if st.session_state.current_page == "Trang chủ":
    home_page()
elif st.session_state.current_page == "Tìm kiếm":
    stats_page()
elif st.session_state.current_page == "Thống kê":
    statistic_page()
