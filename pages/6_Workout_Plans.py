import streamlit as st
from db_connection import get_connection
from datetime import date
from auth import require_login

require_login()


st.title("🏋️ Workout Plans Management")

WORKOUT_TYPES = [
    "Weight Training",
    "Cardio",
    "Yoga",
    "Strength Training",
    "Fat Loss",
    "Muscle Building",
    "Flexibility Training"
]


# ---------------- ASSIGN WORKOUT PLAN ----------------

st.subheader("➕ Assign Workout Plan")

try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT member_id, name FROM members ORDER BY name"
    )
    members = cursor.fetchall()

    cursor.execute(
        "SELECT trainer_id, name FROM trainers ORDER BY name"
    )
    trainers = cursor.fetchall()

    cursor.close()
    connection.close()

    if not members:
        st.warning("Please register a member first.")

    elif not trainers:
        st.warning("Please register a trainer first.")

    else:
        member_options = {
            f"{m['name']} (ID: {m['member_id']})": m["member_id"]
            for m in members
        }

        trainer_options = {
            f"{t['name']} (ID: {t['trainer_id']})": t["trainer_id"]
            for t in trainers
        }

        with st.form("workout_form"):
            selected_member = st.selectbox(
                "Select Member",
                list(member_options.keys())
            )

            selected_trainer = st.selectbox(
                "Select Trainer",
                list(trainer_options.keys())
            )

            workout_name = st.selectbox(
                "Select Workout Plan",
                WORKOUT_TYPES
            )

            description = st.text_area("Workout Description")

            start_date = st.date_input(
                "Start Date",
                value=date.today(),
                key="new_workout_start"
            )

            end_date = st.date_input(
                "End Date",
                value=date.today(),
                key="new_workout_end"
            )

            submitted = st.form_submit_button(
                "Assign Workout Plan"
            )

        if submitted:
            if end_date < start_date:
                st.error("End date cannot be before start date.")
            else:
                connection = None
                cursor = None

                try:
                    connection = get_connection()
                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        INSERT INTO workout_plans
                        (member_id, trainer_id, workout_name,
                         description, start_date, end_date)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            member_options[selected_member],
                            trainer_options[selected_trainer],
                            workout_name,
                            description.strip() or None,
                            start_date,
                            end_date
                        )
                    )

                    connection.commit()
                    st.success("Workout plan assigned successfully!")
                    st.rerun()

                except Exception as error:
                    if connection is not None:
                        connection.rollback()
                    st.error(f"Could not assign workout: {error}")

                finally:
                    if cursor is not None:
                        cursor.close()
                    if connection is not None and connection.is_connected():
                        connection.close()

except Exception as error:
    st.error(f"Could not load assignment form: {error}")


# ---------------- VIEW WORKOUT PLANS ----------------

st.divider()
st.subheader("📋 Assigned Workout Plans")

connection = None
cursor = None

try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            w.workout_id,
            w.member_id,
            w.trainer_id,
            m.name AS member_name,
            t.name AS trainer_name,
            w.workout_name,
            w.description,
            w.start_date,
            w.end_date
        FROM workout_plans w
        JOIN members m ON w.member_id = m.member_id
        JOIN trainers t ON w.trainer_id = t.trainer_id
        ORDER BY w.workout_id DESC
    """)

    workouts = cursor.fetchall()

    cursor.close()
    cursor = None
    connection.close()
    connection = None

    if workouts:
        st.dataframe(
            [
                {
                    "Workout ID": w["workout_id"],
                    "Member": w["member_name"],
                    "Trainer": w["trainer_name"],
                    "Workout Plan": w["workout_name"],
                    "Description": w["description"],
                    "Start Date": w["start_date"],
                    "End Date": w["end_date"]
                }
                for w in workouts
            ],
            hide_index=True,
            width="stretch"
        )

        workout_options = {
            (
                f"ID: {w['workout_id']} - {w['workout_name']} "
                f"(Member: {w['member_name']})"
            ): w["workout_id"]
            for w in workouts
        }

        workout_ids = {
            w["workout_id"]: w for w in workouts
        }

        # ---------------- EDIT WORKOUT PLAN ----------------

        st.divider()
        st.subheader("✏️ Edit Workout Plan")

        selected_edit_label = st.selectbox(
            "Select a workout plan to edit",
            list(workout_options.keys()),
            key="edit_workout_select"
        )

        selected_edit_id = workout_options[selected_edit_label]
        selected_edit = workout_ids[selected_edit_id]

        member_edit_options = {
            f"{m['name']} (ID: {m['member_id']})": m["member_id"]
            for m in members
        } if "members" in locals() else {}

        trainer_edit_options = {
            f"{t['name']} (ID: {t['trainer_id']})": t["trainer_id"]
            for t in trainers
        } if "trainers" in locals() else {}

        # Reload members and trainers for the edit form
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT member_id, name FROM members ORDER BY name"
        )
        edit_members = cursor.fetchall()

        cursor.execute(
            "SELECT trainer_id, name FROM trainers ORDER BY name"
        )
        edit_trainers = cursor.fetchall()

        cursor.close()
        connection.close()
        cursor = None
        connection = None

        member_edit_options = {
            f"{m['name']} (ID: {m['member_id']})": m["member_id"]
            for m in edit_members
        }

        trainer_edit_options = {
            f"{t['name']} (ID: {t['trainer_id']})": t["trainer_id"]
            for t in edit_trainers
        }

        member_labels = list(member_edit_options.keys())
        trainer_labels = list(trainer_edit_options.keys())

        current_member_label = next(
            (
                label for label, member_id in member_edit_options.items()
                if member_id == selected_edit["member_id"]
            ),
            member_labels[0]
        )

        current_trainer_label = next(
            (
                label for label, trainer_id in trainer_edit_options.items()
                if trainer_id == selected_edit["trainer_id"]
            ),
            trainer_labels[0]
        )

        current_workout = selected_edit["workout_name"]
        workout_index = (
            WORKOUT_TYPES.index(current_workout)
            if current_workout in WORKOUT_TYPES else 0
        )

        current_start = selected_edit["start_date"]
        current_end = selected_edit["end_date"]

        if not isinstance(current_start, date):
            current_start = date.today()

        if not isinstance(current_end, date):
            current_end = current_start

        with st.form("edit_workout_form"):
            edit_member = st.selectbox(
                "Member",
                member_labels,
                index=member_labels.index(current_member_label)
            )

            edit_trainer = st.selectbox(
                "Trainer",
                trainer_labels,
                index=trainer_labels.index(current_trainer_label)
            )

            edit_workout_name = st.selectbox(
                "Workout Plan",
                WORKOUT_TYPES,
                index=workout_index
            )

            edit_description = st.text_area(
                "Description",
                value=selected_edit["description"] or ""
            )

            edit_start_date = st.date_input(
                "Start Date",
                value=current_start,
                key="edit_start_date"
            )

            edit_end_date = st.date_input(
                "End Date",
                value=current_end,
                key="edit_end_date"
            )

            update_button = st.form_submit_button(
                "Update Workout Plan"
            )

        if update_button:
            if edit_end_date < edit_start_date:
                st.error("End date cannot be before start date.")
            else:
                update_connection = None
                update_cursor = None

                try:
                    update_connection = get_connection()
                    update_cursor = update_connection.cursor()

                    update_cursor.execute(
                        """
                        UPDATE workout_plans
                        SET member_id = %s,
                            trainer_id = %s,
                            workout_name = %s,
                            description = %s,
                            start_date = %s,
                            end_date = %s
                        WHERE workout_id = %s
                        """,
                        (
                            member_edit_options[edit_member],
                            trainer_edit_options[edit_trainer],
                            edit_workout_name,
                            edit_description.strip() or None,
                            edit_start_date,
                            edit_end_date,
                            selected_edit_id
                        )
                    )

                    update_connection.commit()
                    st.success("Workout plan updated successfully!")
                    st.rerun()

                except Exception as error:
                    if update_connection is not None:
                        update_connection.rollback()
                    st.error(f"Could not update workout plan: {error}")

                finally:
                    if update_cursor is not None:
                        update_cursor.close()
                    if (
                        update_connection is not None
                        and update_connection.is_connected()
                    ):
                        update_connection.close()

        # ---------------- DELETE WORKOUT PLAN ----------------

        st.divider()
        st.subheader("🗑️ Delete Workout Plan")

        selected_delete_label = st.selectbox(
            "Select a workout plan to delete",
            list(workout_options.keys()),
            key="delete_workout_select"
        )

        confirm_delete = st.checkbox(
            "I confirm that I want to permanently delete this workout plan.",
            key="confirm_workout_delete"
        )

        if st.button("Delete Workout Plan"):
            if not confirm_delete:
                st.warning("Please confirm before deleting.")
            else:
                delete_connection = None
                delete_cursor = None

                try:
                    delete_connection = get_connection()
                    delete_cursor = delete_connection.cursor()

                    delete_cursor.execute(
                        """
                        DELETE FROM workout_plans
                        WHERE workout_id = %s
                        """,
                        (workout_options[selected_delete_label],)
                    )

                    delete_connection.commit()
                    st.success("Workout plan deleted successfully!")
                    st.rerun()

                except Exception as error:
                    if delete_connection is not None:
                        delete_connection.rollback()
                    st.error(f"Could not delete workout plan: {error}")

                finally:
                    if delete_cursor is not None:
                        delete_cursor.close()
                    if (
                        delete_connection is not None
                        and delete_connection.is_connected()
                    ):
                        delete_connection.close()

    else:
        st.info("No workout plans assigned yet.")

except Exception as error:
    st.error(f"Could not load workout plans: {error}")

finally:
    if cursor is not None:
        cursor.close()
    if connection is not None and connection.is_connected():
        connection.close()
