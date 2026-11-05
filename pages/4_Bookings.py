
import streamlit as st
from datetime import date, time
from db_connection import get_connection
from auth import require_login

require_login()

st.title("📅 Trainer Booking Management")

SESSION_CAPACITY = 5

st.caption(
    f"Choose your preferred trainer and book a session. "
    f"Only members with an active membership can book. "
    f"Each trainer time slot has a capacity of {SESSION_CAPACITY} bookings."
)

# --------------------------------------------------
# LOAD MEMBERS AND TRAINERS
# --------------------------------------------------

connection = cursor = None
members = []
trainers = []

try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT member_id, name
        FROM members
        ORDER BY name
    """)
    members = cursor.fetchall()

    cursor.execute("""
        SELECT trainer_id, name, specialization
        FROM trainers
        ORDER BY name
    """)
    trainers = cursor.fetchall()

except Exception as error:
    st.error(f"Could not load booking options: {error}")

finally:
    if cursor:
        cursor.close()

    if connection and connection.is_connected():
        connection.close()


# --------------------------------------------------
# TRAINER DIRECTORY
# --------------------------------------------------

st.subheader("🏋️ Our Trainers")

if trainers:
    columns = st.columns(2)

    for index, trainer in enumerate(trainers):
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"### 👤 {trainer['name']}")
                st.write(
                    f"**Specialization:** "
                    f"{trainer['specialization'] or 'General Fitness'}"
                )
                st.caption(f"Trainer ID: {trainer['trainer_id']}")
else:
    st.info("No trainers available. Please add trainers first.")

st.divider()


# --------------------------------------------------
# BOOK A TRAINER SESSION
# --------------------------------------------------

st.subheader("➕ Book Your Trainer Session")

if not members:
    st.warning("Please register a member first.")

elif not trainers:
    st.warning("Please add a trainer before making a booking.")

else:

    member_options = {
        f"{m['name']} (ID: {m['member_id']})": m['member_id']
        for m in members
    }

    trainer_options = {
        f"{t['name']} - {t['specialization'] or 'General Fitness'}":
        t['trainer_id']
        for t in trainers
    }

    with st.form("booking_form"):

        member_label = st.selectbox(
            "Select Member",
            list(member_options.keys())
        )

        trainer_label = st.selectbox(
            "Choose Your Trainer",
            list(trainer_options.keys())
        )

        booking_date = st.date_input(
            "Booking Date",
            value=date.today(),
            min_value=date.today()
        )

        booking_time = st.time_input(
            "Booking Time",
            value=time(10, 0)
        )

        submitted = st.form_submit_button(
            "📅 Book Session",
            use_container_width=True
        )

    if submitted:

        conn = cur = None

        try:
            conn = get_connection()
            cur = conn.cursor()

            member_id = member_options[member_label]
            trainer_id = trainer_options[trainer_label]

            # Check active membership
            cur.execute("""
                SELECT membership_id
                FROM memberships
                WHERE member_id = %s
                  AND status = 'Active'
                  AND start_date <= %s
                  AND end_date >= %s
                LIMIT 1
            """, (member_id, booking_date, booking_date))

            active_membership = cur.fetchone()

            if not active_membership:

                st.error(
                    "This member does not have an active membership "
                    "for the selected date."
                )

            else:

                # Check trainer's existing bookings
                cur.execute("""
                    SELECT COUNT(*)
                    FROM bookings
                    WHERE trainer_id = %s
                      AND booking_date = %s
                      AND booking_time = %s
                      AND status = 'Booked'
                """, (trainer_id, booking_date, booking_time))

                booked_count = cur.fetchone()[0]

                # Check duplicate booking
                cur.execute("""
                    SELECT COUNT(*)
                    FROM bookings
                    WHERE member_id = %s
                      AND trainer_id = %s
                      AND booking_date = %s
                      AND booking_time = %s
                      AND status = 'Booked'
                """, (
                    member_id,
                    trainer_id,
                    booking_date,
                    booking_time
                ))

                duplicate_count = cur.fetchone()[0]

                if duplicate_count:

                    st.warning(
                        "This member already has a booking "
                        "with this trainer at this time."
                    )

                elif booked_count >= SESSION_CAPACITY:

                    st.error(
                        f"This trainer's time slot is full. "
                        f"Maximum capacity is {SESSION_CAPACITY} bookings."
                    )

                else:

                    # Save booking
                    cur.execute("""
                        INSERT INTO bookings
                        (member_id, trainer_id, booking_date,
                         booking_time, status)
                        VALUES (%s, %s, %s, %s, 'Booked')
                    """, (
                        member_id,
                        trainer_id,
                        booking_date,
                        booking_time
                    ))

                    conn.commit()

                    st.success(
                        f"Session successfully booked with "
                        f"{trainer_label}!"
                    )

                    st.rerun()

        except Exception as error:

            if conn:
                conn.rollback()

            st.error(f"Could not book session: {error}")

        finally:

            if cur:
                cur.close()

            if conn and conn.is_connected():
                conn.close()


# --------------------------------------------------
# BOOKING HISTORY
# --------------------------------------------------

st.divider()

st.subheader("📋 Booking History")

conn = cur = None

try:
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT
            b.booking_id,
            m.name AS member_name,
            t.name AS trainer_name,
            t.specialization,
            b.booking_date,
            b.booking_time,
            b.status
        FROM bookings b
        JOIN members m ON b.member_id = m.member_id
        JOIN trainers t ON b.trainer_id = t.trainer_id
        ORDER BY b.booking_date DESC, b.booking_time DESC
    """)

    bookings = cur.fetchall()

    if bookings:
        st.dataframe(
            bookings,
            hide_index=True,
            width="stretch"
        )
    else:
        st.info("No bookings made yet.")

except Exception as error:
    st.error(f"Could not load booking history: {error}")

finally:
    if cur:
        cur.close()

    if conn and conn.is_connected():
        conn.close()
