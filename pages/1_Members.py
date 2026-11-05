import streamlit as st
from db_connection import get_connection
from auth import require_login

require_login()

role = st.session_state.get("role", "").lower()
member_id = st.session_state.get("member_id")
trainer_id = st.session_state.get("trainer_id")

st.title("👥 Member Management")

# ==================================================
# ADMIN: REGISTER NEW MEMBER
# ==================================================

if role == "admin":

    st.subheader("Register New Member")

    with st.form("register_member_form"):

        st.markdown("### Personal Details")

        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        email = st.text_input("Email Address")

        gender = st.selectbox(
            "Gender",
            ["Select", "Male", "Female", "Other", "Prefer not to say"]
        )

        age = st.number_input(
            "Age (Years)",
            min_value=13,
            max_value=100,
            value=18
        )

        height = st.number_input(
            "Height (cm)",
            min_value=100.0,
            max_value=250.0,
            value=165.0,
            step=1.0
        )

        weight = st.number_input(
            "Weight (kg)",
            min_value=25.0,
            max_value=300.0,
            value=60.0,
            step=0.5
        )

        st.markdown("### Fitness Details")

        fitness_goal = st.selectbox(
            "Fitness Goal",
            [
                "General Fitness",
                "Strength Building",
                "Flexibility",
                "Stamina Improvement",
                "Stress Management"
            ]
        )

        experience_level = st.selectbox(
            "Experience Level",
            ["Beginner", "Intermediate", "Advanced"]
        )

        preferred_activity = st.selectbox(
            "Preferred Activity",
            [
                "Cardio",
                "Yoga",
                "Strength Training",
                "Swimming",
                "General Fitness"
            ]
        )

        available_days = st.selectbox(
            "Available Days Per Week",
            [1, 2, 3, 4, 5, 6, 7]
        )

        preferred_session = st.selectbox(
            "Preferred Session",
            ["Morning", "Afternoon", "Evening"]
        )

        monthly_budget = st.number_input(
            "Monthly Membership Budget (₹)",
            min_value=0.0,
            value=1000.0,
            step=500.0
        )

        preferred_duration = st.selectbox(
            "Preferred Membership Duration",
            [1, 3, 6, 12]
        )

        submitted = st.form_submit_button("Register Member")

        if submitted:

            if not name.strip():
                st.error("Please enter the member's name.")

            elif monthly_budget <= 0:
                st.error("Please enter a valid monthly budget.")

            else:
                connection = None
                cursor = None

                try:
                    connection = get_connection()
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        INSERT INTO members
                        (
                            name, phone, email, gender, join_date,
                            age, height_cm, weight_kg,
                            fitness_goal, experience_level,
                            preferred_activity, available_days,
                            preferred_session, monthly_budget,
                            preferred_duration
                        )
                        VALUES (
                            %s, %s, %s, %s, CURDATE(),
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            name.strip(),
                            phone.strip() or None,
                            email.strip() or None,
                            None if gender == "Select" else gender,
                            age,
                            height,
                            weight,
                            fitness_goal,
                            experience_level,
                            preferred_activity,
                            available_days,
                            preferred_session,
                            monthly_budget,
                            preferred_duration
                        )
                    )

                    connection.commit()
                    st.success("Member registered successfully!")
                    st.rerun()

                except Exception as error:
                    st.error(f"Registration error: {error}")

                finally:
                    if cursor is not None:
                        cursor.close()

                    if connection is not None and connection.is_connected():
                        connection.close()


# ==================================================
# LOAD MEMBERS ACCORDING TO USER ROLE
# ==================================================

st.divider()
st.subheader("📋 Member Information")

connection = None
cursor = None
members = []

try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    if role == "admin":

        cursor.execute("""
            SELECT *
            FROM members
            ORDER BY member_id DESC
        """)

        members = cursor.fetchall()

    elif role == "trainer":

        if trainer_id:

            cursor.execute(
                """
                SELECT DISTINCT m.*
                FROM members m
                INNER JOIN workout_plans w
                    ON m.member_id = w.member_id
                WHERE w.trainer_id = %s
                ORDER BY m.name
                """,
                (trainer_id,)
            )

            members = cursor.fetchall()

    elif role == "member":

        if member_id:

            cursor.execute(
                """
                SELECT *
                FROM members
                WHERE member_id = %s
                """,
                (member_id,)
            )

            members = cursor.fetchall()

except Exception as error:
    st.error(f"Could not load member information: {error}")

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None and connection.is_connected():
        connection.close()


# ==================================================
# DISPLAY MEMBERS
# ==================================================

if role == "admin":
    st.caption(f"Total registered members: {len(members)}")

elif role == "trainer":
    st.caption(f"Your assigned members: {len(members)}")

elif role == "member":
    st.caption("Your fitness profile")


if members:

    if role == "admin":

        search = st.text_input("🔍 Search member by name or phone")

        filtered_members = [
            member for member in members
            if search.strip().lower() in
            (member["name"] or "").lower()
            or search.strip().lower() in
            str(member["phone"] or "").lower()
        ]

        if filtered_members:

            display_members = []

            for serial_no, member in enumerate(filtered_members, start=1):

                display_member = {"Serial No.": serial_no}

                for key, value in member.items():
                    if key != "member_id":
                        display_member[key] = value

                display_members.append(display_member)

            st.dataframe(
                display_members,
                hide_index=True,
                width="stretch"
            )

        else:
            st.info("No matching members found.")

        selected_members = filtered_members

    else:
        selected_members = members

        if role == "trainer":
            st.dataframe(
                [
                    {
                        "Member Name": m["name"],
                        "Fitness Goal": m["fitness_goal"],
                        "Experience Level": m["experience_level"],
                        "Preferred Activity": m["preferred_activity"]
                    }
                    for m in members
                ],
                hide_index=True,
                width="stretch"
            )

    # ==================================================
    # MEMBER FITNESS PROFILE
    # ==================================================

    if selected_members:

        st.divider()
        st.subheader("⭐ Fitness Profile")

        if role == "admin" and len(selected_members) > 1:

            member_options = {
                f'{m["name"]} (ID: {m["member_id"]})': m
                for m in selected_members
            }

            selected_label = st.selectbox(
                "Select Member",
                list(member_options.keys())
            )

            selected_member = member_options[selected_label]

        else:
            selected_member = selected_members[0]

        st.write(f'**Name:** {selected_member["name"]}')

        if role == "admin":
            st.write(f'**Phone:** {selected_member["phone"]}')
            st.write(f'**Email:** {selected_member["email"]}')

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Age",
            f'{selected_member["age"] or "N/A"} years'
        )

        col2.metric(
            "Height",
            f'{selected_member["height_cm"] or "N/A"} cm'
        )

        col3.metric(
            "Weight",
            f'{selected_member["weight_kg"] or "N/A"} kg'
        )

        st.write(
            f'**Fitness Goal:** {selected_member["fitness_goal"] or "Not specified"}'
        )

        st.write(
            f'**Experience:** {selected_member["experience_level"] or "Not specified"}'
        )

        st.write(
            f'**Preferred Activity:** {selected_member["preferred_activity"] or "Not specified"}'
        )

        st.write(
            f'**Available Days:** {selected_member["available_days"] or "Not specified"}'
        )

        st.write(
            f'**Preferred Session:** {selected_member["preferred_session"] or "Not specified"}'
        )

        # ==================================================
        # FITNESS SUGGESTIONS
        # ==================================================

        st.divider()
        st.subheader("💡 Suggested Fitness Activities")

        goal = (
            selected_member.get("fitness_goal") or "General Fitness"
        ).lower()

        activity = (
            selected_member.get("preferred_activity") or "General Fitness"
        )

        level = (
            selected_member.get("experience_level") or "Beginner"
        ).lower()

        days = selected_member.get("available_days") or 3

        if "strength" in goal:

            suggestion = (
                "Ask a trainer to prepare a suitable strength routine "
                "with safe technique practice."
            )

        elif "flexibility" in goal:

            suggestion = (
                "Consider guided stretching, mobility exercises, "
                "or beginner yoga sessions."
            )

        elif "stamina" in goal:

            suggestion = (
                "Consider a gradual cardio routine such as walking "
                "or cycling."
            )

        elif "stress" in goal:

            suggestion = (
                "Consider gentle yoga, mobility work, "
                "or a relaxed activity you enjoy."
            )

        else:

            suggestion = (
                "Consider a balanced routine combining enjoyable cardio, "
                "mobility, and trainer-guided strength exercises."
            )

        st.info(
            f"Based on the fitness goal ({selected_member.get('fitness_goal')}) "
            f"and preferred activity ({activity}), a suitable starting "
            f"idea is: {suggestion} "
            f"The member has selected {days} available day(s) per week "
            f"and a {level} experience level. "
            "A qualified trainer should adjust the plan to the member's needs."
        )

else:

    if role == "trainer":
        st.info("No members have been assigned to you yet.")

    elif role == "member":
        st.info("Your member profile could not be found. Please contact Admin.")

    else:
        st.info("No members registered yet.")