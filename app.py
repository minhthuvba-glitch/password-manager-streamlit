import streamlit as st
import json
import os

DATA_FILE = "data.json"

# 📂 Hàm đọc dữ liệu từ file JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"accounts": []}

# 💾 Hàm ghi dữ liệu vào file JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

st.set_page_config(page_title="Password Manager", page_icon="🔑")
st.title("🔑 Password Manager (Demo)")

# Load dữ liệu
data = load_data()

# 📝 Form thêm tài khoản
with st.form("add_account"):
    site = st.text_input("🌐 Website / Ứng dụng")
    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")
    note = st.text_area("📝 Ghi chú")
    submitted = st.form_submit_button("Lưu")

    if submitted:
        if site and username and password:
            data["accounts"].append({
                "site": site,
                "username": username,
                "password": password,
                "note": note
            })
            save_data(data)
            st.success(f"✅ Đã lưu mật khẩu cho {site}")
        else:
            st.error("❌ Vui lòng nhập đầy đủ Website, Username và Password!")

# 📋 Hiển thị danh sách tài khoản
st.subheader("Danh sách tài khoản đã lưu")

if len(data["accounts"]) == 0:
    st.info("Chưa có tài khoản nào được lưu.")
else:
    for i, acc in enumerate(data["accounts"], start=1):
        with st.expander(f"{i}. {acc['site']}"):
            st.write(f"👤 **Username:** {acc['username']}")
            st.write(f"🔑 **Password:** {acc['password']}")
            st.write(f"📝 **Ghi chú:** {acc['note']}")
