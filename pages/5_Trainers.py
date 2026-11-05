import streamlit as st
from db_connection import get_connection
from auth import require_login

require_login()


st.title("🏋️ Trainers Management")

# Register New Trainer
st.subheader("Register New Trainer")

with st.form("register_trainer_form"):
    name = st.text_input("Trainer Name")
    phone = st.text_input("Trainer Phone")
    email = st.text_input("Trainer Email")
    specialization = st.text_input("Specialization")

    salary = st.number_input(
        "Monthly Salary (₹)",
        min_value=0.0,
        step=1000.0
    )

    submitted = st.form_submit_button("Register Trainer")

    if submitted:
        if not name.strip():
            st.error("Please enter the trainer's name.")
        else:
            connection = None
            cursor = None

            try:
                connection = get_connection()
                cursor = connection.cursor()

                cursor.execute(
                    """
                    INSERT INTO trainers
                    (name, phone, email, specialization, salary)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        name.strip(),
                        phone.strip() or None,
                        email.strip() or None,
                        specialization.strip() or None,
                        salary
                    )
                )

                connection.commit()
                st.success("Trainer registered successfully!")
                st.rerun()

            except Exception as error:
                st.error(f"Could not register trainer: {error}")

            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None and connection.is_connected():
                    connection.close()

st.divider()

# Load Trainers
st.subheader("Registered Trainers")

connection = None
cursor = None
trainers = []

try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT trainer_id, name, phone, email, specialization, salary
        FROM trainers
        ORDER BY trainer_id DESC
    """)

    trainers = cursor.fetchall()

except Exception as error:
    st.error(f"Could not load trainers: {error}")

finally:
    if cursor is not None:
        cursor.close()
    if connection is not None and connection.is_connected():
        connection.close()

st.caption(f"Total registered trainers: {len(trainers)}")

if trainers:
    # Search Trainers
    search = st.text_input(
        "🔍 Search by name, phone, or specialization"
    )

    filtered_trainers = [
        trainer for trainer in trainers
        if search.strip().lower() in (trainer["name"] or "").lower()
        or search.strip().lower() in str(trainer["phone"] or "").lower()
        or search.strip().lower() in (
            trainer["specialization"] or ""
        ).lower()
    ]

    if filtered_trainers:
        st.dataframe(
            filtered_trainers,
            hide_index=True,
            width="stretch"
        )
    else:
        st.info("No matching trainers found.")

    st.divider()

    # Edit Trainer
    st.subheader("✏️ Edit Trainer")

    trainer_options = {
        f'{trainer["trainer_id"]} - {trainer["name"]}': trainer
        for trainer in trainers
    }

    selected_label = st.selectbox(
        "Select trainer to edit",
        list(trainer_options.keys()),
        key="edit_trainer_select"
    )

    selected_trainer = trainer_options[selected_label]

    with st.form("edit_trainer_form"):
        edit_name = st.text_input(
            "Trainer Name",
            value=selected_trainer["name"] or ""
        )

        edit_phone = st.text_input(
            "Trainer Phone",
            value=selected_trainer["phone"] or ""
        )

        edit_email = st.text_input(
            "Trainer Email",
            value=selected_trainer["email"] or ""
        )

        edit_specialization = st.text_input(
            "Specialization",
            value=selected_trainer["specialization"] or ""
        )

        edit_salary = st.number_input(
            "Monthly Salary (₹)",
            min_value=0.0,
            step=1000.0,
            value=float(selected_trainer["salary"] or 0)
        )

        update_button = st.form_submit_button("Update Trainer")

        if update_button:
            if not edit_name.strip():
                st.error("Trainer name cannot be empty.")
            else:
                connection = None
                cursor = None

                try:
                    connection = get_connection()
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        UPDATE trainers
                        SET name = %s,
                            phone = %s,
                            email = %s,
                            specialization = %s,
                            salary = %s
                        WHERE trainer_id = %s
                        """,
                        (
                            edit_name.strip(),
                            edit_phone.strip() or None,
                            edit_email.strip() or None,
                            edit_specialization.strip() or None,
                            edit_salary,
                            selected_trainer["trainer_id"]
                        )
                    )

                    connection.commit()
                    st.success("Trainer updated successfully!")
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not update trainer: {error}")

                finally:
                    if cursor is not None:
                        cursor.close()
                    if connection is not None and connection.is_connected():
                        connection.close()

    st.divider()

    # Delete Trainer
    st.subheader("🗑️ Delete Trainer")

    delete_label = st.selectbox(
        "Select trainer to delete",
        list(trainer_options.keys()),
        key="delete_trainer_select"
    )

    delete_trainer = trainer_options[delete_label]

    confirm_delete = st.checkbox(
        f'I confirm that I want to delete {delete_trainer["name"]}.',
        key="confirm_trainer_delete"
    )

    if st.button("Delete Trainer", type="secondary"):
        if not confirm_delete:
            st.warning("Please confirm before deleting the trainer.")
        else:
            connection = None
            cursor = None

            try:
                connection = get_connection()
                cursor = connection.cursor()

                trainer_id = delete_trainer["trainer_id"]

                # Check whether the trainer has assignments
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM workout_plans
                    WHERE trainer_id = %s
                    """,
                    (trainer_id,)
                )
                workout_count = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM bookings
                    WHERE trainer_id = %s
                    """,
                    (trainer_id,)
                )
                booking_count = cursor.fetchone()[0]

                if workout_count > 0 or booking_count > 0:
                    st.error(
                        "This trainer has assigned workout plans or bookings. "
                        "Reassign or remove those records before deleting "
                        "the trainer."
                    )
                else:
                    cursor.execute(
                        "DELETE FROM trainers WHERE trainer_id = %s",
                        (trainer_id,)
                    )

                    connection.commit()
                    st.success("Trainer deleted successfully!")
                    st.rerun()

            except Exception as error:
                st.error(f"Could not delete trainer: {error}")

            finally:
                if cursor is not None:
                    cursor.close()
                if connection is not None and connection.is_connected():
                    connection.close()

else:
    st.info("No trainers registered yet.")
