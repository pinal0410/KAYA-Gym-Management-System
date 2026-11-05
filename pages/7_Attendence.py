from auth import require_login

require_login()


import streamlit as st
from db_connection import get_connection
from datetime import date, datetime

st.title("📅 Attendance Management")

st.subheader("Mark Attendance")

connection = None
cursor = None

try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT member_id, name
        FROM members
        ORDER BY name
    """)

    members = cursor.fetchall()

    if not members:
        st.warning("Please register a member first.")
    else:
        member_options = {
            f"{member['name']} (ID: {member['member_id']})":
            member["member_id"]
            for member in members
        }

        with st.form("attendance_form"):
            selected_member = st.selectbox(
                "Select Member",
                list(member_options.keys())
            )

            attendance_date = st.date_input(
                "Attendance Date",
                value=date.today()
            )

            check_in = st.time_input(
                "Check-in Time",
                value=datetime.now().time().replace(
                    second=0, microsecond=0
                )
            )

            submitted = st.form_submit_button("Mark Attendance")

            if submitted:
                insert_cursor = connection.cursor()

                try:
                    insert_cursor.execute(
                        """
                        INSERT INTO attendance
                        (member_id, attendance_date, check_in)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            member_options[selected_member],
                            attendance_date,
                            check_in
                        )
                    )

                    connection.commit()
                    st.success("Attendance marked successfully!")

                except Exception as error:
                    connection.rollback()
                    st.error(f"Could not mark attendance: {error}")

                finally:
                    insert_cursor.close()

except Exception as error:
    st.error(f"Could not load attendance form: {error}")

finally:
    if cursor is not None:
        cursor.close()
    if connection is not None and connection.is_connected():
        connection.close()

st.divider()
st.subheader("📋 Attendance History")

connection = None
cursor = None

try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            a.attendance_id,
            m.name AS member_name,
            a.attendance_date,
            a.check_in
        FROM attendance a
        JOIN members m ON a.member_id = m.member_id
        ORDER BY a.attendance_date DESC, a.check_in DESC
    """)

    attendance_records = cursor.fetchall()

    st.caption(f"Total attendance records: {len(attendance_records)}")

    if attendance_records:
        st.dataframe(
            attendance_records,
            hide_index=True,
            width="stretch"
        )
    else:
        st.info("No attendance records yet.")

except Exception as error:
    st.error(f"Could not load attendance history: {error}")

finally:
    if cursor is not None:
        cursor.close()
    if connection is not None and connection.is_connected():
        connection.close()
