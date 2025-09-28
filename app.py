import streamlit as st
import json
import os
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from cryptography.fernet import Fernet

# ---------------------------
# Tiện ích xử lý dữ liệu
# ---------------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_data():
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"master": {}, "accounts": []}, f)
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)

# ---------------------------
# Gửi email reset
# ---------------------------
def send_reset_email(to_email, reset_code):
    msg = MIMEText(f"Mã khôi phục mật khẩu của bạn là: {reset_code}")
    msg['Subject'] = "Khôi phục mật khẩu - Password Manager"
    msg['From'] = st.secrets["EMAIL_USER"]
    msg['To'] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(st.secrets["EMAIL_USER"], st.secrets["EMAIL_PASS"])
        server.sendmail(msg['From'], [to_email], msg.as_string())

# ---------------------------
# Khởi tạo key cho Fernet
# ---------------------------
def load_key():
    if not os.path.exists("secret.key"):
        key = Fernet.generate_key()
        with open("secret.key", "wb") as key_file:
            key_file.write(key)
    else:
        with open("secret.key", "rb") as key_file:
            key = key_file.read()
    return key

fernet = Fernet(load_key())

def encrypt(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

# ---------------------------
# Giao diện chính
# ---------------------------
st.title("🔐 Password Manager")

data = load_data()

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "reset_code" not in st.session_state:
    st.session_state.reset_code = None

# ---------------------------
# Tabs
# ---------------------------
tab_login, tab_app = st.tabs(["🔑 Đăng nhập", "📒 Chức năng"])

# ---------------------------
# Tab 1: Đăng nhập / Đăng ký / Quên mật khẩu
# ---------------------------
with tab_login:
    st.subheader("Đăng nhập / Đăng ký")

    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")
    email = st.text_input("Email (chỉ khi Đăng ký hoặc Quên mật khẩu)")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Đăng nhập"):
            if "master" in data and data["master"]:
                if (
                    username == data["master"]["username"]
                    and hash_password(password) == data["master"]["password"]
                ):
                    st.session_state.logged_in = True
                    st.success("Đăng nhập thành công!")
                else:
                    st.error("Sai tên đăng nhập hoặc mật khẩu.")
            else:
                st.warning("Chưa có tài khoản Master. Hãy Đăng ký.")

    with col2:
        if st.button("Đăng ký"):
            if not data["master"]:
                if username and password and email:
                    data["master"] = {
                        "username": username,
                        "password": hash_password(password),
                        "email": email,
                    }
                    save_data(data)
                    st.success("Đăng ký Master thành công! Vui lòng đăng nhập.")
                else:
                    st.error("Vui lòng nhập đủ thông tin.")
            else:
                st.warning("Tài khoản Master đã tồn tại. Không thể đăng ký mới.")

    with col3:
        if st.button("Quên mật khẩu"):
            if "master" in data and data["master"]:
                reset_code = str(random.randint(100000, 999999))
                st.session_state.reset_code = reset_code
                try:
                    send_reset_email(data["master"]["email"], reset_code)
                    st.info("Mã khôi phục đã gửi về email!")
                except Exception as e:
                    st.error(f"Lỗi gửi email: {e}")
            else:
                st.error("Chưa có tài khoản Master để khôi phục.")

    if st.session_state.reset_code:
        st.subheader("Khôi phục mật khẩu")
        code = st.text_input("Nhập mã khôi phục")
        new_pass = st.text_input("Mật khẩu mới", type="password")
        if st.button("Đặt lại mật khẩu"):
            if code == st.session_state.reset_code:
                data["master"]["password"] = hash_password(new_pass)
                save_data(data)
                st.success("Đặt lại mật khẩu thành công! Vui lòng đăng nhập lại.")
                st.session_state.reset_code = None
            else:
                st.error("Sai mã khôi phục.")

# ---------------------------
# Tab 2: Chức năng
# ---------------------------
with tab_app:
    if not st.session_state.logged_in:
        st.warning("⚠️ Vui lòng đăng nhập trước khi sử dụng chức năng.")
    else:
        st.subheader("Thêm tài khoản")
        with st.form("add_account"):
            service = st.text_input("App / Web")
            acc_user = st.text_input("Tên đăng nhập")
            acc_pass = st.text_input("Mật khẩu")
            submitted = st.form_submit_button("Lưu")
            if submitted:
                if service and acc_user and acc_pass:
                    enc_pass = encrypt(acc_pass)
                    data["accounts"].append(
                        {"service": service, "username": acc_user, "password": enc_pass}
                    )
                    save_data(data)
                    st.success("Đã lưu tài khoản.")
                else:
                    st.error("Vui lòng nhập đầy đủ thông tin.")

        st.subheader("Danh sách tài khoản đã lưu")
        for idx, acc in enumerate(data["accounts"]):
            with st.expander(f"{acc['service']} - {acc['username']}"):
                st.write("Tên đăng nhập:", acc["username"])
                st.write("Mật khẩu:", decrypt(acc["password"]))
