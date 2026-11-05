import streamlit as st
import pandas as pd
from db_connection import get_connection
from auth import require_login

# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="KAYA | Fitness Management",
    page_icon="💪",
    layout="wide"
)

require_login()


# ---------------- CUSTOM DESIGN ----------------

st.markdown("""
<style>
.stApp {
    background-color: #0b1120;
    color: #f1f5f9;
}

header[data-testid="stHeader"] {
    background-color: transparent;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1450px;
}

.main-title {
    font-size: 38px;
    font-weight: 800;
    color: #C6A66B;
    letter-spacing: 4px;
}

.subtitle {
    color: #94a3b8;
    font-size: 15px;
    margin-bottom: 15px;
}

.section-title {
    color: #f8fafc;
    font-size: 22px;
    font-weight: 700;
    margin-top: 15px;
    margin-bottom: 15px;
}

.group-title {
    color: #C6A66B;
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 8px;
}

.stat-card {
    background: linear-gradient(145deg, #17243a, #111827);
    border: 1px solid #263751;
    border-radius: 15px;
    padding: 21px;
    min-height: 140px;
    box-shadow: 0 5px 18px rgba(0,0,0,0.18);
}

.stat-card:hover {
    border-color: #C6A66B;
}

.stat-icon {
    font-size: 25px;
    margin-bottom: 12px;
}

.stat-label {
    color: #a8b6ca;
    font-size: 13px;
    font-weight: 500;
}

.stat-number {
    color: #ffffff;
    font-size: 30px;
    font-weight: 800;
    margin-top: 7px;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #263751;
    border-radius: 12px;
    overflow: hidden;
}

.stButton button {
    border-radius: 8px;
}

hr {
    border-color: #263751;
}
</style>
""", unsafe_allow_html=True)


# ---------------- WELCOME HEADER ----------------

username = st.session_state.get("username", "Admin")

st.markdown("""
<div class="main-title">KAYA</div>
<div class="subtitle">GYM & FITNESS MANAGEMENT PLATFORM</div>
""", unsafe_allow_html=True)

st.markdown(f"### Welcome, {username} 👋")
st.caption("Manage your gym activities from one place.")

st.divider()


# ---------------- DATABASE CONNECTION ----------------

connection = None
cursor = None

try:
    connection = get_connection()
    cursor = connection.cursor()

    # ---------------- DASHBOARD OVERVIEW ----------------

    st.markdown(
        '<div class="section-title">📊 Dashboard Overview</div>',
        unsafe_allow_html=True
    )

    cursor.execute("SELECT COUNT(*) FROM members")
    total_members = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trainers")
    total_trainers = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM memberships
        WHERE status = 'Active'
        AND end_date >= CURDATE()
    """)
    active_memberships = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM attendance
        WHERE attendance_date = CURDATE()
    """)
    today_attendance = cursor.fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)

    cards = [
        (col1, "👥", "TOTAL MEMBERS", total_members),
        (col2, "🏋️", "TOTAL TRAINERS", total_trainers),
        (col3, "💳", "ACTIVE MEMBERSHIPS", active_memberships),
        (col4, "📅", "TODAY'S ATTENDANCE", today_attendance)
    ]

    for column, icon, label, value in cards:
        with column:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">{icon}</div>
                <div class="stat-label">{label}</div>
                <div class="stat-number">{value}</div>
            </div>
            """, unsafe_allow_html=True)

    # ---------------- QUICK NAVIGATION ----------------

    st.divider()

    st.markdown(
        '<div class="section-title">⚡ Quick Navigation</div>',
        unsafe_allow_html=True
    )

    st.caption("Access and manage all your gym modules.")

    # MEMBER MANAGEMENT

    st.markdown(
        '<div class="group-title">👥 MEMBER MANAGEMENT</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 👥 Members")
            st.caption("Manage member profiles.")
            st.page_link(
                "pages/1_Members.py",
                label="Open Members",
                icon="➡️"
            )

    with col2:
        with st.container(border=True):
            st.markdown("### 💳 Membership Plans")
            st.caption("Create and manage membership plans.")
            st.page_link(
                "pages/2_Membership_Plans.py",
                label="Open Plans",
                icon="➡️"
            )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 📋 Memberships")
            st.caption("Assign and manage memberships.")
            st.page_link(
                "pages/3_Memberships.py",
                label="Open Memberships",
                icon="➡️"
            )

    with col2:
        with st.container(border=True):
            st.markdown("### 📆 Bookings")
            st.caption("Manage member and trainer bookings.")
            st.page_link(
                "pages/4_Bookings.py",
                label="Open Bookings",
                icon="➡️"
            )

    # GYM OPERATIONS

    st.divider()

    st.markdown(
        '<div class="group-title">🏋️ GYM OPERATIONS</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 🏋️ Trainers")
            st.caption("Register and manage gym trainers.")
            st.page_link(
                "pages/5_Trainers.py",
                label="Open Trainers",
                icon="➡️"
            )

    with col2:
        with st.container(border=True):
            st.markdown("### 🏃 Workout Plans")
            st.caption("Assign and manage workout plans.")
            st.page_link(
                "pages/6_Workout_Plans.py",
                label="Open Workout Plans",
                icon="➡️"
            )

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("### 📅 Attendance")
            st.caption("Track daily gym attendance.")
            st.page_link(
                "pages/7_Attendence.py",
                label="Open Attendance",
                icon="➡️"
            )

    with col2:
        with st.container(border=True):
            st.markdown("### 💰 Payments")
            st.caption("Manage member payment records.")
            st.page_link(
                "pages/8_Payments.py",
                label="Open Payments",
                icon="➡️"
            )

    # ---------------- RECENT MEMBERS ----------------

    st.divider()

    st.markdown(
        '<div class="section-title">🆕 Recent Member Registrations</div>',
        unsafe_allow_html=True
    )

    cursor.execute("""
        SELECT member_id, name, phone, email, join_date
        FROM members
        ORDER BY member_id DESC
        LIMIT 5
    """)

    recent_members = cursor.fetchall()

    if recent_members:
        recent_df = pd.DataFrame(
            recent_members,
            columns=[
                "Member ID",
                "Member Name",
                "Phone",
                "Email",
                "Join Date"
            ]
        )

        st.dataframe(
            recent_df,
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No members registered yet.")

    # ---------------- GYM ANALYTICS ----------------

    st.divider()

    st.markdown(
        '<div class="section-title">📈 Gym Analytics</div>',
        unsafe_allow_html=True
    )

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        with st.container(border=True):
            st.markdown("#### 💳 Membership Status")

            cursor.execute("""
                SELECT status, COUNT(*)
                FROM memberships
                GROUP BY status
            """)

            membership_data = cursor.fetchall()

            if membership_data:
                membership_df = pd.DataFrame(
                    membership_data,
                    columns=["Status", "Total Members"]
                )

                st.bar_chart(
                    membership_df,
                    x="Status",
                    y="Total Members",
                    color="#C6A66B"
                )
            else:
                st.info("No membership records available.")

    with chart_col2:
        with st.container(border=True):
            st.markdown("#### 📅 Attendance - Last 7 Days")

            cursor.execute("""
                SELECT
                    DATE_FORMAT(attendance_date, '%d %b') AS day,
                    COUNT(*) AS total
                FROM attendance
                WHERE attendance_date >=
                    DATE_SUB(CURDATE(), INTERVAL 6 DAY)
                GROUP BY attendance_date
                ORDER BY attendance_date
            """)

            attendance_data = cursor.fetchall()

            if attendance_data:
                attendance_df = pd.DataFrame(
                    attendance_data,
                    columns=["Date", "Attendance"]
                )

                st.line_chart(
                    attendance_df,
                    x="Date",
                    y="Attendance",
                    color="#22c55e"
                )
            else:
                st.info("No attendance records for the last 7 days.")

except Exception as error:
    st.error(f"Dashboard error: {error}")

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None and connection.is_connected():
        connection.close()
