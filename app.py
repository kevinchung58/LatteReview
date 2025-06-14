import streamlit as st
import os
import re # For sanitizing project name
from datetime import datetime # For timestamping
import json # For reading project config
from lattereview.utils import data_handler # For RIS parsing
from lattereview.agents import TitleAbstractReviewer, ScoringReviewer, AbstractionReviewer
import pandas as pd
import time # For simulating review progress

PROJECTS_ROOT_DIR = "lattereview_projects"

AGENT_TYPES = {
    "TitleAbstractReviewer": TitleAbstractReviewer,
    "ScoringReviewer": ScoringReviewer,
    "AbstractionReviewer": AbstractionReviewer,
}
AGENT_TYPE_NAMES = list(AGENT_TYPES.keys())

# --- Helper Functions ---
def sanitize_project_name(name):
    name = name.strip(); name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name); name = re.sub(r'\s+', '_', name)
    return name

def create_project_structure(project_name):
    sanitized_name = sanitize_project_name(project_name)
    if not sanitized_name: return False, "Invalid project name."
    project_path = os.path.join(PROJECTS_ROOT_DIR, sanitized_name)
    if os.path.exists(project_path): return False, f"Project '{sanitized_name}' already exists."
    try:
        os.makedirs(project_path); os.makedirs(os.path.join(project_path, "data")); os.makedirs(os.path.join(project_path, "results"))
        ct = datetime.now().isoformat()
        with open(os.path.join(project_path, "project_config.json"), 'w') as f: json.dump({"project_name": project_name, "sanitized_name": sanitized_name, "created_at": ct}, f, indent=2)
        with open(os.path.join(project_path, "README.md"), 'w') as f: f.write(f"# Project: {project_name}\nDir: {sanitized_name}\nCreated: {ct}")
        return True, f"Project '{project_name}' created."
    except OSError as e: return False, f"Error: {e}"

def get_existing_projects():
    if not os.path.exists(PROJECTS_ROOT_DIR): return []
    projects = []
    for item in os.listdir(PROJECTS_ROOT_DIR):
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)):
            dn = item
            try:
                with open(os.path.join(PROJECTS_ROOT_DIR, item, "project_config.json"), 'r') as f: cfg = json.load(f)
                dn = cfg.get("project_name", item)
                projects.append({"id": item, "name": dn})
            except Exception: projects.append({"id": item, "name": item})
    return sorted(projects, key=lambda x: x["name"])

def parse_ris_file(file_path):
    try:
        df = data_handler.RISHandler().load_ris_file_to_dataframe(file_path)
        return df, None
    except Exception as e: return None, f"Error parsing '{os.path.basename(file_path)}': {e}"

# Placeholder for actual workflow execution
def execute_review_workflow_stub(project_workflow, ris_data_df):
    st.session_state.review_log.append("Starting review process (simulation)...")
    st.session_state.review_status_message = "Initializing..."

    num_rounds = len(project_workflow.get("rounds", []))
    total_steps = num_rounds * 3 # Simulate a few steps per round (e.g., init, processing, finalizing)
    if total_steps == 0: total_steps = 1 # Avoid division by zero if no rounds

    current_step = 0
    for i, round_data in enumerate(project_workflow.get("rounds", [])):
        round_name = round_data.get("name", f"Round {i+1}")
        st.session_state.review_log.append(f"Starting {round_name}...")
        st.session_state.review_status_message = f"{round_name}: Initializing agents..."
        current_step +=1
        st.session_state.review_progress = int((current_step / total_steps) * 100)
        time.sleep(0.5) # Simulate work

        num_agents = len(round_data.get("agents", []))
        st.session_state.review_log.append(f"{round_name}: Found {num_agents} agent(s).")
        st.session_state.review_status_message = f"{round_name}: Processing with {num_agents} agent(s)..."
        current_step +=1
        st.session_state.review_progress = int((current_step / total_steps) * 100)
        time.sleep(1) # Simulate work

        # Simulate article processing based on number of articles
        num_articles = len(ris_data_df) if ris_data_df is not None else 0
        st.session_state.review_log.append(f"{round_name}: Simulating review of {num_articles} articles.")
        if num_articles > 0:
            for article_idx in range(num_articles):
                 # Simulate some fine-grained progress if needed, or just one step for all articles
                 if article_idx % (num_articles // 3 +1) == 0 : # Update status a few times during article processing
                    st.session_state.review_status_message = f"{round_name}: Reviewing article {article_idx+1}/{num_articles}..."
                    # This inner loop could also update a sub-progress bar if desired
                    time.sleep(0.05) # Quick sleep for many articles

        st.session_state.review_log.append(f"{round_name} completed.")
        st.session_state.review_status_message = f"{round_name}: Finalizing..."
        current_step +=1
        st.session_state.review_progress = int((current_step / total_steps) * 100)
        time.sleep(0.5) # Simulate work

    st.session_state.review_log.append("Review process (simulation) completed!")
    st.session_state.review_status_message = "Simulation Complete!"
    st.session_state.review_progress = 100
    st.session_state.review_in_progress = False # Re-enable button, or change UI


# --- Main Application UI ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")

    # Initialize session state (condensed)
    for key, default_val in [
        ("api_key_entered", False), ("gemini_api_key", ""), ("selected_project_id", None),
        ("workflow_config", {}), ("ris_dataframes", {}), ("active_ris_filename", None),
        ("selected_project_display_name", None), ("show_create_project_modal", False),
        ("review_in_progress", False), ("review_log", []), ("review_progress", 0),
        ("review_status_message", "")
    ]:
        if key not in st.session_state: st.session_state[key] = default_val

    def get_current_project_workflow():
        # (Unchanged)
        project_id = st.session_state.selected_project_id
        if not project_id: return None
        if project_id not in st.session_state.workflow_config or not st.session_state.workflow_config[project_id].get("rounds"):
            st.session_state.workflow_config[project_id] = {"rounds": [{"name": "Round 1", "agents": [], "filter_config": {"type": "all_previous"}}]}
        workflow = st.session_state.workflow_config[project_id]
        for i, round_data in enumerate(workflow["rounds"]):
            if "filter_config" not in round_data:
                workflow["rounds"][i]["filter_config"] = {"type": "all_previous"} if i == 0 else {"type": "included_previous"}
        return workflow

    def is_workflow_runnable(workflow):
        # (Unchanged)
        if not workflow or not workflow.get("rounds"): return False
        for r_idx, round_data in enumerate(workflow["rounds"]):
            if not round_data.get("agents"): return False
        return True

    # --- Sidebar ---
    # (Unchanged)
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
    # (API Key warning & Welcome markdown - Unchanged)
    if not st.session_state.api_key_entered or not st.session_state.gemini_api_key:
        st.warning("Please enter your Gemini API Key in the sidebar to enable all features.", icon="🔑")
    st.markdown("Welcome to LatteReview! Your AI-powered literature review assistant.")
    st.divider()


    # --- Project Management ---
    # (Unchanged)
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
                    st.session_state.selected_project_id = proj['id']; st.session_state.selected_project_display_name = proj['name']
                    st.session_state.active_ris_filename = None
                    if st.session_state.selected_project_id not in st.session_state.ris_dataframes: st.session_state.ris_dataframes[st.session_state.selected_project_id] = {}
                    get_current_project_workflow(); st.session_state.review_in_progress = False; st.session_state.review_log = []; st.session_state.review_progress = 0
                    st.rerun()
    with col_actions:
        if st.button("➕ Create New Project", use_container_width=True): st.session_state.show_create_project_modal = True
        if st.session_state.selected_project_id:
            st.success(f"Active project: **{st.session_state.selected_project_display_name}** (`{st.session_state.selected_project_id}`)")
            if st.button("✖️ Close Project", use_container_width=True):
                st.session_state.selected_project_id = None; st.session_state.selected_project_display_name = None; st.session_state.active_ris_filename = None
                st.session_state.review_in_progress = False; st.session_state.review_log = []; st.session_state.review_progress = 0
                st.rerun()
    if st.session_state.get("show_create_project_modal", False):
        with st.form("new_project_form"):
            st.subheader("Create New Project"); project_name_input = st.text_input("Project Name")
            if st.form_submit_button("Create Project"):
                if project_name_input:
                    success, message = create_project_structure(project_name_input)
                    if success: st.success(message); st.session_state.show_create_project_modal = False; st.rerun()
                    else: st.error(message)
                else: st.error("Project name cannot be empty.")
    st.divider()

    # --- Data Management ---
    # (Unchanged)
    active_df_to_display = None
    if st.session_state.selected_project_id:
        st.subheader(f"Data Management for: {st.session_state.selected_project_display_name}")
        project_data_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "data")
        with st.expander("Upload New RIS File", expanded=not bool(os.listdir(project_data_path) if os.path.exists(project_data_path) else [])):
            uploaded_file = st.file_uploader("Upload .ris File", type=['ris'], accept_multiple_files=False, key=f"ris_uploader_{st.session_state.selected_project_id}")
            if uploaded_file:
                file_path = os.path.join(project_data_path, uploaded_file.name)
                try:
                    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    st.success(f"File '{uploaded_file.name}' uploaded."); st.session_state.active_ris_filename = None; st.rerun() #Rerun to refresh selectbox
                except Exception as e: st.error(f"Error saving: {e}")
        st.write("##### Process and View Existing RIS File")
        ris_files_in_project = [f for f in os.listdir(project_data_path) if f.endswith(".ris")] if os.path.exists(project_data_path) else []
        if not ris_files_in_project: st.caption("No RIS files. Upload one.")
        else:
            selected_ris_to_view = st.selectbox("Select RIS file:", options=[""] + ris_files_in_project, index=0, key=f"sel_ris_{st.session_state.selected_project_id}", format_func=lambda x: x or "Select...")
            if selected_ris_to_view:
                current_df = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(selected_ris_to_view)
                if current_df is None:
                    if st.button(f"Process '{selected_ris_to_view}'", key=f"proc_{selected_ris_to_view}"):
                        fp = os.path.join(project_data_path, selected_ris_to_view); df, err = parse_ris_file(fp)
                        if df is not None:
                            st.session_state.ris_dataframes.setdefault(st.session_state.selected_project_id, {})[selected_ris_to_view] = df
                            st.session_state.active_ris_filename = selected_ris_to_view; st.success(f"Parsed '{selected_ris_to_view}'."); st.rerun()
                        else:
                            st.error(err or f"Failed to parse."); st.session_state.active_ris_filename = None
                            if selected_ris_to_view in st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}): del st.session_state.ris_dataframes[st.session_state.selected_project_id][selected_ris_to_view]
                else: st.session_state.active_ris_filename = selected_ris_to_view
        if st.session_state.active_ris_filename and st.session_state.selected_project_id:
            active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)
        if active_df_to_display is not None:
            st.markdown(f"#### Preview: `{st.session_state.active_ris_filename}` ({len(active_df_to_display)} articles)")
            cols = ['id','title','TI','primary_title','abstract','AB','year','PY','authors','AU']
            fc = [c for c in cols if c in active_df_to_display.columns] or active_df_to_display.columns.tolist()[:5]
            st.dataframe(active_df_to_display[fc] if fc else active_df_to_display)
            if st.button("Clear Preview", key="clear_prev"): st.session_state.active_ris_filename = None; st.rerun()
        elif st.session_state.selected_project_id and ris_files_in_project and selected_ris_to_view: st.caption("Process file to view.")
        st.divider()

    # --- Workflow Configuration & Execution ---
    workflow_execution_container = st.container()
    with workflow_execution_container:
        if st.session_state.selected_project_id and st.session_state.active_ris_filename and (active_df_to_display is not None):
            st.subheader(f"Workflow for: {st.session_state.selected_project_display_name} (`{st.session_state.active_ris_filename}`)")
            current_workflow = get_current_project_workflow()
            if not current_workflow: st.error("Workflow error."); return

            # Workflow Definition UI (disabled if review in progress)
            with st.expander("Define Workflow Rounds & Agents", expanded=not st.session_state.review_in_progress):
                # (Tabs & Agent Config UI - Unchanged)
                col_add_round, col_remove_round, _ = st.columns([1,1,3])
                with col_add_round:
                    if st.button("➕ Add Round", key="add_r", disabled=st.session_state.review_in_progress):
                        new_round_name = f"Round {len(current_workflow['rounds']) + 1}"
                        current_workflow["rounds"].append({"name": new_round_name, "agents": [], "filter_config": {"type": "included_previous"}})
                        st.rerun()
                with col_remove_round:
                    if len(current_workflow["rounds"]) > 1:
                        if st.button("➖ Remove Last Round", key="rem_r", type="secondary", disabled=st.session_state.review_in_progress):
                            current_workflow["rounds"].pop(); st.rerun()
                tab_titles = [r.get('name', f'R {idx+1}') for idx, r in enumerate(current_workflow["rounds"])]
                tabs = st.tabs(tab_titles)
                for i, tab_content in enumerate(tabs):
                    with tab_content:
                        rd = current_workflow['rounds'][i]
                        st.markdown(f"**{rd.get('name', f'R {i+1}')} Settings**")
                        new_r_name = st.text_input("Name", value=rd.get('name',''), key=f"rn_{i}_{st.session_state.selected_project_id}", disabled=st.session_state.review_in_progress)
                        if new_r_name != rd.get('name',''): rd['name'] = new_r_name; st.rerun()
                        if i > 0: # Inter-round filtering
                            st.markdown("Article Source:")
                            prev_scorer = any(a.get("type")=="ScoringReviewer" for a in current_workflow["rounds"][i-1].get("agents",[]))
                            fo = {"all_previous":"All prev","included_previous":"Incl prev","excluded_previous":"Excl prev","disagreement_previous":"Disagree prev"} # Corrected keys
                            if prev_scorer: fo["score_above_threshold"] = "Score > X prev" # Corrected key
                            cfg = rd.get("filter_config",{})
                            ct = cfg.get("type","included_previous") # Corrected default
                            if ct=="score_above_threshold" and not prev_scorer: ct="included_previous"; cfg={"type":ct} # Corrected key and default
                            sfk = st.selectbox("Source:",options=list(fo.keys()),format_func=lambda x:fo[x],index=list(fo.keys()).index(ct),key=f"ftr_{i}", disabled=st.session_state.review_in_progress)
                            cfg["type"]=sfk
                            if sfk=="score_above_threshold": cfg["threshold"]=st.number_input("Score Thresh",min_value=0.0,max_value=5.0,value=cfg.get("threshold",3.0),step=0.1,key=f"fsc_{i}", disabled=st.session_state.review_in_progress) # Corrected key
                            elif "threshold" in cfg: del cfg["threshold"] # Corrected key
                            rd["filter_config"] = cfg
                        st.markdown("---"); st.write(f"**Agents:** {len(rd.get('agents',[]))}")
                        if st.button(f"➕ Add Agent", key=f"aa_{i}", disabled=st.session_state.review_in_progress):
                            rd.setdefault("agents",[]).append({"name":f"Agent {len(rd.get('agents',[]))+1}","type":AGENT_TYPE_NAMES[0],"backstory":"","inclusion_criteria":"","exclusion_criteria":""}); st.rerun() # Corrected key for criteria
                        for agent_idx, acfg in enumerate(rd.get("agents",[])):
                            with st.expander(f"{acfg.get('name')} ({acfg.get('type')})", expanded=True):
                                acfg["name"]=st.text_input("Name",value=acfg["name"],key=f"an_{i}_{agent_idx}", disabled=st.session_state.review_in_progress)
                                acfg["type"]=st.selectbox("Type",options=AGENT_TYPE_NAMES,index=AGENT_TYPE_NAMES.index(acfg["type"]) if acfg["type"] in AGENT_TYPE_NAMES else 0,key=f"at_{i}_{agent_idx}", disabled=st.session_state.review_in_progress)
                                acfg["backstory"]=st.text_area("Backstory",value=acfg["backstory"],key=f"ab_{i}_{agent_idx}",h=75, disabled=st.session_state.review_in_progress)
                                acfg["inclusion_criteria"]=st.text_area("Inclusion",value=acfg.get("inclusion_criteria",""),key=f"aic_{i}_{agent_idx}",h=75, disabled=st.session_state.review_in_progress) # Corrected key
                                acfg["exclusion_criteria"]=st.text_area("Exclusion",value=acfg.get("exclusion_criteria",""),key=f"aec_{i}_{agent_idx}",h=75, disabled=st.session_state.review_in_progress) # Corrected key
                                if st.button(f"➖ Remove",key=f"ra_{i}_{agent_idx}",type="secondary", disabled=st.session_state.review_in_progress): rd["agents"].pop(agent_idx);st.rerun()
                                st.markdown("---")

            st.divider()
            ready_to_run = (st.session_state.api_key_entered and st.session_state.gemini_api_key and
                            st.session_state.selected_project_id and active_df_to_display is not None and
                            len(active_df_to_display) > 0 and is_workflow_runnable(current_workflow))

            if ready_to_run:
                st.markdown("### Review Execution")
                if st.button("🚀 Start Review", type="primary", use_container_width=True, disabled=st.session_state.review_in_progress):
                    st.session_state.review_in_progress = True
                    st.session_state.review_log = []
                    st.session_state.review_progress = 0
                    st.session_state.review_status_message = "Initiating review simulation..."
                    # Call the stub function
                    execute_review_workflow_stub(current_workflow, active_df_to_display)
                    # No rerun here, execute_review_workflow_stub will manage state for completion
            elif st.session_state.selected_project_id and active_df_to_display is not None:
                if not (st.session_state.api_key_entered and st.session_state.gemini_api_key): st.warning("API Key not set.")
                elif not is_workflow_runnable(current_workflow): st.warning("Workflow not runnable: ensure each round has at least one agent.")

            # Progress Display Area
            if st.session_state.review_in_progress or st.session_state.review_progress == 100 : # Show if in progress or just completed
                st.markdown("#### Review Progress")
                st.progress(st.session_state.review_progress / 100)
                st.caption(st.session_state.review_status_message)

                # Use st.status for cleaner log display during active review
                if st.session_state.review_in_progress:
                    with st.status("Review Log", expanded=True):
                        for log_entry in st.session_state.review_log:
                            st.write(log_entry)
                elif st.session_state.review_log : # if review is finished but log exists
                     with st.expander("Show Full Review Log", expanded=False):
                        st.code("\n".join(st.session_state.review_log), language="text")


                # Placeholder for cost tracking (TODO 4.1 UI)
                st.caption("Estimated/Actual Cost: $0.00 (simulation)")

                if not st.session_state.review_in_progress and st.session_state.review_progress == 100:
                    st.success("Review Simulation Completed!")
                    if st.button("Reset Review State"): # Allow user to reset to run again or modify
                        st.session_state.review_in_progress = False
                        st.session_state.review_log = []
                        st.session_state.review_progress = 0
                        st.session_state.review_status_message = ""
                        st.rerun()


        elif st.session_state.selected_project_id:
            st.info("Please select and process a RIS file to configure workflow and start review.")

if __name__ == "__main__":
    main()
