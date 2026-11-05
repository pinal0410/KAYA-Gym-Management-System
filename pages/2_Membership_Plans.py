import streamlit as st
from db_connection import get_connection
from auth import require_login

require_login()
role = st.session_state.get("role", "").lower()

st.title("💳 Membership Plans Management")


# ---------------- LOAD MEMBERSHIP PLANS ----------------

connection = None
cursor = None
plans = []

try:
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT plan_id, plan_name, duration_months,
               price, description
        FROM membership_plans
        ORDER BY plan_id DESC
    """)

    plans = cursor.fetchall()

except Exception as error:
    st.error(f"Could not load membership plans: {error}")

finally:
    if cursor is not None:
        cursor.close()

    if connection is not None and connection.is_connected():
        connection.close()


# ---------------- AVAILABLE MEMBERSHIP PLANS ----------------

st.subheader("📋 Available Membership Plans")

st.caption(f"Total membership plans: {len(plans)}")

if plans:

    search = st.text_input("🔍 Search plans by name")

    filtered_plans = [
        plan for plan in plans
        if search.strip().lower() in
        (plan["plan_name"] or "").lower()
    ]

    if filtered_plans:
        st.dataframe(
            filtered_plans,
            hide_index=True,
            width="stretch"
        )
    else:
        st.info("No matching membership plans found.")

    plan_options = {
        f'{plan["plan_id"]} - {plan["plan_name"]}': plan
        for plan in plans
    }

    st.divider()

    if role == "admin":
            # ---------------- EDIT MEMBERSHIP PLAN ----------------

            st.subheader("✏️ Edit Membership Plan")

            selected_label = st.selectbox(
                "Select Plan to Edit",
                list(plan_options.keys()),
                key="edit_plan_select"
            )

            selected_plan = plan_options[selected_label]

            duration_options = [1, 3, 6, 12]
            current_duration = int(selected_plan["duration_months"])

            if current_duration not in duration_options:
                duration_options.append(current_duration)
                duration_options.sort()

            with st.form("edit_membership_plan_form"):

                edit_name = st.text_input(
                    "Plan Name",
                    value=selected_plan["plan_name"] or ""
                )

                edit_duration = st.selectbox(
                    "Duration (Months)",
                    duration_options,
                    index=duration_options.index(current_duration)
                )

                edit_price = st.number_input(
                    "Plan Price (₹)",
                    min_value=0.0,
                    step=500.0,
                    value=float(selected_plan["price"] or 0)
                )

                edit_description = st.text_area(
                    "Plan Description",
                    value=selected_plan["description"] or ""
                )

                update_button = st.form_submit_button("Update Plan")

                if update_button:

                    if not edit_name.strip():
                        st.error("Please enter a plan name.")

                    elif edit_price <= 0:
                        st.error("Plan price must be greater than zero.")

                    else:
                        connection = None
                        cursor = None

                        try:
                            connection = get_connection()
                            cursor = connection.cursor()

                            cursor.execute("""
                                UPDATE membership_plans
                                SET plan_name = %s,
                                    duration_months = %s,
                                    price = %s,
                                    description = %s
                                WHERE plan_id = %s
                            """, (
                                edit_name.strip(),
                                edit_duration,
                                edit_price,
                                edit_description.strip() or None,
                                selected_plan["plan_id"]
                            ))

                            connection.commit()

                            st.success("Membership plan updated successfully!")
                            st.rerun()

                        except Exception as error:
                            st.error(f"Could not update plan: {error}")

                        finally:
                            if cursor is not None:
                                cursor.close()

                            if connection is not None and connection.is_connected():
                                connection.close()

            st.divider()

            # ---------------- DELETE MEMBERSHIP PLAN ----------------

            st.subheader("🗑️ Delete Membership Plan")

            delete_label = st.selectbox(
                "Select Plan to Delete",
                list(plan_options.keys()),
                key="delete_plan_select"
            )

            delete_plan = plan_options[delete_label]

            confirm_delete = st.checkbox(
                f'I confirm that I want to delete "{delete_plan["plan_name"]}".',
                key="confirm_plan_delete"
            )

            if st.button("Delete Membership Plan", type="secondary"):

                if not confirm_delete:
                    st.warning("Please confirm before deleting the plan.")

                else:
                    connection = None
                    cursor = None

                    try:
                        connection = get_connection()
                        cursor = connection.cursor()

                        cursor.execute("""
                            SELECT COUNT(*)
                            FROM memberships
                            WHERE plan_id = %s
                        """, (delete_plan["plan_id"],))

                        assigned_count = cursor.fetchone()[0]

                        if assigned_count > 0:
                            st.error(
                                "This plan is assigned to existing memberships. "
                                "It cannot be deleted."
                            )

                        else:
                            cursor.execute("""
                                DELETE FROM membership_plans
                                WHERE plan_id = %s
                            """, (delete_plan["plan_id"],))

                            connection.commit()

                            st.success("Membership plan deleted successfully!")
                            st.rerun()

                    except Exception as error:
                        st.error(f"Could not delete plan: {error}")

                    finally:
                        if cursor is not None:
                            cursor.close()

                        if connection is not None and connection.is_connected():
                            connection.close()

else:
    st.info("No membership plans added yet.")


if role == "admin":
    # ---------------- ADD MEMBERSHIP PLAN ----------------

    st.divider()

    st.subheader("➕ Add Membership Plan")

    with st.form("membership_plan_form"):

        plan_name = st.text_input("Plan Name")

        duration_months = st.selectbox(
            "Duration (Months)",
            [1, 3, 6, 12]
        )

        price = st.number_input(
            "Plan Price (₹)",
            min_value=0.0,
            step=500.0
        )

        description = st.text_area("Plan Description")

        submitted = st.form_submit_button("Add Plan")

        if submitted:

            if not plan_name.strip():
                st.error("Please enter a plan name.")

            elif price <= 0:
                st.error("Plan price must be greater than zero.")

            else:
                connection = None
                cursor = None

                try:
                    connection = get_connection()
                    cursor = connection.cursor()

                    cursor.execute("""
                        INSERT INTO membership_plans
                        (plan_name, duration_months, price, description)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        plan_name.strip(),
                        duration_months,
                        price,
                        description.strip() or None
                    ))

                    connection.commit()

                    st.success("Membership plan added successfully!")
                    st.rerun()

                except Exception as error:
                    st.error(f"Could not add plan: {error}")

                finally:
                    if cursor is not None:
                        cursor.close()

                    if connection is not None and connection.is_connected():
                        connection.close()
