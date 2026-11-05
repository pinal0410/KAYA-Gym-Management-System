import streamlit as st
from datetime import date
from db_connection import get_connection
from auth import require_login

require_login()
st.title("💰 Payment Management")
st.caption("A membership is activated automatically when its payment is recorded as Paid.")

connection = cursor = None
pending_memberships = []
try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("""
        SELECT ms.membership_id, ms.member_id, m.name AS member_name,
               p.plan_name, p.price, ms.start_date, ms.end_date
        FROM memberships ms
        JOIN members m ON ms.member_id = m.member_id
        JOIN membership_plans p ON ms.plan_id = p.plan_id
        WHERE ms.status = 'Pending'
        ORDER BY ms.membership_id DESC
    """)
    pending_memberships = cursor.fetchall()
except Exception as error:
    st.error(f"Could not load pending memberships: {error}")
finally:
    if cursor:
        cursor.close()
    if connection and connection.is_connected():
        connection.close()

st.subheader("➕ Record Membership Payment")
if not pending_memberships:
    st.info("There are no pending memberships. Assign a membership first.")
else:
    options = {
        f"{r['member_name']} | {r['plan_name']} | Membership #{r['membership_id']}": r
        for r in pending_memberships
    }
    with st.form("payment_form"):
        label = st.selectbox("Select Pending Membership", list(options))
        selected = options[label]
        st.metric("Amount to Pay", f"₹{float(selected['price']):,.2f}")
        payment_date = st.date_input("Payment Date", value=date.today())
        payment_method = st.selectbox("Payment Method", ["Cash", "UPI", "Card", "Bank Transfer"])
        payment_status = st.selectbox("Payment Status", ["Paid", "Pending"])
        submitted = st.form_submit_button("Save Payment")
    if submitted:
        conn = cur = None
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO payments
                    (member_id, membership_id, amount, payment_date, payment_method, payment_status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (selected['member_id'], selected['membership_id'], selected['price'], payment_date, payment_method, payment_status))
            if payment_status == "Paid":
                cur.execute("""
                    UPDATE memberships
                    SET status = CASE
                        WHEN end_date < %s THEN 'Expired'
                        WHEN start_date <= %s THEN 'Active'
                        ELSE 'Pending'
                    END
                    WHERE membership_id = %s AND status = 'Pending'
                """, (payment_date, payment_date, selected['membership_id']))
            conn.commit()
            if payment_status == "Paid":
                st.success("Payment recorded. Membership status has been updated.")
            else:
                st.success("Pending payment recorded. Membership remains inactive.")
            st.rerun()
        except Exception as error:
            if conn:
                conn.rollback()
            st.error(f"Could not record payment: {error}")
        finally:
            if cur:
                cur.close()
            if conn and conn.is_connected():
                conn.close()

st.divider()
st.subheader("📋 Payment History")
conn = cur = None
try:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT pay.payment_id, m.name AS member_name,
               pay.membership_id, pay.amount, pay.payment_date,
               pay.payment_method, pay.payment_status
        FROM payments pay
        JOIN members m ON pay.member_id = m.member_id
        ORDER BY pay.payment_id DESC
    """)
    payments = cur.fetchall()
    if payments:
        st.dataframe(payments, hide_index=True, width="stretch")
    else:
        st.info("No payments recorded yet.")
except Exception as error:
    st.error(f"Could not load payment history: {error}")
finally:
    if cur:
        cur.close()
    if conn and conn.is_connected():
        conn.close()
