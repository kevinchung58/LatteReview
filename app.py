import streamlit as st
import os
import re # For sanitizing project name
from datetime import datetime # For timestamping
import json # For reading project config

# TODO 1.1: Basic Structure (Done)
# TODO 1.2: Project Management (UI & Backend Done)
# TODO 1.3: Global API Key Setting (UI & Backend Done)

PROJECTS_ROOT_DIR = "lattereview_projects"

def sanitize_project_name(name):
    """Sanitizes a string to be a valid directory name."""
    name = name.strip()
    name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name

def create_project_structure(project_name):
    """Creates the directory structure for a new project."""
    sanitized_name = sanitize_project_name(project_name)
    if not sanitized_name:
        st.error("Invalid project name after sanitization. Please use allowed characters.")
        return False

    project_path = os.path.join(PROJECTS_ROOT_DIR, sanitized_name)

    if os.path.exists(project_path):
        st.error(f"Project '{sanitized_name}' already exists.")
        return False
    try:
        os.makedirs(project_path)
        data_path = os.path.join(project_path, "data")
        os.makedirs(data_path)
        os.makedirs(os.path.join(project_path, "results"))
        current_time_iso = datetime.now().isoformat()
        with open(os.path.join(project_path, "project_config.json"), 'w') as f:
            json.dump({"project_name": project_name, "sanitized_name": sanitized_name, "created_at": current_time_iso}, f, indent=2)
        with open(os.path.join(project_path, "README.md"), 'w') as f:
            f.write(f"# Project: {project_name}\n\nDirectory: {sanitized_name}\nCreated: {current_time_iso}\n\nThis project was created by LatteReview GUI.")
        st.success(f"Project '{project_name}' (directory: '{sanitized_name}') created successfully!")
        return True
    except OSError as e:
        st.error(f"Error creating project directory: {e}")
        return False

def get_existing_projects():
    """Scans the projects root directory and returns a list of project names."""
    if not os.path.exists(PROJECTS_ROOT_DIR):
        return []
    projects = []
    for item in os.listdir(PROJECTS_ROOT_DIR):
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)):
            # Try to read original name from config
            display_name = item # Fallback to directory name
            try:
                config_path = os.path.join(PROJECTS_ROOT_DIR, item, "project_config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f_cfg:
                        cfg = json.load(f_cfg)
                        display_name = cfg.get("project_name", item)
                projects.append({"id": item, "name": display_name})
            except Exception:
                 projects.append({"id": item, "name": item}) # Fallback
    return sorted(projects, key=lambda x: x["name"])


def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")

    # Initialize session state variables
    if "api_key_entered" not in st.session_state:
        st.session_state.api_key_entered = False
    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = ""
    if "show_create_project_modal" not in st.session_state:
        st.session_state.show_create_project_modal = False
    if "selected_project_id" not in st.session_state: # Store sanitized name as ID
        st.session_state.selected_project_id = None
    if "selected_project_display_name" not in st.session_state:
        st.session_state.selected_project_display_name = None


    # Sidebar
    with st.sidebar:
        st.title("LatteReview 🤖☕")
        st.caption("Navigation & Settings")
        st.divider()
        st.subheader("Settings")
        api_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.gemini_api_key if st.session_state.api_key_entered else "",
            help="Enter your Google AI / Vertex AI API Key. LatteReview will use gemini-2.0-flash.",
            key="api_key_input_widget"
        )
        if api_key_input and api_key_input != st.session_state.gemini_api_key :
            st.session_state.gemini_api_key = api_key_input
            st.session_state.api_key_entered = True
            st.success("API Key stored in session.")
            st.rerun()
        elif st.session_state.api_key_entered:
            st.success("API Key is set in session.")
        st.caption("Model: `gemini-2.0-flash` (fixed)")

    # Main page content
    st.title("LatteReview 🤖☕")

    if not st.session_state.api_key_entered or not st.session_state.gemini_api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to enable all features.", icon="🔑")

    st.markdown("Welcome to LatteReview! Your AI-powered literature review assistant.")
    st.divider()

    # Project Management Section
    st.subheader("Project Management")
    if not os.path.exists(PROJECTS_ROOT_DIR):
        os.makedirs(PROJECTS_ROOT_DIR)

    col_projects, col_actions = st.columns([0.7, 0.3])

    with col_projects:
        st.write("#### Existing Projects")
        existing_projects_list = get_existing_projects()
        if not existing_projects_list:
            st.info("No projects found. Click 'Create New Project' to get started.")
        else:
            for proj in existing_projects_list:
                if st.button(f"Open: {proj['name']}", key=f"project_{proj['id']}", use_container_width=True,
                             type="primary" if st.session_state.selected_project_id == proj['id'] else "secondary"):
                    st.session_state.selected_project_id = proj['id']
                    st.session_state.selected_project_display_name = proj['name']
                    st.rerun()

    with col_actions:
        if st.button("➕ Create New Project", use_container_width=True):
            st.session_state.show_create_project_modal = True

        if st.session_state.selected_project_id:
            st.success(f"Active project: **{st.session_state.selected_project_display_name}** (`{st.session_state.selected_project_id}`)")
            if st.button("✖️ Close Project", use_container_width=True):
                st.session_state.selected_project_id = None
                st.session_state.selected_project_display_name = None
                st.rerun()

    if st.session_state.get("show_create_project_modal", False):
        with st.form("new_project_form"):
            st.subheader("Create New Project")
            project_name_input = st.text_input("Project Name")
            submitted = st.form_submit_button("Create Project")
            if submitted:
                if project_name_input:
                    if create_project_structure(project_name_input):
                        st.session_state.show_create_project_modal = False
                        st.rerun()
                else:
                    st.error("Project name cannot be empty.")

    st.divider()

    # TODO 2.1: 實作 RIS 檔案上傳功能
    # - 在專案頁面中，使用 st.file_uploader 允許使用者上傳 .ris 檔案。
    # - 限制檔案類型為 ['ris']。
    # - 上傳後，後端呼叫現有的 RIS 解析器來處理檔案。(Parsing later, just save for now)
    if st.session_state.selected_project_id:
        st.subheader(f"Data Management for: {st.session_state.selected_project_display_name}")

        project_data_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "data")

        uploaded_file = st.file_uploader(
            "Upload RIS File",
            type=['ris'],
            accept_multiple_files=False, # For now, one main RIS file per project simplicity
            key=f"ris_uploader_{st.session_state.selected_project_id}" # Key to reset on project change
        )

        if uploaded_file is not None:
            # Save the uploaded file
            file_path = os.path.join(project_data_path, uploaded_file.name)
            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"File '{uploaded_file.name}' uploaded successfully to project '{st.session_state.selected_project_display_name}'.")
                # TODO 2.2 will display preview here.
            except Exception as e:
                st.error(f"Error saving uploaded file: {e}")

        # Display existing RIS files in project's data directory
        st.write("##### Existing RIS files in project:")
        try:
            ris_files_in_project = [f for f in os.listdir(project_data_path) if f.endswith(".ris")]
            if ris_files_in_project:
                for ris_file in ris_files_in_project:
                    st.text(ris_file)
            else:
                st.caption("No RIS files found in this project's data directory.")
        except FileNotFoundError:
            st.error(f"Project data directory not found: {project_data_path}. This should not happen if project was created correctly.")


if __name__ == "__main__":
    main()
