
import hashlib
import secrets
from datetime import datetime, timedelta

import streamlit as st
import extra_streamlit_components as stx

from db_connection import get_connection


SESSION_COOKIE = "kaya_session"
SESSION_DAYS = 30
PBKDF2_ITERATIONS = 310000


# --------------------------------------------------
# PASSWORD SECURITY
# --------------------------------------------------

def hash_password(password):
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS
    ).hex()

    return f"pbkdf2_sha256${salt}${password_hash}"


def verify_password(password, stored_password):
    try:
        algorithm, salt, saved_hash = stored_password.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            PBKDF2_ITERATIONS
        ).hex()

        return secrets.compare_digest(password_hash, saved_hash)

    except (ValueError, AttributeError):
        return False


# --------------------------------------------------
# LOGIN SESSION
# --------------------------------------------------

def save_login(user, cursor, connection, cookie_manager):
    session_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        session_token.encode("utf-8")
    ).hexdigest()

    expiry = datetime.now() + timedelta(days=SESSION_DAYS)

    cursor.execute("""
        INSERT INTO auth_sessions (user_id, token_hash, expires_at)
        VALUES (%s, %s, %s)
    """, (user["user_id"], token_hash, expiry))

    connection.commit()

    cookie_manager.set(
        SESSION_COOKIE,
        session_token,
        expires_at=expiry,
        path="/",
        same_site="lax",
        secure=False
    )

    st.session_state.logged_in = True
    st.session_state.user_id = user["user_id"]
    st.session_state.username = user["username"]
    st.session_state.role = str(user["role"]).lower()
    st.session_state.member_id = user.get("member_id")
    st.session_state.trainer_id = user.get("trainer_id")


def restore_login(cursor, cookie_manager):
    session_token = cookie_manager.get(SESSION_COOKIE)

    if not session_token:
        return False

    token_hash = hashlib.sha256(
        session_token.encode("utf-8")
    ).hexdigest()

    cursor.execute("""
        SELECT u.user_id, u.username, u.role,
               u.member_id, u.trainer_id
        FROM auth_sessions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.token_hash = %s
          AND s.expires_at > NOW()
    """, (token_hash,))

    user = cursor.fetchone()

    if not user:
        return False

    st.session_state.logged_in = True
    st.session_state.user_id = user[0]
    st.session_state.username = user[1]
    st.session_state.role = str(user[2]).lower()
    st.session_state.member_id = user[3]
    st.session_state.trainer_id = user[4]

    return True


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

def logout(cursor, connection, cookie_manager):

    session_token = cookie_manager.get(SESSION_COOKIE)

    if session_token:
        token_hash = hashlib.sha256(
            session_token.encode("utf-8")
        ).hexdigest()

        cursor.execute("""
            DELETE FROM auth_sessions
            WHERE token_hash = %s
        """, (token_hash,))

        connection.commit()

    cookie_manager.delete(SESSION_COOKIE)

    for key in [
        "logged_in",
        "user_id",
        "username",
        "role",
        "member_id",
        "trainer_id"
    ]:
        st.session_state.pop(key, None)

    st.rerun()


# --------------------------------------------------
# LOGIN AND MEMBER SIGN UP
# --------------------------------------------------

def show_login_screen(cursor, connection, cookie_manager):

    st.title("KAYA")
    st.caption("GYM & FITNESS MANAGEMENT")
    st.write("Welcome to KAYA. Manage. Track. Transform.")

    login_tab, signup_tab = st.tabs([
        "🔐 Login",
        "📝 Member Sign Up"
    ])

    with login_tab:

        st.subheader("Login")

        with st.form("login_form"):

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submitted = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if submitted:

            cursor.execute("""
                SELECT user_id, username, password, role,
                       member_id, trainer_id
                FROM users
                WHERE username = %s
            """, (username.strip(),))

            row = cursor.fetchone()

            if row and verify_password(password, row[2]):

                user = {
                    "user_id": row[0],
                    "username": row[1],
                    "role": row[3],
                    "member_id": row[4],
                    "trainer_id": row[5]
                }

                save_login(user, cursor, connection, cookie_manager)
                st.rerun()

            else:
                st.error("Invalid username or password.")

    with signup_tab:

        st.subheader("Member Registration")

        st.info(
            "Use the phone number and email already registered "
            "with your gym."
        )

        with st.form("member_signup_form"):

            full_name = st.text_input("Registered Full Name")
            phone = st.text_input("Registered Phone Number")
            email = st.text_input("Registered Email")

            new_username = st.text_input("Create Username")
            new_password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")

            signup = st.form_submit_button(
                "Create Member Account",
                use_container_width=True
            )

        if signup:

            if not all([
                full_name.strip(),
                phone.strip(),
                email.strip(),
                new_username.strip(),
                new_password
            ]):
                st.error("Please fill in all fields.")

            elif len(new_password) < 8:
                st.error("Password must contain at least 8 characters.")

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            else:

                cursor.execute("""
                    SELECT member_id
                    FROM members
                    WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
                      AND phone = %s
                      AND LOWER(TRIM(email)) = LOWER(TRIM(%s))
                    LIMIT 1
                """, (
                    full_name.strip(),
                    phone.strip(),
                    email.strip()
                ))

                member = cursor.fetchone()

                if not member:
                    st.error(
                        "Member profile not found. "
                        "Please contact the gym Admin."
                    )

                else:

                    member_id = member[0]

                    cursor.execute("""
                        SELECT user_id
                        FROM users
                        WHERE username = %s OR member_id = %s
                    """, (new_username.strip(), member_id))

                    existing = cursor.fetchone()

                    if existing:
                        st.error(
                            "This username or member profile "
                            "already has an account."
                        )

                    else:

                        cursor.execute("""
                            INSERT INTO users
                            (username, password, role, member_id)
                            VALUES (%s, %s, 'Member', %s)
                        """, (
                            new_username.strip(),
                            hash_password(new_password),
                            member_id
                        ))

                        connection.commit()

                        st.success(
                            "Member account created! You can now log in."
                        )


# --------------------------------------------------
# MAIN LOGIN CHECK
# --------------------------------------------------

def require_login():

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    cookie_manager = stx.CookieManager(
        key="kaya_cookie_manager"
    )

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]

        # First Admin account setup
        if user_count == 0:

            st.title("KAYA")
            st.caption("GYM & FITNESS MANAGEMENT")
            st.subheader("Create Admin Account")

            with st.form("admin_setup_form"):

                username = st.text_input("Create Username")
                password = st.text_input("Create Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                submitted = st.form_submit_button(
                    "Create Admin Account",
                    use_container_width=True
                )

            if submitted:

                if not username.strip() or not password:
                    st.error("Please fill in all fields.")

                elif len(password) < 8:
                    st.error("Password must contain at least 8 characters.")

                elif password != confirm_password:
                    st.error("Passwords do not match.")

                else:

                    cursor.execute("""
                        INSERT INTO users (username, password, role)
                        VALUES (%s, %s, 'Admin')
                    """, (
                        username.strip(),
                        hash_password(password)
                    ))

                    connection.commit()
                    st.success("Admin account created successfully.")
                    st.rerun()

            st.stop()

        # Restore saved login
        if not st.session_state.logged_in:
            restore_login(cursor, cookie_manager)

        # Login screen
        if not st.session_state.logged_in:

            show_login_screen(
                cursor,
                connection,
                cookie_manager
            )

            st.stop()

        # Sidebar
        with st.sidebar:

            st.caption(
                f"Logged in as: "
                f"{st.session_state.get('username', 'User')}"
            )

            st.caption(
                f"Role: "
                f"{st.session_state.get('role', 'User').title()}"
            )

            if st.button("🚪 Logout", use_container_width=True):
                logout(cursor, connection, cookie_manager)

    except Exception as error:
        st.error(f"Authentication error: {error}")
        st.stop()

    finally:

        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# --------------------------------------------------
# ROLE PERMISSION CHECK
# --------------------------------------------------

def require_role(*allowed_roles):

    require_login()

    current_role = st.session_state.get("role", "").lower()
    allowed = [role.lower() for role in allowed_roles]

    if current_role not in allowed:
        st.error(
            "Access denied. You do not have permission to view this page."
        )
        st.stop()
