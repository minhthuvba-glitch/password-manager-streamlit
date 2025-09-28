import streamlit as st
import json
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from cryptography.fernet import Fernet
import base64  # ✅ cần cho mã hóa/giải mã

DATA_FILE = "data.json"

# ====== Helper functions ======
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"master": {}, "accounts": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_key(master_password: str):
    return hashlib.sha256(master_password.encode()).digest()[:32]

def encrypt_password(password: str, key: bytes) -> str:
    return Fernet(base64.urlsafe_b64encode(key)).encrypt(password.encode()).decode()

def decrypt_password(encrypted: str, key: bytes) -> str:
    return Fernet(base64.urlsafe_b64encode(key)).decrypt(encrypted.encode()).decode()

# ====== Email gửi mật khẩu quên ======
def send_recovery_email(to_email, master_username, master_password):
    try:
        # Chỉ demo gửi mail qua SMTP Gmail
        sender = "your_email@gmail.com"
        sender_pass = "your_app_password"  # app password (2FA)
        msg = MIMEText(f"Tài khoản master: {master_username}\nMật khẩu: {master_password}")
        msg["Subject"] = "Khôi phục mật khẩu Master"
        msg["From"] = sender
        msg["To"] = to_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, sender_pass)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error(f"Lỗi gửi email: {e}")

# ====== UI ======
st.set_page_config(page_title="Password Manager", layout="centered")
st.title("🔐 Password Manager")

data = load_data()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "master_username" not in st.session_state:
    st.session_state.master_username = ""
if "master_password" not in st.session_state:
    st.session_state.master_password = ""

# TAB ĐĂNG NHẬP / ĐĂNG KÝ
if not st.session_state.authenticated:
    tab1, tab2, tab3 = st.tabs(["🔑 Đăng nhập", "🆕 Đăng ký", "❓ Quên mật khẩu"])

    # ---- Đăng nhập ----
    with tab1:
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")

        if st.button("Đăng nhập"):
            if data["master"]:
                if username == data["master"]["username"] and hash_password(password) == data["master"]["password"]:
                    st.session_state.authenticated = True
                    st.session_state.master_username = username
                    st.session_state.master_password = password
                    st.success("Đăng nhập thành công!")
                    st.rerun()
                else:
                    st.error("Sai tên đăng nhập hoặc mật khẩu")
            else:
                st.warning("Chưa có tài khoản master. Hãy đăng ký trước.")

    # ---- Đăng ký ----
    with tab2:
        if data["master"]:
            st.info("Tài khoản master đã tồn tại. Không thể tạo thêm.")
        else:
            new_username = st.text_input("Tên đăng nhập master")
            new_password = st.text_input("Mật khẩu master", type="password")
            email = st.text_input("Email khôi phục")
            if st.button("Đăng ký"):
                if new_username and new_password and email:
                    data["master"] = {
                        "username": new_username,
                        "password": hash_password(new_password),
                        "email": email
                    }
                    save_data(data)
                    st.success("Tạo tài khoản master thành công! Hãy đăng nhập.")
                else:
                    st.error("Vui lòng nhập đủ thông tin")

    # ---- Quên mật khẩu ----
    with tab3:
        if data["master"]:
            recovery_email = data["master"]["email"]
            st.write(f"Nếu quên mật khẩu, mật khẩu sẽ gửi về email: {recovery_email}")
            if st.button("Gửi email khôi phục"):
                # ⚠️ Demo: bạn cần thay bằng mật khẩu thật chưa mã hóa
                send_recovery_email(recovery_email, data["master"]["username"], "[mật khẩu thật]")
                st.success("Đã gửi email khôi phục!")
        else:
            st.info("Chưa có tài khoản master.")
else:
    # TAB CHỨC NĂNG (sau khi đăng nhập)
    tab_func = st.tabs(["📂 Quản lý mật khẩu"])[0]

    with tab_func:
        st.subheader(f"Xin chào, {st.session_state.master_username} 👋")

        # ✅ Nút đăng xuất
        if st.button("🚪 Đăng xuất"):
            st.session_state.authenticated = False
            st.session_state.master_username = ""
            st.session_state.master_password = ""
            st.success("Bạn đã đăng xuất.")
            st.rerun()

        app_name = st.text_input("Tên App/Web")
        acc_username = st.text_input("Tên đăng nhập")
        acc_password = st.text_input("Mật khẩu")

        if st.button("Lưu mật khẩu"):
            if app_name and acc_username and acc_password:
                key = generate_key(st.session_state.master_password)
                encrypted_pw = encrypt_password(acc_password, key)
                data["accounts"].append({
                    "app": app_name,
                    "username": acc_username,
                    "password": encrypted_pw
                })
                save_data(data)
                st.success("Đã lưu mật khẩu!")
            else:
                st.error("Nhập đầy đủ thông tin")

        st.subheader("📋 Danh sách đã lưu")
        if data["accounts"]:
            key = generate_key(st.session_state.master_password)
            for acc in data["accounts"]:
                try:
                    pw = decrypt_password(acc["password"], key)
                except:
                    pw = "⚠️ Không giải mã được"
                st.write(f"**{acc['app']}** - {acc['username']} - {pw}")
        else:
            st.info("Chưa có tài khoản nào.")
