import streamlit as st
import json
import os
import hashlib
import random
import smtplib
from email.mime.text import MIMEText
from cryptography.fernet import Fernet

# ---------------------------
# Hàm tiện ích
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
# Giao diện
# ---------------------------
st.title("🔐 Password Manager với Master Login")

data = load_data()

# Nếu chưa có master thì tạo mới
if "master" not in data or not data["master"]:
    st.subheader("Thiết lập tài khoản Master")
    new_user = st.text_input("Tên đăng nhập")
    new_pass = st.text_input("Mật khẩu", type="password")
    new_email = st.text_input("Email khôi phục")
    if st.button("Tạo Master"):
        if new_user and new_pass and new_email:
            data["master"] = {
                "username": new_user,
                "password": hash_password(new_pass),
                "email": new_email
            }
            save_data(data)
            st.success("Tạo Master thành công! Vui lòng đăng nhập.")
        else:
            st.error("Vui lòng nhập đủ thông tin.")
else:
    # ---------------------------
    # Xử lý đăng nhập
    # ---------------------------
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "reset_code" not in st.session_state:
        st.session_state.reset_code = None

    if not st.session_state.logged_in:
        st.subheader("Đăng nhập Master")
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Đăng nhập"):
                if (
                    username == data["master"]["username"]
                    and hash_password(password) == data["master"]["password"]
                ):
                    st.session_state.logged_in = True
                    st.success("Đăng nhập thành công!")
                else:
                    st.error("Sai tên đăng nhập hoặc mật khẩu.")

        with col2:
            if st.button("Quên mật khẩu"):
                reset_code = str(random.randint(100000, 999999))
                st.session_state.reset_code = reset_code
                try:
                    send_reset_email(data["master"]["email"], reset_code)
                    st.info("Mã khôi phục đã gửi về email!")
                except Exception as e:
                    st.error(f"Lỗi gửi email: {e}")

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
    else:
        # ---------------------------
        # Chức năng quản lý mật khẩu
        # ---------------------------
        st.subheader("Quản lý tài khoản")

        # Thêm tài khoản
        with st.form("add_account"):
            service = st.text_input("Dịch vụ / Trang web")
            acc_user = st.text_input("Tên đăng nhập")
            acc_pass = st.text_input("Mật khẩu")
            submitted = st.form_submit_button("Lưu")
            if submitted:
                enc_pass = encrypt(acc_pass)
                data["accounts"].append(
                    {"service": service, "username": acc_user, "password": enc_pass}
                )
                save_data(data)
                st.success("Đã lưu tài khoản.")

        # Hiển thị danh sách
        st.write("### Danh sách tài khoản")
        for idx, acc in enumerate(data["accounts"]):
            with st.expander(f"{acc['service']} - {acc['username']}"):
                st.write("Tên đăng nhập:", acc["username"])
                st.write("Mật khẩu:", decrypt(acc["password"]))
