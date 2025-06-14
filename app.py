import streamlit as st
import os
import re # For sanitizing project name
from datetime import datetime # For timestamping
import json # For reading project config
from lattereview.utils import data_handler # For RIS parsing
import pandas as pd # For DataFrame

PROJECTS_ROOT_DIR = "lattereview_projects"

def sanitize_project_name(name):
    name = name.strip()
    name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name

def create_project_structure(project_name):
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
    if not os.path.exists(PROJECTS_ROOT_DIR):
        return []
    projects = []
    for item in os.listdir(PROJECTS_ROOT_DIR):
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)):
            display_name = item
            try:
                config_path = os.path.join(PROJECTS_ROOT_DIR, item, "project_config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f_cfg:
                        cfg = json.load(f_cfg)
                        display_name = cfg.get("project_name", item)
                projects.append({"id": item, "name": display_name})
            except Exception:
                 projects.append({"id": item, "name": item})
    return sorted(projects, key=lambda x: x["name"])

def parse_ris_file(file_path):
    try:
        ris_handler = data_handler.RISHandler()
        df = ris_handler.load_ris_file_to_dataframe(file_path)
        # Standardize column names for preview - adapt based on actual RISHandler output
        # Common RIS fields: TY (Type), TI (Title), AB (Abstract), PY (Year), AU (Authors), ID (Record ID)
        # The RISHandler might already produce consistent names. If not, map them here.
        # For example, if title is 'primary_title': df.rename(columns={'primary_title': 'Title'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Error parsing RIS file '{os.path.basename(file_path)}': {e}")
        return None

def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")

    if "api_key_entered" not in st.session_state: st.session_state.api_key_entered = False
    if "gemini_api_key" not in st.session_state: st.session_state.gemini_api_key = ""
    if "show_create_project_modal" not in st.session_state: st.session_state.show_create_project_modal = False
    if "selected_project_id" not in st.session_state: st.session_state.selected_project_id = None
    if "selected_project_display_name" not in st.session_state: st.session_state.selected_project_display_name = None
    if "ris_dataframes" not in st.session_state: st.session_state.ris_dataframes = {}
    if "active_ris_filename" not in st.session_state: # Tracks the filename whose data is currently displayed/active
        st.session_state.active_ris_filename = None

    with st.sidebar:
        st.title("LatteReview 🤖☕")
        st.caption("Navigation & Settings")
        st.divider()
        st.subheader("Settings")
        api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_api_key if st.session_state.api_key_entered else "", help="Enter your Google AI / Vertex AI API Key. LatteReview will use gemini-2.0-flash.", key="api_key_input_widget")
        if api_key_input and api_key_input != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = api_key_input
            st.session_state.api_key_entered = True
            st.success("API Key stored in session.")
            st.rerun()
        elif st.session_state.api_key_entered: st.success("API Key is set in session.")
        st.caption("Model: `gemini-2.0-flash` (fixed)")

    st.title("LatteReview 🤖☕")
    if not st.session_state.api_key_entered or not st.session_state.gemini_api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to enable all features.", icon="🔑")
    st.markdown("Welcome to LatteReview! Your AI-powered literature review assistant.")
    st.divider()

    st.subheader("Project Management")
    if not os.path.exists(PROJECTS_ROOT_DIR): os.makedirs(PROJECTS_ROOT_DIR)
    col_projects, col_actions = st.columns([0.7, 0.3])
    with col_projects:
        st.write("#### Existing Projects")
        existing_projects_list = get_existing_projects()
        if not existing_projects_list: st.info("No projects found. Click 'Create New Project'.")
        else:
            for proj in existing_projects_list:
                if st.button(f"Open: {proj['name']}", key=f"project_{proj['id']}", use_container_width=True, type="primary" if st.session_state.selected_project_id == proj['id'] else "secondary"):
                    st.session_state.selected_project_id = proj['id']
                    st.session_state.selected_project_display_name = proj['name']
                    st.session_state.active_ris_filename = None # Reset active file on project change
                    if st.session_state.selected_project_id not in st.session_state.ris_dataframes:
                        st.session_state.ris_dataframes[st.session_state.selected_project_id] = {}
                    st.rerun()
    with col_actions:
        if st.button("➕ Create New Project", use_container_width=True): st.session_state.show_create_project_modal = True
        if st.session_state.selected_project_id:
            st.success(f"Active project: **{st.session_state.selected_project_display_name}** (`{st.session_state.selected_project_id}`)")
            if st.button("✖️ Close Project", use_container_width=True):
                st.session_state.selected_project_id = None
                st.session_state.selected_project_display_name = None
                st.session_state.active_ris_filename = None
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
                else: st.error("Project name cannot be empty.")
    st.divider()

    if st.session_state.selected_project_id:
        st.subheader(f"Data Management for: {st.session_state.selected_project_display_name}")
        project_data_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "data")

        with st.expander("Upload New RIS File", expanded=True):
            uploaded_file = st.file_uploader("Upload .ris File", type=['ris'], accept_multiple_files=False, key=f"ris_uploader_{st.session_state.selected_project_id}")
            if uploaded_file is not None:
                file_path = os.path.join(project_data_path, uploaded_file.name)
                try:
                    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    st.success(f"File '{uploaded_file.name}' uploaded successfully.")
                    st.session_state.active_ris_filename = None # Reset to allow processing new/different file
                except Exception as e: st.error(f"Error saving uploaded file: {e}")

        st.write("##### Process and View Existing RIS File")
        ris_files_in_project = [f for f in os.listdir(project_data_path) if f.endswith(".ris")]
        if not ris_files_in_project: st.caption("No RIS files found. Upload one above.")
        else:
            selected_ris_to_view = st.selectbox("Select a RIS file to process/view:", options=[""] + ris_files_in_project, index=0, key=f"select_ris_{st.session_state.selected_project_id}",
                                                format_func=lambda x: "Select a file..." if x == "" else x)

            if selected_ris_to_view:
                # Check if data is already parsed and in session state
                current_df = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(selected_ris_to_view)

                if current_df is None: # Not parsed yet or parsing failed previously
                    if st.button(f"Process '{selected_ris_to_view}'", key=f"process_{selected_ris_to_view}"):
                        full_file_path = os.path.join(project_data_path, selected_ris_to_view)
                        df = parse_ris_file(full_file_path)
                        if df is not None:
                            st.session_state.ris_dataframes[st.session_state.selected_project_id][selected_ris_to_view] = df
                            st.session_state.active_ris_filename = selected_ris_to_view
                            st.success(f"Successfully parsed '{selected_ris_to_view}'.")
                            st.rerun() # Rerun to display the dataframe
                        else: # Error handled in parse_ris_file
                            st.session_state.active_ris_filename = None
                            if selected_ris_to_view in st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}):
                                del st.session_state.ris_dataframes[st.session_state.selected_project_id][selected_ris_to_view]
                else: # Data is already parsed
                    st.session_state.active_ris_filename = selected_ris_to_view

        # Display DataFrame if one is active for the current project
        active_df_to_display = None
        if st.session_state.active_ris_filename and st.session_state.selected_project_id:
            active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)

        if active_df_to_display is not None:
            st.markdown(f"#### Preview for: `{st.session_state.active_ris_filename}`")
            st.info(f"Total articles imported: **{len(active_df_to_display)}**")

            # Define essential columns for preview - adjust based on typical RISHandler output
            # Common columns: 'id', 'title', 'abstract', 'year', 'authors', 'journal', 'keywords'
            # Check actual columns from RISHandler and select the most relevant ones.
            # If the parser produces 'primary_title', 'TI', etc., they should be mapped or used directly.
            preview_cols = []
            if 'id' in active_df_to_display.columns: preview_cols.append('id')
            if 'title' in active_df_to_display.columns: preview_cols.append('title')
            elif 'TI' in active_df_to_display.columns: preview_cols.append('TI') # Fallback
            elif 'primary_title' in active_df_to_display.columns: preview_cols.append('primary_title')

            if 'abstract' in active_df_to_display.columns: preview_cols.append('abstract')
            elif 'AB' in active_df_to_display.columns: preview_cols.append('AB')

            if 'year' in active_df_to_display.columns: preview_cols.append('year')
            elif 'PY' in active_df_to_display.columns: preview_cols.append('PY')

            if 'authors' in active_df_to_display.columns: preview_cols.append('authors')
            elif 'AU' in active_df_to_display.columns: preview_cols.append('AU')

            # Ensure only existing columns are selected
            final_preview_cols = [col for col in preview_cols if col in active_df_to_display.columns]
            if not final_preview_cols and len(active_df_to_display.columns) > 0: # If no standard columns, show first few
                final_preview_cols = active_df_to_display.columns.tolist()[:5] # Show up to 5 if no standard ones match

            if final_preview_cols:
                st.dataframe(active_df_to_display[final_preview_cols])
            else: # Fallback if no columns could be selected (e.g. empty df)
                st.dataframe(active_df_to_display)

            if st.button("Clear Preview / Process Another File", key="clear_preview"):
                st.session_state.active_ris_filename = None
                # Optionally, clear the selected file in selectbox if needed, or just let user pick another
                st.rerun()
        elif st.session_state.selected_project_id and ris_files_in_project and selected_ris_to_view:
             # This case means a file is selected but not yet processed, or processing failed.
             # The "Process" button should be visible above.
             st.caption("Select a file and click 'Process' to view its contents.")


if __name__ == "__main__":
    main()
