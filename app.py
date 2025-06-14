import streamlit as st
import os
import re # For sanitizing project name
from datetime import datetime # For timestamping
import json # For reading project config
from lattereview.utils import data_handler # For RIS parsing
from lattereview.agents import TitleAbstractReviewer, ScoringReviewer, AbstractionReviewer
import pandas as pd
import time # For simulating review progress
import random # For simulating results
from collections import Counter # For concept aggregation
from wordcloud import WordCloud
import matplotlib.pyplot as plt

PROJECTS_ROOT_DIR = "lattereview_projects"
AGENT_TYPES = {"TitleAbstractReviewer": TitleAbstractReviewer, "ScoringReviewer": ScoringReviewer, "AbstractionReviewer": AbstractionReviewer}
AGENT_TYPE_NAMES = list(AGENT_TYPES.keys())

# --- Helper Functions ---
# (Assume these are present and correct from previous versions)
def sanitize_project_name(name):
    name = name.strip(); name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name); name = re.sub(r'\s+', '_', name)
    return name

def create_project_structure(project_name):
    sanitized_name = sanitize_project_name(project_name)
    if not sanitized_name: return False, "Invalid project name."
    project_path = os.path.join(PROJECTS_ROOT_DIR, sanitized_name)
    if os.path.exists(project_path): return False, f"Project '{sanitized_name}' already exists."
    try:
        os.makedirs(project_path)
        os.makedirs(os.path.join(project_path, "data"))
        os.makedirs(os.path.join(project_path, "results"))
        os.makedirs(os.path.join(project_path, "rag_context")) # For TODO 5.3
        ct = datetime.now().isoformat()
        with open(os.path.join(project_path, "project_config.json"), 'w') as f:
            json.dump({"project_name": project_name, "sanitized_name": sanitized_name, "created_at": ct, "rag_files": []}, f, indent=2)
        return True, f"Project '{project_name}' created."
    except OSError as e: return False, f"Error: {e}"

def get_existing_projects(): # Unchanged
    if not os.path.exists(PROJECTS_ROOT_DIR): return []
    projects = []; # ... (implementation from previous step)
    for item in os.listdir(PROJECTS_ROOT_DIR):
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)):
            dn = item
            try:
                with open(os.path.join(PROJECTS_ROOT_DIR, item, "project_config.json"), 'r') as f: cfg = json.load(f)
                dn = cfg.get("project_name", item)
                projects.append({"id": item, "name": dn, "rag_files": cfg.get("rag_files", [])}) # Load RAG files list
            except Exception: projects.append({"id": item, "name": item, "rag_files": []}) # Fallback
    return sorted(projects, key=lambda x: x["name"])


def update_project_rag_files(project_id, rag_file_names):
    config_path = os.path.join(PROJECTS_ROOT_DIR, project_id, "project_config.json")
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        config["rag_files"] = rag_file_names
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error updating project config with RAG files: {e}")
        return False


def parse_ris_file(file_path): # Unchanged
    try: # ... (implementation from previous step)
        df = data_handler.RISHandler().load_ris_file_to_dataframe(file_path)
        if 'title' not in df.columns and ('TI' in df.columns or 'primary_title' in df.columns):
            df = df.rename(columns={'TI': 'title', 'primary_title': 'title'}, errors='ignore')
        if 'id' not in df.columns:
            for id_col in ['ID', 'AN', 'UT']:
                if id_col in df.columns: df = df.rename(columns={id_col: 'id'}, errors='ignore'); break
            if 'id' not in df.columns: df['id'] = [f"Art{i}" for i in range(len(df))]
        if 'abstract' not in df.columns and 'AB' in df.columns: df = df.rename(columns={'AB': 'abstract'}, errors='ignore')
        return df, None
    except Exception as e: return None, f"Error parsing '{os.path.basename(file_path)}': {e}"


def generate_simulated_results(ris_data_df, project_workflow, rag_files): # MODIFIED for RAG
    results_list = [] # ... (rest of function largely unchanged but uses rag_files)
    if ris_data_df is None or ris_data_df.empty or 'id' not in ris_data_df.columns: return pd.DataFrame()
    has_scorer_in_workflow = any(a.get("type") == "ScoringReviewer" for r in project_workflow.get("rounds", []) for a in r.get("agents", []))

    for index, row in ris_data_df.iterrows():
        article_id = row['id']; title = row.get('title', f"Unknown Title for {article_id}"); abstract = row.get('abstract', "N/A")
        detailed_log_entries = []

        # Simulate RAG context usage if files are present
        rag_context_log = ""
        if rag_files:
            chosen_rag_file = random.choice(rag_files)
            simulated_rag_snippet = f"Simulated snippet from '{chosen_rag_file}' related to '{title[:20]}...'"
            rag_context_log = f"RAG CONTEXT: Using background from '{chosen_rag_file}'. Snippet: '{simulated_rag_snippet}'. Prompt enhanced."
            detailed_log_entries.append(rag_context_log)

        # Simulate initial rounds & debate (unchanged logic, just prepends RAG log if any)
        # ... (debate simulation logic as before) ...
        # For brevity, the debate simulation part is assumed to be here.
        # It would append its own logs to detailed_log_entries. Example:
        detailed_log_entries.append(f"**Round 1 - Agent A**: Decided 'Included'. Justification: lorem ipsum.")
        if rag_context_log: # Show RAG was considered
             detailed_log_entries.append(f" (Agent A considered RAG: {rag_context_log})")


        final_decision_for_article = random.choice(["Included", "Excluded"]) # Simplified
        final_score = round(random.uniform(1.0, 5.0),1) if has_scorer_in_workflow else "N/A"
        summary_reasoning = f"Simulated overall summary for '{title[:30]}...'"
        extracted_concepts = []
        if final_decision_for_article == "Included":
            base_concepts = ["AI", "Machine Learning", "Healthcare", "Diagnostics", "Treatment", "Clinical Trials", "Radiology", "Pathology", "Genomics", "Drug Discovery", "Literature Review", "Systematic Review", "Meta-Analysis"]
            extracted_concepts = random.sample(base_concepts, k=random.randint(2,6))
            if "AI" in extracted_concepts and random.random() > 0.6: extracted_concepts.append("Deep Learning")

        results_list.append({
            "Article ID": article_id, "Title": title, "Abstract": abstract,
            "Final Decision": final_decision_for_article, "Avg Score": final_score,
            "Reasoning Summary": summary_reasoning,
            "Detailed Workflow Log": "\n\n".join(detailed_log_entries),
            "Extracted Concepts": extracted_concepts if extracted_concepts else []
        })
    return pd.DataFrame(results_list)


def execute_review_workflow_stub(project_workflow, ris_data_df, rag_files_list): # MODIFIED for RAG
    st.session_state.review_log.append("Starting review (sim)...");
    # ... (simulation loop - unchanged) ...
    st.session_state.review_results = generate_simulated_results(ris_data_df, project_workflow, rag_files_list) # Pass RAG files
    # ... (rest of function - unchanged) ...
    st.session_state.review_log.append("Review (sim) completed!"); st.session_state.review_status_message = "Sim Complete! Results ready."
    st.session_state.review_progress = 100; st.session_state.review_in_progress = False


# --- Main Application UI ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")
    # Session state init (condensed)
    for k, dv in [
        ("api_key_entered",False),("gemini_api_key",""),("selected_project_id",None),
        ("workflow_config",{}),("ris_dataframes",{}),("active_ris_filename",None),
        ("selected_project_display_name",None),("show_create_project_modal",False),
        ("review_in_progress",False),("review_log",[]),("review_progress",0),
        ("review_status_message",""),("review_results",None),("data_editor_key",0),
        ("project_rag_files", []) # For TODO 5.3
    ]:
        if k not in st.session_state: st.session_state[k]=dv

    def load_project_rag_files_to_session(project_id):
        config_path = os.path.join(PROJECTS_ROOT_DIR, project_id, "project_config.json")
        try:
            with open(config_path, 'r') as f: config = json.load(f)
            st.session_state.project_rag_files = config.get("rag_files", [])
        except: st.session_state.project_rag_files = []


    def get_current_project_workflow(): # Unchanged
        pid=st.session_state.selected_project_id; # ...
        if not pid: return None
        if pid not in st.session_state.workflow_config or not st.session_state.workflow_config[pid].get("rounds"):
            st.session_state.workflow_config[pid]={"rounds":[{"name":"Round 1","agents":[],"filter_config":{"type":"all_previous"}}]}
        wf=st.session_state.workflow_config[pid]
        for i,rd in enumerate(wf["rounds"]):
            if "filter_config" not in rd: wf["rounds"][i]["filter_config"]={"type":"all_previous"} if i==0 else {"type":"included_previous"}
        return wf
    def is_workflow_runnable(wf): # Unchanged
        if not wf or not wf.get("rounds"): return False; # ...
        for _,rd in enumerate(wf["rounds"]):
            if not rd.get("agents"): return False
        return True

    # Sidebar, Title, Project/Data Management (condensed for brevity)
    with st.sidebar:
        st.title("LatteReview Settings")
        # ... API Key ...
        existing_projects_list = get_existing_projects(); project_options = {p['id']: p['name'] for p in existing_projects_list}
        sel_proj_id_sb = st.sidebar.selectbox("Active Project", [""] + list(project_options.keys()), format_func=lambda x: project_options.get(x, "Select..."), key="sb_proj_sel")
        if sel_proj_id_sb and sel_proj_id_sb != st.session_state.selected_project_id:
            st.session_state.selected_project_id = sel_proj_id_sb; st.session_state.selected_project_display_name = project_options[sel_proj_id_sb]
            st.session_state.active_ris_filename = None; get_current_project_workflow()
            st.session_state.review_in_progress = False; st.session_state.review_log = []; st.session_state.review_progress = 0; st.session_state.review_results = None
            st.session_state.data_editor_key += 1
            load_project_rag_files_to_session(sel_proj_id_sb) # Load RAG files for new project
            st.rerun()
        if st.session_state.selected_project_id: st.sidebar.caption(f"Current: {st.session_state.selected_project_display_name}")


    st.title("LatteReview 🤖☕") # ...
    if not st.session_state.selected_project_id: st.info("Select/create project."); st.stop()

    # Data Management & RAG Upload (TODO 5.3 A)
    st.subheader(f"Data & Context: {st.session_state.selected_project_display_name}")
    project_data_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "data")
    project_rag_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "rag_context")
    if not os.path.exists(project_rag_path): os.makedirs(project_rag_path)

    # RIS File Management (condensed)
    # ... (Assume RIS selection and processing UI is here) ...
    active_df_to_display = None
    if st.session_state.active_ris_filename and st.session_state.selected_project_id:
        active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)
    # For brevity, assume active_df_to_display gets populated correctly if a RIS file is processed.
    # If not, the app stops or shows a warning.
    if active_df_to_display is None:
        st.warning("No RIS data processed for the selected project. Please upload and process a RIS file under 'Data Management'.")
        # Simplified RIS upload for focus
        example_ris_files = [f for f in os.listdir(project_data_path) if f.endswith(".ris")] if os.path.exists(project_data_path) else []
        sel_ris = st.selectbox("Select RIS to Process:", [""]+example_ris_files, format_func=lambda x:x or "Select...")
        if sel_ris and st.button(f"Process {sel_ris}"): # Simplified processing
            df,err = parse_ris_file(os.path.join(project_data_path, sel_ris))
            if df is not None: st.session_state.ris_dataframes.setdefault(st.session_state.selected_project_id, {})[sel_ris] = df; st.session_state.active_ris_filename = sel_ris; st.rerun()
            else: st.error(err)
        st.stop()

    st.info(f"Using dataset: `{st.session_state.active_ris_filename}` ({len(active_df_to_display)} articles)")

    # RAG Background Document Upload (TODO 5.3 A)
    with st.expander("Upload Background Materials for RAG (Optional PDF/TXT)"):
        uploaded_rag_files = st.file_uploader(
            "Upload 1-3 core papers or research plans:",
            type=["pdf", "txt"],
            accept_multiple_files=True,
            key=f"rag_uploader_{st.session_state.selected_project_id}"
        )
        if uploaded_rag_files:
            newly_uploaded_filenames = []
            for uploaded_file in uploaded_rag_files:
                # Prevent saving if too many files are already there (e.g., limit to 3-5)
                if len(st.session_state.project_rag_files) + len(newly_uploaded_filenames) >= 5: # Example limit
                    st.warning(f"Reached RAG file limit (5). Cannot upload '{uploaded_file.name}'.")
                    break

                file_path = os.path.join(project_rag_path, uploaded_file.name)
                try:
                    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    newly_uploaded_filenames.append(uploaded_file.name)
                except Exception as e: st.error(f"Error saving RAG file '{uploaded_file.name}': {e}")

            if newly_uploaded_filenames:
                st.success(f"Uploaded RAG background files: {', '.join(newly_uploaded_filenames)}")
                # Update session state and project config
                current_rag_files_set = set(st.session_state.project_rag_files)
                current_rag_files_set.update(newly_uploaded_filenames)
                st.session_state.project_rag_files = sorted(list(current_rag_files_set))
                update_project_rag_files(st.session_state.selected_project_id, st.session_state.project_rag_files)
                st.rerun() # Rerun to clear uploader and reflect changes

        st.write("**Current RAG Background Files:**")
        if st.session_state.project_rag_files:
            for rag_file_name in st.session_state.project_rag_files:
                col1_rag, col2_rag = st.columns([0.8, 0.2])
                col1_rag.caption(rag_file_name)
                # Add delete button for each RAG file
                if col2_rag.button(f"🗑️ {rag_file_name[:10]}...", key=f"del_rag_{rag_file_name}", help=f"Delete {rag_file_name}"):
                    try:
                        os.remove(os.path.join(project_rag_path, rag_file_name))
                        st.session_state.project_rag_files.remove(rag_file_name)
                        update_project_rag_files(st.session_state.selected_project_id, st.session_state.project_rag_files)
                        st.success(f"Deleted RAG file: {rag_file_name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting RAG file '{rag_file_name}': {e}")
        else:
            st.caption("No background documents uploaded for this project.")

        # TODO 5.3 B - Simulate Vector Store Creation
        if st.session_state.project_rag_files:
            st.info("Simulated: If these files changed, a vector store would be updated/rebuilt here.")


    st.divider()
    # Workflow Config & Execution (condensed)
    # ... (Assume this section is present and functional) ...
    st.subheader(f"Workflow & Execution") # Simplified
    current_workflow = get_current_project_workflow()
    if (st.session_state.api_key_entered and active_df_to_display is not None and is_workflow_runnable(current_workflow)):
        if st.button("🚀 Start Review (Sim)", disabled=st.session_state.review_in_progress):
             st.session_state.review_in_progress=True; st.session_state.review_log=[]; st.session_state.review_progress=0
             # Pass the list of RAG file names to the execution stub
             execute_review_workflow_stub(current_workflow, active_df_to_display, st.session_state.project_rag_files)
             st.session_state.data_editor_key+=1; st.rerun()

    # ... (Progress display) ...

    # --- Results Display Section ---
    # ... (Assume this section is present and functional, including tabs for Overview and Theme Analysis) ...
    if st.session_state.review_results is not None and not st.session_state.review_in_progress:
        st.divider(); st.subheader("📄 Review Analysis")
        # ... (Tabs and content within tabs) ...

if __name__ == "__main__":
    main()
