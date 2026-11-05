import streamlit as st
from datetime import date
from calendar import monthrange
from db_connection import get_connection
from auth import require_login

require_login()
st.title("🎫 Membership Management")
st.caption("Assign a plan first. A membership becomes active only after its payment is marked Paid.")


def calculate_end_date(start_date, months):
    total_month = start_date.month - 1 + int(months)
    year = start_date.year + total_month // 12
    month = total_month % 12 + 1
    day = min(start_date.day, monthrange(year, month)[1])
    return date(year, month, day)

members, plans = [], []
connection = cursor = None
try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT member_id, name FROM members ORDER BY name")
    members = cursor.fetchall()
    cursor.execute("SELECT plan_id, plan_name, duration_months, price FROM membership_plans ORDER BY price")
    plans = cursor.fetchall()
except Exception as error:
    st.error(f"Could not load members or plans: {error}")
finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()

st.subheader("➕ Assign Membership")
if not members:
    st.info("Please register a member first.")
elif not plans:
    st.info("Please add a membership plan first.")
else:
    member_options = {f"{m['name']} (ID: {m['member_id']})": m['member_id'] for m in members}
    plan_options = {f"{p['plan_name']} - {p['duration_months']} month(s) - ₹{p['price']}": p for p in plans}
    with st.form("membership_form"):
        member_label = st.selectbox("Select Member", list(member_options))
        plan_label = st.selectbox("Select Membership Plan", list(plan_options))
        start_date = st.date_input("Membership Start Date", value=date.today())
        plan = plan_options[plan_label]
        end_date = calculate_end_date(start_date, plan['duration_months'])
        st.info(f"Plan amount: ₹{float(plan['price']):,.2f} | End date: {end_date:%d-%m-%Y}")
        submitted = st.form_submit_button("Assign Membership")
    if submitted:
        conn = cur = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO memberships (member_id, plan_id, start_date, end_date, status) VALUES (%s, %s, %s, %s, 'Pending')",
                (member_options[member_label], plan['plan_id'], start_date, end_date),
            )
            conn.commit()
            st.success("Membership assigned as Pending. Record its payment to activate it.")
            st.rerun()
        except Exception as error:
            if conn:
                conn.rollback()
            st.error(f"Could not assign membership: {error}")
        finally:
            if cur:
                cur.close()
            if conn and conn.is_connected():
                conn.close()

st.divider()
st.subheader("📋 Membership Records")
conn = cur = None
try:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        UPDATE memberships SET status = 'Expired'
        WHERE end_date < CURDATE() AND status IN ('Active', 'Pending')
    """)
    conn.commit()
    cur.execute("""
        SELECT ms.membership_id, m.name AS member_name, p.plan_name, p.price,
               ms.start_date, ms.end_date, ms.status
        FROM memberships ms
        JOIN members m ON ms.member_id = m.member_id
        JOIN membership_plans p ON ms.plan_id = p.plan_id
        ORDER BY ms.membership_id DESC
    """)
    records = cur.fetchall()
    if records:
        st.dataframe(records, hide_index=True, width="stretch")
    else:
        st.info("No memberships assigned yet.")
except Exception as error:
    st.error(f"Could not load memberships: {error}")
finally:
    if cur:
        cur.close()
    if conn and conn.is_connected():
        conn.close()
