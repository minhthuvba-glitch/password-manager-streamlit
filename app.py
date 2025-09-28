import streamlit as st
import json
import os
import base64
import hashlib
from cryptography.fernet import Fernet

DATA_FILE = "data.json"

# ✅ Khóa master cố định (bạn có thể đổi tùy ý)
MASTER_KEY = "123456"

# 🔑 Tạo key từ master password
def generate_key(master_password: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(master_password.encode()).digest())

# 📂 Load dữ liệu JSON
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    else:
        return {"accounts": []}

# 💾 Lưu dữ liệu JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# -------------------------
st.set_page_config(page_title="Password Manager", page_icon="🔑")
st.title("🔑 Password Manager (Secure with Master Key)")

# 🛡️ Đăng nhập bằng Master Key
master_key_input = st.text_input("Nhập Master Key để đăng nhập", type="password")

if master_key_input != MASTER_KEY:
    st.warning("Bạn cần nhập đúng Master Key để sử dụng ứng dụng.")
    st.stop()

st.success("✅ Đăng nhập thành công!")

# 🔑 Nhập master password để mã hóa/giải mã
master_password = st.text_input("Nhập Master Password để mã hóa dữ liệu", type="password")

if not master_password:
    st.info("Vui lòng nhập Master Password để tiếp tục.")
    st.stop()

# Sinh key từ master password
key = generate_key(master_password)
cipher = Fernet(key)

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
            encrypted_password = cipher.encrypt(password.encode()).decode()
            data["accounts"].append({
                "site": site,
                "username": username,
                "password": encrypted_password,
                "note": note
            })
            save_data(data)
            st.success(f"✅ Đã lưu mật khẩu cho {site}")
        else:
            st.error("❌ Vui lòng nhập đầy đủ Website, Username và Password!")

# 📋 Hiển thị danh sách
st.subheader("Danh sách tài khoản đã lưu")

if len(data["accounts"]) == 0:
    st.info("Chưa có tài khoản nào được lưu.")
else:
    for i, acc in enumerate(data["accounts"], start=1):
        with st.expander(f"{i}. {acc['site']}"):
            st.write(f"👤 **Username:** {acc['username']}")
            st.write(f"📝 **Ghi chú:** {acc['note']}")

            # Hiển mật khẩu khi nhấn nút
            if st.button(f"Hiện mật khẩu #{i}"):
                try:
                    decrypted_password = cipher.decrypt(acc["password"].encode()).decode()
                    st.code(decrypted_password)
                except Exception:
                    st.error("❌ Master Password không đúng hoặc dữ liệu bị lỗi!")
