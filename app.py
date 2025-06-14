import streamlit as st
import os
import re # For sanitizing project name
from datetime import datetime # For timestamping
import json # For reading project config
from lattereview.utils import data_handler # For RIS parsing
# Ensure all agent types are available for selection
from lattereview.agents import TitleAbstractReviewer, ScoringReviewer, AbstractionReviewer

import pandas as pd # For DataFrame

PROJECTS_ROOT_DIR = "lattereview_projects"

# --- Helper Functions (sanitize_project_name, create_project_structure, get_existing_projects, parse_ris_file) ---
def sanitize_project_name(name):
    name = name.strip()
    name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name

def create_project_structure(project_name):
    sanitized_name = sanitize_project_name(project_name)
    if not sanitized_name:
        return False, "Invalid project name after sanitization. Please use allowed characters."
    project_path = os.path.join(PROJECTS_ROOT_DIR, sanitized_name)
    if os.path.exists(project_path):
        return False, f"Project '{sanitized_name}' already exists."
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
        return True, f"Project '{project_name}' (directory: '{sanitized_name}') created successfully!"
    except OSError as e:
        return False, f"Error creating project directory: {e}"

def get_existing_projects():
    if not os.path.exists(PROJECTS_ROOT_DIR): return []
    projects = []
    for item in os.listdir(PROJECTS_ROOT_DIR):
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)):
            display_name = item
            try:
                config_path = os.path.join(PROJECTS_ROOT_DIR, item, "project_config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f_cfg: cfg = json.load(f_cfg)
                    display_name = cfg.get("project_name", item)
                projects.append({"id": item, "name": display_name})
            except Exception: projects.append({"id": item, "name": item})
    return sorted(projects, key=lambda x: x["name"])

def parse_ris_file(file_path):
    try:
        ris_handler = data_handler.RISHandler()
        df = ris_handler.load_ris_file_to_dataframe(file_path)
        return df, None
    except Exception as e: return None, f"Error parsing RIS file '{os.path.basename(file_path)}': {e}"

# --- Main Application ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")

    # Initialize session state
    if "api_key_entered" not in st.session_state: st.session_state.api_key_entered = False
    if "gemini_api_key" not in st.session_state: st.session_state.gemini_api_key = ""
    if "show_create_project_modal" not in st.session_state: st.session_state.show_create_project_modal = False
    if "selected_project_id" not in st.session_state: st.session_state.selected_project_id = None
    if "selected_project_display_name" not in st.session_state: st.session_state.selected_project_display_name = None
    if "ris_dataframes" not in st.session_state: st.session_state.ris_dataframes = {}
    if "active_ris_filename" not in st.session_state: st.session_state.active_ris_filename = None
    if "workflow_config" not in st.session_state: st.session_state.workflow_config = {}

    AGENT_TYPES = {
        "TitleAbstractReviewer": TitleAbstractReviewer,
        "ScoringReviewer": ScoringReviewer,
        "AbstractionReviewer": AbstractionReviewer,
        # "CustomReviewer": CustomReviewer, # If you have a base class for custom
    }
    AGENT_TYPE_NAMES = list(AGENT_TYPES.keys())


    def get_current_project_workflow():
        project_id = st.session_state.selected_project_id
        if not project_id: return None
        if project_id not in st.session_state.workflow_config or not st.session_state.workflow_config[project_id].get("rounds"):
            st.session_state.workflow_config[project_id] = {"rounds": [{"name": "Round 1", "agents": []}]}
        return st.session_state.workflow_config[project_id]

    # --- Sidebar ---
    # (Sidebar code unchanged)
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

    # --- Main Page Content ---
    st.title("LatteReview 🤖☕")
    # (API Key warning and Welcome markdown unchanged)
    if not st.session_state.api_key_entered or not st.session_state.gemini_api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to enable all features.", icon="🔑")
    st.markdown("Welcome to LatteReview! Your AI-powered literature review assistant.")
    st.divider()

    # --- Project Management ---
    # (Project management code unchanged)
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
                    st.session_state.active_ris_filename = None
                    if st.session_state.selected_project_id not in st.session_state.ris_dataframes:
                        st.session_state.ris_dataframes[st.session_state.selected_project_id] = {}
                    get_current_project_workflow()
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
                    success, message = create_project_structure(project_name_input)
                    if success: st.success(message); st.session_state.show_create_project_modal = False; st.rerun()
                    else: st.error(message)
                else: st.error("Project name cannot be empty.")
    st.divider()

    # --- Data Management ---
    # (RIS data management code unchanged)
    active_df_to_display = None
    if st.session_state.selected_project_id:
        st.subheader(f"Data Management for: {st.session_state.selected_project_display_name}")
        project_data_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "data")
        with st.expander("Upload New RIS File", expanded=not bool(get_existing_projects())):
            uploaded_file = st.file_uploader("Upload .ris File", type=['ris'], accept_multiple_files=False, key=f"ris_uploader_{st.session_state.selected_project_id}")
            if uploaded_file is not None:
                file_path = os.path.join(project_data_path, uploaded_file.name)
                try:
                    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    st.success(f"File '{uploaded_file.name}' uploaded successfully.")
                    st.session_state.active_ris_filename = None
                except Exception as e: st.error(f"Error saving uploaded file: {e}")

        st.write("##### Process and View Existing RIS File")
        ris_files_in_project = [f for f in os.listdir(project_data_path) if f.endswith(".ris")]
        if not ris_files_in_project: st.caption("No RIS files found. Upload one above.")
        else:
            selected_ris_to_view = st.selectbox("Select a RIS file to process/view:", options=[""] + ris_files_in_project, index=0, key=f"select_ris_{st.session_state.selected_project_id}", format_func=lambda x: "Select a file..." if x == "" else x)
            if selected_ris_to_view:
                current_df = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(selected_ris_to_view)
                if current_df is None:
                    if st.button(f"Process '{selected_ris_to_view}'", key=f"process_{selected_ris_to_view}"):
                        full_file_path = os.path.join(project_data_path, selected_ris_to_view)
                        df, error_msg = parse_ris_file(full_file_path)
                        if df is not None:
                            st.session_state.ris_dataframes[st.session_state.selected_project_id][selected_ris_to_view] = df
                            st.session_state.active_ris_filename = selected_ris_to_view
                            st.success(f"Successfully parsed '{selected_ris_to_view}'.")
                            st.rerun()
                        else:
                            st.error(error_msg or f"Failed to parse '{selected_ris_to_view}'.")
                            st.session_state.active_ris_filename = None
                            if selected_ris_to_view in st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}):
                                del st.session_state.ris_dataframes[st.session_state.selected_project_id][selected_ris_to_view]
                else: st.session_state.active_ris_filename = selected_ris_to_view

        if st.session_state.active_ris_filename and st.session_state.selected_project_id:
            active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)

        if active_df_to_display is not None:
            st.markdown(f"#### Preview for: `{st.session_state.active_ris_filename}`")
            # (DataFrame display logic unchanged)
            st.info(f"Total articles imported: **{len(active_df_to_display)}**")
            preview_cols_options = ['id', 'title', 'TI', 'primary_title', 'abstract', 'AB', 'year', 'PY', 'authors', 'AU']
            final_preview_cols = [col for col in preview_cols_options if col in active_df_to_display.columns]
            if not final_preview_cols and len(active_df_to_display.columns) > 0: final_preview_cols = active_df_to_display.columns.tolist()[:5]
            if final_preview_cols: st.dataframe(active_df_to_display[final_preview_cols])
            else: st.dataframe(active_df_to_display) # Show all if no specific columns found
            if st.button("Clear Preview / Process Another File", key="clear_preview"):
                st.session_state.active_ris_filename = None; st.rerun()
        elif st.session_state.selected_project_id and ris_files_in_project and selected_ris_to_view :
             st.caption("Select a file and click 'Process' to view its contents.")
        st.divider()

        # --- Workflow Configuration Section (TODO 3.0) ---
        if st.session_state.selected_project_id and st.session_state.active_ris_filename and (active_df_to_display is not None):
            st.subheader(f"Workflow Configuration for: {st.session_state.selected_project_display_name} (using `{st.session_state.active_ris_filename}`)")

            current_workflow = get_current_project_workflow()
            if not current_workflow: st.error("Workflow not initialized."); return

            # TODO 3.1: Multi-Round Interface (Done)
            col_add_round, col_remove_round, _ = st.columns([1,1,2]) # Adjust ratio for spacing
            with col_add_round:
                if st.button("➕ Add Review Round", key="add_round"):
                    current_workflow["rounds"].append({"name": f"Round {len(current_workflow['rounds']) + 1}", "agents": []})
                    st.rerun()
            with col_remove_round:
                if len(current_workflow["rounds"]) > 1:
                     if st.button("➖ Remove Last Round", key="remove_round", type="secondary"):
                        current_workflow["rounds"].pop(); st.rerun()
                else: st.caption(" ") # Keep space consistent

            tab_titles = [r.get('name', f'Round {i+1}') for i, r in enumerate(current_workflow["rounds"])]
            if not tab_titles: # Should be caught by get_current_project_workflow initialization
                st.session_state.workflow_config[st.session_state.selected_project_id]["rounds"] = [{"name": "Round 1", "agents": []}]
                current_workflow = get_current_project_workflow()
                tab_titles = [r.get('name', f'Round {i+1}') for i, r in enumerate(current_workflow["rounds"])]

            tabs = st.tabs(tab_titles)

            for i, tab_content in enumerate(tabs):
                with tab_content:
                    st.markdown(f"#### Settings for: **{current_workflow['rounds'][i].get('name', f'Round {i+1}')}**")

                    # Allow renaming the round
                    new_round_name = st.text_input("Round Name", value=current_workflow['rounds'][i].get('name', f'Round {i+1}'), key=f"round_name_{i}_{st.session_state.selected_project_id}")
                    if new_round_name != current_workflow['rounds'][i].get('name', f'Round {i+1}'):
                        current_workflow['rounds'][i]['name'] = new_round_name
                        # Consider a "Save Round Name" button or auto-save on blur if possible, for now direct update
                        st.rerun() # Rerun to update tab titles immediately

                    st.markdown("---")
                    # TODO 3.2: 設計 Agent 設定器
                    # - 在每個回合的 Tab 內，允許使用者 "新增 Agent"。
                    # - 每個 Agent 都是一個卡片或 st.expander

                    num_agents_in_round = len(current_workflow["rounds"][i]["agents"])
                    st.write(f"**Configured Agents in this Round: {num_agents_in_round}**")

                    if st.button(f"➕ Add Agent to {current_workflow['rounds'][i]['name']}", key=f"add_agent_round_{i}"):
                        # Add a new default agent dictionary to this round's agent list
                        new_agent_default_name = f"Agent {len(current_workflow['rounds'][i]['agents']) + 1}"
                        current_workflow["rounds"][i]["agents"].append({
                            "name": new_agent_default_name,
                            "type": AGENT_TYPE_NAMES[0], # Default to first agent type
                            "backstory": "A diligent AI assistant specializing in initial review of titles and abstracts.", # More specific default
                            "inclusion_criteria": "- Relevant to [Specific Topic]\n- Published after [Year]\n- Study type: [e.g., RCT, Review, Case Study]", # Example placeholder
                            "exclusion_criteria": "- Not in English\n- Focus on [Irrelevant Subtopic]\n- Lacks empirical data" # Example placeholder
                        })
                        st.rerun()

                    # Display existing agents for this round
                    for agent_idx, agent_config in enumerate(current_workflow["rounds"][i]["agents"]):
                        with st.expander(f"Configure: {agent_config.get('name', f'Agent {agent_idx+1}')} ({agent_config.get('type', 'N/A')})", expanded=True):
                            agent_name = st.text_input("Agent Name", value=agent_config["name"], key=f"agent_name_{i}_{agent_idx}_{st.session_state.selected_project_id}")
                            agent_type = st.selectbox("Agent Type", options=AGENT_TYPE_NAMES, index=AGENT_TYPE_NAMES.index(agent_config["type"]) if agent_config["type"] in AGENT_TYPE_NAMES else 0, key=f"agent_type_{i}_{agent_idx}_{st.session_state.selected_project_id}")
                            agent_backstory = st.text_area("Agent Backstory/Persona", value=agent_config["backstory"], key=f"agent_backstory_{i}_{agent_idx}_{st.session_state.selected_project_id}", height=100, help="Describe the agent's expertise and perspective.")
                            agent_inclusion = st.text_area("Inclusion Criteria (one per line)", value=agent_config["inclusion_criteria"], key=f"agent_inclusion_{i}_{agent_idx}_{st.session_state.selected_project_id}", height=100, help="Specific criteria for including a paper.")
                            agent_exclusion = st.text_area("Exclusion Criteria (one per line)", value=agent_config["exclusion_criteria"], key=f"agent_exclusion_{i}_{agent_idx}_{st.session_state.selected_project_id}", height=100, help="Specific criteria for excluding a paper.")

                            # Update session state directly (basic implementation)
                            current_workflow["rounds"][i]["agents"][agent_idx]["name"] = agent_name
                            current_workflow["rounds"][i]["agents"][agent_idx]["type"] = agent_type
                            current_workflow["rounds"][i]["agents"][agent_idx]["backstory"] = agent_backstory
                            current_workflow["rounds"][i]["agents"][agent_idx]["inclusion_criteria"] = agent_inclusion
                            current_workflow["rounds"][i]["agents"][agent_idx]["exclusion_criteria"] = agent_exclusion

                            if st.button(f"➖ Remove {agent_name}", key=f"remove_agent_{i}_{agent_idx}_{st.session_state.selected_project_id}", type="secondary"):
                                current_workflow["rounds"][i]["agents"].pop(agent_idx)
                                st.rerun()
                            st.markdown("---")


                    # Placeholder for TODO 3.3 (Filtering)
                    if i > 0: # Filtering logic only for rounds > 0
                        st.markdown("##### Inter-Round Article Filtering")
                        st.info(f"Filtering logic for articles entering {current_workflow['rounds'][i]['name']} (TODO 3.3) will appear here.")


        elif st.session_state.selected_project_id :
            st.info("Please select and process a RIS file above to configure the workflow.")

if __name__ == "__main__":
    main()
