import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import plotly.express as px
from datetime import datetime

# ---------------- DATABASE ---------------- #
def run_query(q, params=(), fetch=False):
    conn = sqlite3.connect("hospital.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute(q, params)
    conn.commit()
    data = cur.fetchall() if fetch else None
    conn.close()
    return data

# Create tables
run_query("""CREATE TABLE IF NOT EXISTS users(
    username TEXT PRIMARY KEY,
    password BLOB
)""")

run_query("""CREATE TABLE IF NOT EXISTS doctors(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    specialty TEXT,
    total_slots INTEGER,
    booked_slots INTEGER DEFAULT 0
)""")

run_query("""CREATE TABLE IF NOT EXISTS patients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    blood TEXT,
    reason TEXT,
    payment REAL,
    visit_date TEXT
)""")

# ---------------- DESIGN ---------------- #
st.set_page_config(page_title="VitalNode Pro", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#4e73df,#1cc88a); color:white; }
div.stButton > button {
    border-radius: 20px;
    background: linear-gradient(to right,#36b9cc,#1cc88a);
    color:white;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- AUTH ---------------- #
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:

    st.title("🏥 VitalNode Pro")

    option = st.radio("Select Option", ["Login", "Sign Up"])

    if option == "Sign Up":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Create Account"):
            hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
            try:
                run_query("INSERT INTO users VALUES (?,?)", (u, hashed))
                st.success("Account Created!")
            except:
                st.error("Username already exists")

    if option == "Login":
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            user = run_query("SELECT * FROM users WHERE username=?", (u,), True)
            if user and bcrypt.checkpw(p.encode(), user[0][1]):
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Invalid credentials")

else:

    st.sidebar.title("🏥 Navigation")
    page = st.sidebar.radio("Menu", ["Dashboard", "Doctors Allotment", "Patient Details"])

    if st.sidebar.button("Logout"):
        st.session_state.auth = False
        st.rerun()

    # ---------------- DASHBOARD ---------------- #
    if page == "Dashboard":

        st.title("📊 Hospital Dashboard")

        patients = run_query("SELECT * FROM patients", fetch=True)
        doctors = run_query("SELECT * FROM doctors", fetch=True)

        total_visits = len(patients)
        total_revenue = sum([p[5] for p in patients]) if patients else 0

        col1, col2 = st.columns(2)
        col1.metric("Total Visits", total_visits)
        col2.metric("Total Revenue", f"₹ {total_revenue}")

        if patients:
            df = pd.DataFrame(patients,
                              columns=["ID","Name","Age","Blood",
                                       "Reason","Payment","Date"])

            fig = px.bar(df["Reason"].value_counts().reset_index(),
                         x="index", y="Reason",
                         labels={"index":"Reason","Reason":"Count"},
                         title="Visits by Reason")
            st.plotly_chart(fig, use_container_width=True)

        if doctors:
            df2 = pd.DataFrame(doctors,
                               columns=["ID","Name","Specialty",
                                        "Total Slots","Booked Slots"])
            fig2 = px.pie(df2,
                          names="Name",
                          values="Booked Slots",
                          title="Doctor Workload Distribution")
            st.plotly_chart(fig2, use_container_width=True)

    # ---------------- DOCTORS ---------------- #
    elif page == "Doctors Allotment":

        st.title("👨‍⚕️ Doctors Management")

        with st.form("add_doc"):
            name = st.text_input("Doctor Name")
            spec = st.text_input("Specialty")
            slots = st.number_input("Total Appointment Slots", 1, 100)
            if st.form_submit_button("Add Doctor"):
                run_query("INSERT INTO doctors (name,specialty,total_slots) VALUES (?,?,?)",
                          (name, spec, slots))
                st.success("Doctor Added")
                st.rerun()

        doctors = run_query("SELECT * FROM doctors", fetch=True)
        if doctors:
            df = pd.DataFrame(doctors,
                              columns=["ID","Name","Specialty",
                                       "Total Slots","Booked Slots"])
            df["Vacancies Left"] = df["Total Slots"] - df["Booked Slots"]
            st.dataframe(df)

            del_id = st.number_input("Enter Doctor ID to Remove", 0)
            if st.button("Remove Doctor"):
                run_query("DELETE FROM doctors WHERE id=?", (del_id,))
                st.success("Doctor Removed")
                st.rerun()

    # ---------------- PATIENTS ---------------- #
    elif page == "Patient Details":

        st.title("👥 Patient Management")

        with st.form("add_patient"):
            name = st.text_input("Patient Name")
            age = st.number_input("Age", 0, 120)
            blood = st.selectbox("Blood Group",
                                 ["A+","B+","O+","AB+","A-","B-","O-","AB-"])
            reason = st.text_input("Reason for Visit")
            payment = st.number_input("Payment Done (₹)", 0.0)
            if st.form_submit_button("Add Patient"):
                run_query("""INSERT INTO patients
                             (name,age,blood,reason,payment,visit_date)
                             VALUES (?,?,?,?,?,?)""",
                          (name, age, blood, reason, payment,
                           str(datetime.now().date())))
                st.success("Patient Added")
                st.rerun()

        patients = run_query("SELECT * FROM patients", fetch=True)
        if patients:
            df = pd.DataFrame(patients,
                              columns=["ID","Name","Age","Blood",
                                       "Reason","Payment","Visit Date"])
            st.dataframe(df)

            del_id = st.number_input("Enter Patient ID to Delete", 0)
            if st.button("Delete Patient"):
                run_query("DELETE FROM patients WHERE id=?", (del_id,))
                st.success("Patient Deleted")
                st.rerun()
