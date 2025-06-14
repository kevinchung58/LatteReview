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

PROJECTS_ROOT_DIR = "lattereview_projects"

AGENT_TYPES = {
    "TitleAbstractReviewer": TitleAbstractReviewer,
    "ScoringReviewer": ScoringReviewer,
    "AbstractionReviewer": AbstractionReviewer,
}
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
        if 'title' not in df.columns and 'TI' in df.columns: df = df.rename(columns={'TI': 'title'})
        if 'title' not in df.columns and 'primary_title' in df.columns: df = df.rename(columns={'primary_title': 'title'})
        if 'id' not in df.columns:
            if 'ID' in df.columns: df = df.rename(columns={'ID': 'id'})
            elif 'AN' in df.columns: df = df.rename(columns={'AN': 'id'})
            else: df['id'] = [f"Art{i}" for i in range(len(df))]
        if 'abstract' not in df.columns and 'AB' in df.columns: df = df.rename(columns={'AB': 'abstract'})
        return df, None
    except Exception as e: return None, f"Error parsing '{os.path.basename(file_path)}': {e}"

def generate_simulated_results(ris_data_df, project_workflow):
    results_list = []
    if ris_data_df is None or ris_data_df.empty: return pd.DataFrame()
    if 'id' not in ris_data_df.columns: return pd.DataFrame() # Should have id
    has_scorer = any(a.get("type") == "ScoringReviewer" for r in project_workflow.get("rounds", []) for a in r.get("agents", []))
    for index, row in ris_data_df.iterrows():
        article_id = row['id']; title = row.get('title', f"Unknown Title for {article_id}"); abstract = row.get('abstract', "N/A")
        decision = random.choice(["Included", "Excluded", "Unsure"]); score = round(random.uniform(1.0, 5.0),1) if has_scorer else "N/A"
        summary = f"Simulated summary for '{title[:30]}...'"; detailed_log = ""
        for r_idx, r_data in enumerate(project_workflow.get("rounds",[])):
            for a_idx, a_data in enumerate(r_data.get("agents",[])):
                detailed_log += f"R{r_idx+1}-{a_data.get('name')}: Decided '{random.choice(['Incl','Excl'])}'. Notes...\n"
        results_list.append({"Article ID": article_id, "Title": title, "Abstract": abstract, "Final Decision": decision, "Avg Score": score, "Reasoning Summary": summary, "Detailed Workflow Log": detailed_log.strip()})
    return pd.DataFrame(results_list)

def execute_review_workflow_stub(project_workflow, ris_data_df): # (Unchanged)
    st.session_state.review_log.append("Starting review (sim)..."); st.session_state.review_status_message = "Initializing..."; st.session_state.review_results = None
    num_r = len(project_workflow.get("rounds", [])); tot_steps = num_r * 3 or 1; curr_step = 0
    for i, r_data in enumerate(project_workflow.get("rounds", [])):
        r_name = r_data.get("name", f"R {i+1}")
        st.session_state.review_log.append(f"Starting {r_name}..."); st.session_state.review_status_message = f"{r_name}: Init agents..."
        curr_step +=1; st.session_state.review_progress = int((curr_step/tot_steps)*100); time.sleep(0.1)
        num_a = len(r_data.get("agents", []))
        st.session_state.review_log.append(f"{r_name}: {num_a} agent(s)."); st.session_state.review_status_message = f"{r_name}: Processing..."
        curr_step +=1; st.session_state.review_progress = int((curr_step/tot_steps)*100); time.sleep(0.2)
        num_art = len(ris_data_df) if ris_data_df is not None else 0
        st.session_state.review_log.append(f"{r_name}: Simulating {num_art} articles.")
        if num_art > 0:
            for art_idx in range(num_art):
                 if art_idx % (num_art//5+1)==0: st.session_state.review_status_message = f"{r_name}: Article {art_idx+1}/{num_art}..."; time.sleep(0.01)
        st.session_state.review_log.append(f"{r_name} done."); st.session_state.review_status_message = f"{r_name}: Finalizing..."
        curr_step +=1; st.session_state.review_progress = int((curr_step/tot_steps)*100); time.sleep(0.1)
    st.session_state.review_results = generate_simulated_results(ris_data_df, project_workflow)
    st.session_state.review_log.append("Review (sim) completed!"); st.session_state.review_status_message = "Sim Complete! Results ready."
    st.session_state.review_progress = 100; st.session_state.review_in_progress = False

# --- Main Application UI ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")
    # Session state init (condensed)
    for k, dv in [("api_key_entered",False),("gemini_api_key",""),("selected_project_id",None),("workflow_config",{}),("ris_dataframes",{}),("active_ris_filename",None),("selected_project_display_name",None),("show_create_project_modal",False),("review_in_progress",False),("review_log",[]),("review_progress",0),("review_status_message",""),("review_results",None),("data_editor_key",0)]:
        if k not in st.session_state: st.session_state[k]=dv

    def get_current_project_workflow(): # (Unchanged)
        pid=st.session_state.selected_project_id
        if not pid: return None
        if pid not in st.session_state.workflow_config or not st.session_state.workflow_config[pid].get("rounds"):
            st.session_state.workflow_config[pid]={"rounds":[{"name":"Round 1","agents":[],"filter_config":{"type":"all_previous"}}]}
        wf=st.session_state.workflow_config[pid]
        for i,rd in enumerate(wf["rounds"]):
            if "filter_config" not in rd: wf["rounds"][i]["filter_config"]={"type":"all_previous"} if i==0 else {"type":"included_previous"}
        return wf
    def is_workflow_runnable(wf): # (Unchanged)
        if not wf or not wf.get("rounds"): return False
        for _,rd in enumerate(wf["rounds"]):
            if not rd.get("agents"): return False
        return True

    # Sidebar, Title, Project/Data Management (condensed)
    with st.sidebar: # Simplified
        st.title("LatteReview"); st.caption("Settings & Nav"); st.divider(); st.subheader("Settings")
        # API Key, Project Selector (assume present)
        # ...
    st.title("LatteReview 🤖☕") # ...
    if not st.session_state.selected_project_id: st.info("Select/create project."); st.stop()
    # ... (Data loading UI - assume present and active_df_to_display is populated) ...
    active_df_to_display = None
    if st.session_state.active_ris_filename and st.session_state.selected_project_id:
        active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)
    if active_df_to_display is None: st.warning("No RIS data processed."); st.stop()


    # Workflow Config & Execution (condensed)
    st.subheader(f"Workflow & Execution: {st.session_state.selected_project_display_name}")
    current_workflow = get_current_project_workflow()
    # ... (Workflow definition UI - assume present) ...
    # ... (Start Review button & Progress UI - assume present) ...
    if (st.session_state.api_key_entered and active_df_to_display is not None and is_workflow_runnable(current_workflow)):
        if st.button("🚀 Start Review", disabled=st.session_state.review_in_progress):
             st.session_state.review_in_progress=True; st.session_state.review_log=[]; st.session_state.review_progress=0
             execute_review_workflow_stub(current_workflow, active_df_to_display); st.session_state.data_editor_key+=1; st.rerun()
    if st.session_state.review_in_progress or st.session_state.review_progress==100: st.caption(f"Progress: {st.session_state.review_progress}%") # Simplified progress

    # --- Results Display Section (TODO 4.2, 4.3, 4.4) ---
    if st.session_state.review_results is not None and not st.session_state.review_in_progress:
        st.divider(); st.subheader("📄 Review Results")
        results_df = st.session_state.review_results.copy()
        if "_selected" not in results_df.columns: results_df.insert(0, "_selected", False)

        # Filters (TODO 4.2 UI)
        filter_cols = st.columns([2,2,1])
        dec_opts = results_df["Final Decision"].unique().tolist(); sel_decs = filter_cols[0].multiselect("Filter Decision:", dec_opts, default=dec_opts, key="res_dec_filt")
        has_num_scores = 'Avg Score' in results_df.columns and pd.to_numeric(results_df['Avg Score'], errors='coerce').notna().any()
        sel_score_rng = None # Define sel_score_rng before conditional assignment
        if has_num_scores:
            num_scores = pd.to_numeric(results_df['Avg Score'], errors='coerce'); min_s, max_s = float(num_scores.min()), float(num_scores.max())
            sel_score_rng = filter_cols[1].slider("Filter Score:", min_s, max_s, (min_s,max_s), 0.1, key="res_score_filt", disabled=min_s==max_s)

        filtered_df = results_df.copy()
        if sel_decs: filtered_df = filtered_df[filtered_df["Final Decision"].isin(sel_decs)]
        if has_num_scores and sel_score_rng: # check sel_score_rng is not None
            num_s_col = pd.to_numeric(filtered_df['Avg Score'], errors='coerce')
            mask = (num_s_col >= sel_score_rng[0]) & (num_s_col <= sel_score_rng[1])
            if 'Avg Score' in filtered_df.columns and pd.api.types.is_string_dtype(filtered_df['Avg Score']): mask |= (filtered_df['Avg Score'] == "N/A")
            filtered_df = filtered_df[mask]

        st.info(f"Displaying {len(filtered_df)} of {len(results_df)} results.")

        editor_key = f"data_editor_{st.session_state.selected_project_id}_{st.session_state.active_ris_filename}_{st.session_state.data_editor_key}"
        disp_cols = ["_selected", "Article ID", "Title", "Final Decision", "Avg Score"]
        final_disp_cols = [c for c in disp_cols if c in filtered_df.columns]

        edited_display_df = st.data_editor(filtered_df[final_disp_cols] if final_disp_cols else filtered_df, key=editor_key, hide_index=True, num_rows="dynamic", disabled=[c for c in final_disp_cols if c != "_selected"])
        selected_display_rows = edited_display_df[edited_display_df["_selected"]]

        # Detailed View (TODO 4.3)
        if not selected_display_rows.empty:
            st.markdown("---"); st.subheader("Selected Article Details")
            selected_article_ids = selected_display_rows["Article ID"].tolist()
            selected_original_rows = st.session_state.review_results[st.session_state.review_results["Article ID"].isin(selected_article_ids)]
            for _, orig_row in selected_original_rows.iterrows():
                st.markdown(f"#### {orig_row.get('Title', 'N/A')}")
                with st.expander("Full Details & Workflow Log"):
                    st.json(orig_row.to_dict())
                    st.text(orig_row.get('Detailed Workflow Log', "No log."))

        # Export Functionality (TODO 4.4)
        st.markdown("---")
        st.subheader("Export Results")
        export_cols = st.columns(2)
        csv_filtered = filtered_df.drop(columns=["_selected"], errors='ignore').to_csv(index=False).encode('utf-8')
        export_cols[0].download_button(label="📥 Download Filtered CSV", data=csv_filtered, file_name=f"{st.session_state.selected_project_id}_filtered.csv", mime="text/csv", key="exp_filt_csv")
        if not selected_display_rows.empty:
            selected_ids_for_export = selected_display_rows["Article ID"].tolist()
            df_to_export_selected = st.session_state.review_results[st.session_state.review_results["Article ID"].isin(selected_ids_for_export)]
            csv_selected = df_to_export_selected.to_csv(index=False).encode('utf-8') # Export full data for selected
            export_cols[1].download_button(label=f"📥 Download Selected ({len(selected_display_rows)}) CSV", data=csv_selected, file_name=f"{st.session_state.selected_project_id}_selected.csv", mime="text/csv", key="exp_sel_csv")
        else: export_cols[1].caption("Select rows to export.")
        st.button("📥 Download as RIS (Placeholder)", disabled=True)

if __name__ == "__main__":
    main()
