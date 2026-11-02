
import streamlit as st
import brain_twin_db as db


# Assessment state that must never carry over to another account.
ASSESSMENT_KEYS = [
    "current_index",
    "answers",
    "memory_ready",
    "question_started_at",
    "ai_report",
    "ai_report_error",
    "skill_difficulty",
    "skill_stats",
    "question_order",
    "seen_questions",
    "category_schedule",
]


def clear_assessment_state():
    for key in ASSESSMENT_KEYS:
        "assessment_length",
        "assessment_started",
        st.session_state.pop(key, None)


def render_auth():
    """
    Show login/registration when logged out.
    Return True only when a user is authenticated.
    """

    st.markdown("# 🧠 MindTrace")
    st.caption("Your cognitive practice space. Sign in to continue.")

    # Logged-in user: show account controls.
    if st.session_state.get("user_id"):
        st.sidebar.markdown("### Your account")
        st.sidebar.write(
            f"Signed in as **{st.session_state.get('username', 'User')}**"
        )

        if st.sidebar.button("Log out", use_container_width=True):
            clear_assessment_state()
            st.session_state.pop("user_id", None)
            st.session_state.pop("username", None)
            st.rerun()

        return True

    login_tab, register_tab = st.tabs(["Sign in", "Create account"])

    with login_tab:
        with st.form("mindtrace_login_form"):
            login_username = st.text_input("Username")
            login_password = st.text_input(
                "Password",
                type="password"
            )
            login_submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True
            )

        if login_submitted:
            username = login_username.strip()

            if not username or not login_password:
                st.warning("Enter both your username and password.")
            else:
                try:
                    user_id = db.authenticate_user(
                        username,
                        login_password
                    )

                    if user_id:
                        clear_assessment_state()
                        st.session_state["user_id"] = user_id
                        st.session_state["username"] = username
                        st.rerun()
                    else:
                        st.error(
                            "Sign-in failed. Check your username and password."
                        )

                except Exception:
                    st.error(
                        "Sign-in could not be completed. "
                        "Check the application logs."
                    )

    with register_tab:
        with st.form("mindtrace_register_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input(
                "Create a password",
                type="password"
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            register_submitted = st.form_submit_button(
                "Create account",
                type="primary",
                use_container_width=True
            )

        if register_submitted:
            username = new_username.strip()

            if not username or not new_password:
                st.warning("Enter a username and password.")
            elif len(username) < 3:
                st.warning("Your username must contain at least 3 characters.")
            elif len(new_password) < 12:
                st.warning("Use a password with at least 12 characters.")
            elif new_password != confirm_password:
                st.error("The passwords do not match.")
            else:
                try:
                    db.create_user(username, new_password)
                    st.success(
                        "Account created! Open the Sign in tab to log in."
                    )
                except ValueError as error:
                    st.error(str(error))
                except Exception:
                    st.error(
                        "The account could not be created. "
                        "Check the username and try again."
                    )

    st.info(
        "Use a unique password. This prototype stores account records "
        "locally in its SQLite database."
    )

    return False

