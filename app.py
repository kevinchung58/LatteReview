import streamlit as st
import os
import re # For sanitizing project name
from datetime import datetime # For timestamping
import json # For reading project config
from lattereview.utils import data_handler # For RIS parsing
from lattereview.agents import TitleAbstractReviewer, ScoringReviewer, AbstractionReviewer
import pandas as pd

PROJECTS_ROOT_DIR = "lattereview_projects"

# Agent type definitions
AGENT_TYPES = {
    "TitleAbstractReviewer": TitleAbstractReviewer,
    "ScoringReviewer": ScoringReviewer,
    "AbstractionReviewer": AbstractionReviewer,
}
AGENT_TYPE_NAMES = list(AGENT_TYPES.keys())

# --- Helper Functions (sanitize_project_name, create_project_structure, get_existing_projects, parse_ris_file) ---
# Assume these are present and correct from previous steps.
def sanitize_project_name(name):
    name = name.strip()
    name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name

def create_project_structure(project_name):
    sanitized_name = sanitize_project_name(project_name)
    if not sanitized_name: return False, "Invalid project name after sanitization."
    project_path = os.path.join(PROJECTS_ROOT_DIR, sanitized_name)
    if os.path.exists(project_path): return False, f"Project '{sanitized_name}' already exists."
    try:
        os.makedirs(project_path); os.makedirs(os.path.join(project_path, "data")); os.makedirs(os.path.join(project_path, "results"))
        current_time_iso = datetime.now().isoformat()
        with open(os.path.join(project_path, "project_config.json"), 'w') as f: json.dump({"project_name": project_name, "sanitized_name": sanitized_name, "created_at": current_time_iso}, f, indent=2)
        with open(os.path.join(project_path, "README.md"), 'w') as f: f.write(f"# Project: {project_name}\n\nDirectory: {sanitized_name}\nCreated: {current_time_iso}")
        return True, f"Project '{project_name}' created."
    except OSError as e: return False, f"Error creating project directory: {e}"

def get_existing_projects():
    if not os.path.exists(PROJECTS_ROOT_DIR): return []
    projects = []
    for item in os.listdir(PROJECTS_ROOT_DIR):
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)):
            display_name = item
            try:
                with open(os.path.join(PROJECTS_ROOT_DIR, item, "project_config.json"), 'r') as f_cfg: cfg = json.load(f_cfg)
                display_name = cfg.get("project_name", item)
                projects.append({"id": item, "name": display_name})
            except Exception: projects.append({"id": item, "name": item}) # Fallback
    return sorted(projects, key=lambda x: x["name"])

def parse_ris_file(file_path):
    try:
        df = data_handler.RISHandler().load_ris_file_to_dataframe(file_path)
        return df, None
    except Exception as e: return None, f"Error parsing RIS file '{os.path.basename(file_path)}': {e}"

# --- Main Application ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")

    # Initialize session state
    if "api_key_entered" not in st.session_state: st.session_state.api_key_entered = False
    if "gemini_api_key" not in st.session_state: st.session_state.gemini_api_key = ""
    # ... other initializations ...
    if "selected_project_id" not in st.session_state: st.session_state.selected_project_id = None
    if "workflow_config" not in st.session_state: st.session_state.workflow_config = {}
    if "ris_dataframes" not in st.session_state: st.session_state.ris_dataframes = {}
    if "active_ris_filename" not in st.session_state: st.session_state.active_ris_filename = None
    if "selected_project_display_name" not in st.session_state: st.session_state.selected_project_display_name = None
    if "show_create_project_modal" not in st.session_state: st.session_state.show_create_project_modal = False


    def get_current_project_workflow():
        project_id = st.session_state.selected_project_id
        if not project_id: return None
        if project_id not in st.session_state.workflow_config or not st.session_state.workflow_config[project_id].get("rounds"):
            st.session_state.workflow_config[project_id] = {"rounds": [{"name": "Round 1", "agents": [], "filter_config": {"type": "all_previous"}}]} # Default filter for first round

        # Ensure all rounds have a filter_config, especially for rounds > 0
        workflow = st.session_state.workflow_config[project_id]
        for i, round_data in enumerate(workflow["rounds"]):
            if "filter_config" not in round_data:
                workflow["rounds"][i]["filter_config"] = {"type": "all_previous"} if i == 0 else {"type": "included_previous"} # Default for subsequent rounds
        return workflow

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

    # --- Main Page ---
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
                st.session_state.selected_project_id = None; st.session_state.selected_project_display_name = None; st.session_state.active_ris_filename = None
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
        with st.expander("Upload New RIS File", expanded=not bool(os.listdir(project_data_path) if os.path.exists(project_data_path) else [])):
            uploaded_file = st.file_uploader("Upload .ris File", type=['ris'], accept_multiple_files=False, key=f"ris_uploader_{st.session_state.selected_project_id}")
            if uploaded_file is not None:
                file_path = os.path.join(project_data_path, uploaded_file.name)
                try:
                    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    st.success(f"File '{uploaded_file.name}' uploaded successfully.")
                    st.session_state.active_ris_filename = None
                except Exception as e: st.error(f"Error saving uploaded file: {e}")

        st.write("##### Process and View Existing RIS File")
        ris_files_in_project = [f for f in os.listdir(project_data_path) if f.endswith(".ris")] if os.path.exists(project_data_path) else []
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
            else: st.dataframe(active_df_to_display)
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

            col_add_round, col_remove_round, _ = st.columns([1,1,2])
            with col_add_round:
                if st.button("➕ Add Review Round", key="add_round"):
                    new_round_name = f"Round {len(current_workflow['rounds']) + 1}"
                    default_filter = {"type": "included_previous"} # Default for new subsequent rounds
                    current_workflow["rounds"].append({"name": new_round_name, "agents": [], "filter_config": default_filter})
                    st.rerun()
            with col_remove_round:
                if len(current_workflow["rounds"]) > 1:
                     if st.button("➖ Remove Last Round", key="remove_round", type="secondary"):
                        current_workflow["rounds"].pop(); st.rerun()

            tab_titles = [r.get('name', f'Round {i+1}') for i, r in enumerate(current_workflow["rounds"])]
            tabs = st.tabs(tab_titles)

            for i, tab_content in enumerate(tabs):
                with tab_content:
                    round_data = current_workflow['rounds'][i] # Reference for easier access
                    st.markdown(f"#### Settings for: **{round_data.get('name', f'Round {i+1}')}**")

                    new_round_name = st.text_input("Round Name", value=round_data.get('name', f'Round {i+1}'), key=f"round_name_{i}_{st.session_state.selected_project_id}")
                    if new_round_name != round_data.get('name', f'Round {i+1}'):
                        round_data['name'] = new_round_name; st.rerun()

                    # TODO 3.3: 設定回合間的過濾邏輯
                    if i > 0: # Filtering logic only for rounds > 0
                        st.markdown("##### Article Source & Filtering for this Round")

                        # Check if previous round had a scoring reviewer
                        previous_round_has_scorer = False
                        if i > 0: # This check is redundant with the outer if, but good for clarity
                            for agent_cfg in current_workflow["rounds"][i-1].get("agents", []):
                                if agent_cfg.get("type") == "ScoringReviewer":
                                    previous_round_has_scorer = True
                                    break

                        filter_options = {
                            "all_previous": "All articles from previous round", # This is not in TODO, but can be useful.
                            "included_previous": "Only 'Included' articles from previous round",
                            "excluded_previous": "Only 'Excluded' articles from previous round",
                            "disagreement_previous": "Articles with disagreement from previous round",
                        }
                        if previous_round_has_scorer:
                            filter_options["score_above_threshold"] = "Articles with average score above X from previous round"

                        # Ensure current_filter_type is valid, fallback if not
                        current_filter_type = round_data.get("filter_config", {}).get("type", "included_previous") # Default for round > 0
                        if current_filter_type not in filter_options:
                             current_filter_type = "included_previous" # Fallback if previous option (e.g. scorer) removed
                             round_data["filter_config"] = {"type": current_filter_type}


                        selected_filter_key = st.selectbox(
                            "Source of Articles:",
                            options=list(filter_options.keys()),
                            format_func=lambda x: filter_options[x],
                            index=list(filter_options.keys()).index(current_filter_type),
                            key=f"filter_type_round_{i}_{st.session_state.selected_project_id}"
                        )

                        # Update filter type in session state
                        if round_data.get("filter_config",{}).get("type") != selected_filter_key:
                            round_data["filter_config"]["type"] = selected_filter_key
                            # No rerun, allow configuring threshold if needed before rerun

                        if selected_filter_key == "score_above_threshold":
                            current_threshold = round_data.get("filter_config", {}).get("threshold", 3.0) # Default threshold
                            score_threshold = st.number_input(
                                "Score Threshold (e.g., 0.0-5.0 or 0-100 depending on scorer's scale)",
                                value=current_threshold, step=0.1,
                                key=f"filter_score_round_{i}_{st.session_state.selected_project_id}"
                            )
                            if round_data.get("filter_config",{}).get("threshold") != score_threshold:
                                round_data["filter_config"]["threshold"] = score_threshold
                        # Clean up threshold if filter type changes away from score-based
                        elif "threshold" in round_data.get("filter_config", {}):
                            del round_data["filter_config"]["threshold"]

                    st.markdown("---") # Separator before agent configurations
                    st.write(f"**Configured Agents in this Round:** {len(round_data.get('agents', []))}")
                    if st.button(f"➕ Add Agent to {round_data['name']}", key=f"add_agent_round_{i}_{st.session_state.selected_project_id}"):
                        new_agent_name = f"Agent {len(round_data.get('agents', [])) + 1}"
                        round_data.setdefault("agents", []).append({
                            "name": new_agent_name, "type": AGENT_TYPE_NAMES[0],
                            "backstory": "A diligent AI assistant.",
                            "inclusion_criteria": "- Criterion 1", "exclusion_criteria": "- Criterion A"
                        })
                        st.rerun()

                    for agent_idx, agent_config in enumerate(round_data.get("agents", [])):
                        with st.expander(f"Configure: {agent_config.get('name', f'Agent {agent_idx+1}')} ({agent_config.get('type', 'N/A')})", expanded=True):
                            # (Agent config UI - unchanged from previous step)
                            agent_name = st.text_input("Agent Name", value=agent_config["name"], key=f"agent_name_{i}_{agent_idx}_{st.session_state.selected_project_id}")
                            agent_type = st.selectbox("Agent Type", options=AGENT_TYPE_NAMES, index=AGENT_TYPE_NAMES.index(agent_config["type"]) if agent_config["type"] in AGENT_TYPE_NAMES else 0, key=f"agent_type_{i}_{agent_idx}_{st.session_state.selected_project_id}")
                            agent_backstory = st.text_area("Agent Backstory/Persona", value=agent_config["backstory"], key=f"agent_backstory_{i}_{agent_idx}_{st.session_state.selected_project_id}", height=100)
                            agent_inclusion = st.text_area("Inclusion Criteria (one per line)", value=agent_config["inclusion_criteria"], key=f"agent_inclusion_{i}_{agent_idx}_{st.session_state.selected_project_id}", height=100)
                            agent_exclusion = st.text_area("Exclusion Criteria (one per line)", value=agent_config["exclusion_criteria"], key=f"agent_exclusion_{i}_{agent_idx}_{st.session_state.selected_project_id}", height=100)

                            agent_config["name"] = agent_name; agent_config["type"] = agent_type
                            agent_config["backstory"] = agent_backstory; agent_config["inclusion_criteria"] = agent_inclusion
                            agent_config["exclusion_criteria"] = agent_exclusion

                            if st.button(f"➖ Remove {agent_name}", key=f"remove_agent_{i}_{agent_idx}_{st.session_state.selected_project_id}", type="secondary"):
                                round_data["agents"].pop(agent_idx); st.rerun()
                            st.markdown("---")
        elif st.session_state.selected_project_id :
            st.info("Please select and process a RIS file above to configure the workflow.")

if __name__ == "__main__":
    main()
