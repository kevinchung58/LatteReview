import streamlit as st

# TODO 1.1: Basic Structure (Done)
# TODO 1.2: Project Management UI (Done)

def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")

    # Sidebar
    with st.sidebar:
        st.title("LatteReview 🤖☕")
        st.caption("Navigation & Settings")
        # Placeholder for future navigation items
        # st.page_link("app.py", label="Home / Project Management")

        st.divider() # Visually separate navigation from settings

        # TODO 1.3: 全域 API Key 設定
        # 細節:
        # - 在側邊欄 st.sidebar 中，新增一個 st.text_input 欄位，類型為 password，讓使用者輸入他們的 Gemini API Key。
        # - 使用 st.session_state 來安全地儲存該 Key，避免每次頁面刷新都要重新輸入。 (Session state logic later)
        # - 提示使用者模型將固定使用 gemini-2.0-flash。
        st.subheader("Settings")
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Google AI / Vertex AI API Key. LatteReview will use gemini-2.0-flash."
        )
        st.caption("Model: `gemini-2.0-flash` (fixed)")

        if api_key:
            # Placeholder for saving/using the API key
            # For now, just acknowledge input. Session state will handle persistence.
            # st.success("API Key entered (not saved yet).")
            pass


    # Main page content
    st.title("LatteReview 🤖☕")
    st.markdown("Welcome to LatteReview! Your AI-powered literature review assistant.")

    st.divider()
    st.subheader("Project Management")

    col1, col2 = st.columns([0.7, 0.3])

    with col1:
        st.write("#### Existing Projects")
        st.info("No projects found. Click 'Create New Project' to get started.")
        # projects = [] # Logic to list projects will be added later
        # if projects:
        #     for project in projects:
        #         if st.button(project, key=f"project_{project}"):
        #             st.session_state.current_project = project
        # else:
        #     st.info("No projects found. Click 'Create New Project' to get started.")

    with col2:
        if st.button("➕ Create New Project", use_container_width=True):
            st.session_state.show_create_project_modal = True

    if st.session_state.get("show_create_project_modal", False):
        # Using a more modal-like approach with st.dialog (new in Streamlit 1.3 dialogs)
        # For wider compatibility, will stick to a form for now, can be refactored to st.dialog
        with st.form("new_project_form"):
            st.subheader("Create New Project")
            project_name = st.text_input("Project Name")
            submitted = st.form_submit_button("Create Project")

            if submitted:
                if project_name:
                    st.success(f"Project '{project_name}' creation initiated (backend logic pending).")
                    # Actual project creation logic (e.g., creating a folder) will be added later.
                    # For now, just close the pseudo-modal
                    st.session_state.show_create_project_modal = False
                    st.rerun() # Rerun to hide the form
                else:
                    st.error("Project name cannot be empty.")


if __name__ == "__main__":
    main()
