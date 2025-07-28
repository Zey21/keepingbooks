import streamlit as st
import sqlite3
from sqlite3 import Error
import hashlib
import pandas as pd  # Import pandas
from datetime import datetime

# Database setup
def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('database.db', check_same_thread=False)
    except Error as e:
        st.error(f"Error connecting to database: {e}")
    return conn

conn = create_connection()
c = conn.cursor()

# Password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication
def register(username, name, password):
    try:
        c.execute("INSERT INTO users (username, name, password) VALUES (?, ?, ?)", (username, name, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def login(username, password):
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    return c.fetchone()

# CRUD operations
def add_record(user_id, date, name, description, amount, type_):
    c.execute("INSERT INTO records (user_id, date, name, description, amount, type) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, date, name, description, amount, type_))
    conn.commit()

def get_records(user_id):
    c.execute("SELECT id, date, name, description, amount, type FROM records WHERE user_id = ? ORDER BY date DESC", (user_id,))
    return c.fetchall()

def get_records_all():
    c.execute("SELECT id, date, name, description, amount, type FROM records ORDER BY date DESC")
    return c.fetchall()

def get_name(user_id):
    c.execute("SELECT name FROM users WHERE id = ?", (user_id,))
    return c.fetchall()

def update_record(record_id, date, description, amount, type_):
    c.execute("UPDATE records SET date = ?, description = ?, amount = ?, type = ? WHERE id = ?",
              (date, description, amount, type_, record_id))
    conn.commit()

def delete_record(record_id):
    c.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    
def get_time():
    # Tanggal yang ditentukan (format: YYYY-MM-DD)
    tanggal_ditetapkan = '2025-06-21'

    # Konversi string ke objek tanggal
    tanggal_ditetapkan = datetime.strptime(tanggal_ditetapkan, '%Y-%m-%d').date()

    # Ambil tanggal hari ini
    tanggal_hari_ini = datetime.today().date()

    # Hitung selisih hari
    jumlah_hari_terlewat = (tanggal_hari_ini - tanggal_ditetapkan).days

    # # Tampilkan hasil
    # if jumlah_hari_terlewat >= 0:
    #     st.write(f"Jumlah hari yang telah berlalu sejak {tanggal_ditetapkan}: {jumlah_hari_terlewat} hari")
    # else:
    #     st.write(f"Tanggal {tanggal_ditetapkan} belum terjadi. Masih {abs(jumlah_hari_terlewat)} hari lagi.")

    return jumlah_hari_terlewat

# Streamlit UI
st.title("Aplikasi Pembukuan Tabungan Harian")

menu = ["Login", "Register"]
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.logged_in:
    choice = st.sidebar.selectbox("Menu", menu)
    if choice == "Login":
        st.subheader("Login to your account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login(username, password)
            if user:
                st.success(f"Welcome back, {username}!")
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid username or password")
    elif choice == "Register":
        st.subheader("Create a new account")
        new_username = st.text_input("Username", key="reg_username")
        new_name = st.text_input("Name", key="reg_name")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
        # if st.button("Register"):
        #     if new_password != confirm_password:
        #         st.error("Passwords do not match")
        #     elif len(new_password) < 6:
        #         st.error("Password must be at least 6 characters")
        #     elif register(new_username, new_name, new_password):
        #         st.success("Account created successfully! Please login.")
        #     else:
        #         st.error("Username already exists")
else:
    st.sidebar.write(f"Logged in as: {st.session_state.user[1]}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        c.close()
        st.rerun()

    user_id = st.session_state.user[0]
    name_user = get_name(user_id)
    name_user = name_user[0][0]

    st.subheader("Selamat Datang {}".format(name_user))
    
    st.subheader("Create")
    # Add new record
    with st.expander("Add New Record"):
        with st.form("add_record_form", clear_on_submit=True):
            date = st.date_input("Date")
            description = st.text_input("Description")
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            type_ = st.selectbox("Type", ["income", "expense"])
            submitted = st.form_submit_button("Add Record")
            if submitted:
                if description.strip() == "":
                    st.error("Description cannot be empty")
                else:
                    add_record(user_id, date.isoformat(), name_user, description, amount, type_)
                    st.success("Record added successfully")
                    st.rerun()

    
    
    # Display records    
    records = get_records(user_id)
    records_all = get_records_all()
    if records:
        # Create a DataFrame from the records
        records_df = pd.DataFrame(records, columns=["ID", "Date", "Name", "Description", "Amount", "Type"])
        records_df_all = pd.DataFrame(records_all, columns=["ID", "Date", "Name", "Description", "Amount", "Type"])
        
        # Display the DataFrame
        st.subheader("Tabel Data :")
        st.write("Semua Pembukuan :")
        st.dataframe(records_df_all)
        st.write("{}".format(name_user))
        st.dataframe(records_df)
        
        st.subheader("Details")
        if records:
            income_amount_id = []
            expense_amount_id = []
            total_income = 0
            total_expense = 0
            total_amount = 0
            
            for data in records:
                if data[5] == "income":
                    income_amount_id.append(data[4])
                elif data[5] == "expense":
                    expense_amount_id.append(data[4])
            
            if income_amount_id != []:
                total_income = sum(income_amount_id)
            
            if expense_amount_id != []:
                total_expense = sum(expense_amount_id)
            
            st.write("Info {}:".format(name_user))    
            st.write("Total Income: Rp. {},-".format(total_income))
            st.write("Total Expense: Rp. {},-".format(total_expense))
            days_count = get_time()
            money_count_by_days = 10000 * days_count
            if total_income > money_count_by_days :
                st.write(f"Total uang yang ditabung oleh {name_user} sudah cukup untuk hari ini")
            else:
                money_saving = money_count_by_days - total_income
                st.write(f"Total uang yang harus ditabung oleh {name_user} sebesar : Rp.{money_saving},-")
            
        if records_all:
            income_amount = []
            expense_amount = []
            total_income = 0
            total_expense = 0
            total_amount = 0
            
            for data in records_all:
                if data[5] == "income":
                    income_amount.append(data[4])
                elif data[5] == "expense":
                    expense_amount.append(data[4])
            
            if income_amount != []:
                total_income = sum(income_amount)
            
            if expense_amount != []:
                total_expense = sum(expense_amount)
            
            st.write("Info All:")    
            st.write("Total Income: Rp. {},-".format(total_income))
            st.write("Total Expense: Rp. {},-".format(total_expense))
            
            total_amount = total_income - total_expense
            
            st.write("Total Saldo: Rp. {},-".format(total_amount))
            
                        
                
        else:
            st.info("Belum ada informasi apapun disini.")
        
        
        st.subheader("Update")
        # Optional: Add functionality to edit or delete records directly from the table
        for index, record in records_df.iterrows():
            rec_id, rec_date, rec_name, rec_desc, rec_amount, rec_type = record
            with st.expander(f"Actions for {rec_desc}"):
                with st.form(f"edit_form_{rec_id}"):
                    new_date = st.date_input("Date", value=pd.to_datetime(rec_date))
                    new_desc = st.text_input("Description", value=rec_desc)
                    new_amount = st.number_input("Amount", min_value=0.0, format="%.2f", value=rec_amount)
                    new_type = st.selectbox("Type", ["income", "expense"], index=0 if rec_type == "income" else 1)
                    update_btn = st.form_submit_button("Update")
                    delete_btn = st.form_submit_button("Delete")
                    if update_btn:
                        if new_desc.strip() == "":
                            st.error("Description cannot be empty")
                        else:
                            update_record(rec_id, new_date.isoformat(), new_desc, new_amount, new_type)
                            st.success("Record updated successfully")
                            st.rerun()
                    if delete_btn:
                        delete_record(rec_id)
                        st.success("Record deleted successfully")
                        st.rerun()
    else:
        st.info("No records found. Add your first record above.")