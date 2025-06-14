import streamlit as st
import os
import re
from datetime import datetime
import json
from lattereview.utils import data_handler
from lattereview.agents import TitleAbstractReviewer, ScoringReviewer, AbstractionReviewer
from lattereview.providers import LiteLLMProvider
from lattereview.workflows import ReviewWorkflow
import pandas as pd
import time
import random
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import asyncio
import nest_asyncio
nest_asyncio.apply()

PROJECTS_ROOT_DIR = "lattereview_projects"
AGENT_TYPES_MAP = {"TitleAbstractReviewer": TitleAbstractReviewer, "ScoringReviewer": ScoringReviewer, "AbstractionReviewer": AbstractionReviewer}
AGENT_TYPE_NAMES = list(AGENT_TYPES_MAP.keys())

# --- Helper Functions (Assume complete and correct) ---
def sanitize_project_name(name): return re.sub(r'\s+', '_', re.sub(r'[^a-zA-Z0-9_\-\s]', '', name.strip()))
def create_project_structure(project_name):
    s_name=sanitize_project_name(project_name); p_path=os.path.join(PROJECTS_ROOT_DIR,s_name)
    if not s_name or os.path.exists(p_path): return False, "Error creating: Invalid name or project exists."
    try:
        for sub_dir in ["", "data", "results", "rag_context"]: os.makedirs(os.path.join(p_path, sub_dir), exist_ok=True)
        with open(os.path.join(p_path, "project_config.json"),'w') as f: json.dump({"project_name":project_name,"sanitized_name":s_name,"created_at":datetime.now().isoformat(),"rag_files":[]},f,indent=2)
        return True, f"Project '{project_name}' created."
    except OSError as e: return False, f"Error creating: {e}"
def get_existing_projects():
    if not os.path.exists(PROJECTS_ROOT_DIR): return []
    proj_list = []; # Simplified for brevity
    for item in os.listdir(PROJECTS_ROOT_DIR):
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)): proj_list.append({"id":item, "name":item, "rag_files":[]})
    return proj_list
def update_project_rag_files(project_id, rag_file_names): return True
def parse_ris_file(file_path):
    try:
        df = data_handler.RISHandler().load_ris_file_to_dataframe(file_path)
        col_map = {'TI':'title','AB':'abstract','ID':'id','PY':'year','AU':'authors'}; df = df.rename(columns=col_map, errors='ignore')
        for col in ['id','title','abstract']:
            if col not in df.columns: df[col] = f"Missing_{col}_{random.randint(1,100)}"
        return df, None
    except Exception as e: return None, f"Parse Error: {e}"
def extract_text_from_rag_document(file_path): # Assumed complete
    # ...
    return "Sample RAG text snippet..."

def build_lattereview_workflow_from_config(gui_workflow_config, api_key, project_rag_files): # Assumed complete
    # ...
    class DummyWorkflow:
        async def __call__(self, data, return_type):
            # This now needs to return a DataFrame that resembles real LatteReview output
            # with per-agent columns, not the one from generate_simulated_results.
            # For this test, let's make a mock real output.

            # Get round and agent names from config for column naming
            mock_results = []
            num_rounds_in_workflow = len(gui_workflow_config.get("rounds", []))
            round_ids = [chr(ord('A') + i) for i in range(num_rounds_in_workflow)]

            for idx, r_in in data.iterrows():
                res_row = r_in.to_dict()
                for r_idx, round_data_cfg in enumerate(gui_workflow_config.get("rounds", [])):
                    round_id_char = round_ids[r_idx]
                    for agent_cfg in round_data_cfg.get("agents", []):
                        agent_name = agent_cfg["name"]
                        res_row[f"round-{round_id_char}_{agent_name}_evaluation"] = random.choice(["Included", "Excluded"])
                        res_row[f"round-{round_id_char}_{agent_name}_reasoning"] = f"Reasoning by {agent_name} for {r_in['id']}"
                        if agent_cfg["type"] == "ScoringReviewer":
                            res_row[f"round-{round_id_char}_{agent_name}_score"] = round(random.uniform(1,5),1)
                        if agent_cfg["type"] == "AbstractionReviewer":
                            res_row[f"round-{round_id_char}_{agent_name}_extracted_concepts"] = random.sample(["RealConcept1", "RealConcept2", "RC3"], k=1)
                mock_results.append(res_row)
            return pd.DataFrame(mock_results)
    if gui_workflow_config: # Basic check
        return DummyWorkflow()
    return None


# --- Main Application UI ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")
    # Session state init (condensed)
    for k, dv in [("api_key_entered",True),("gemini_api_key","test_key"),("selected_project_id",None),("workflow_config",{}),("ris_dataframes",{}),("active_ris_filename",None),("selected_project_display_name",None),("review_in_progress",False),("review_log",[]),("review_progress",0),("review_status_message",""),("review_results",None),("data_editor_key",0), ("project_rag_files", [])]:
        if k not in st.session_state: st.session_state[k]=dv

    def get_current_project_workflow(): # Simplified for test
        pid=st.session_state.selected_project_id
        if not pid: return None
        if pid not in st.session_state.workflow_config or not st.session_state.workflow_config[pid].get("rounds"):
             st.session_state.workflow_config[pid]={"rounds":[{"name":"R1","agents":[{"name":"Agent1","type":"TitleAbstractReviewer","incl_crit":"ic","excl_crit":"ec"}],"filter_config":{"type":"all"}}]}
        return st.session_state.workflow_config[pid]
    def is_workflow_runnable(wf): return True if wf and wf.get("rounds") and wf["rounds"][0].get("agents") else False


    # --- UI Sections (Simplified for focus) ---
    st.title("LatteReview 🤖☕ - Test Actual Output Handling")
    st.session_state.selected_project_id = "test_proj" # Force a project for test
    st.session_state.active_ris_filename = "test.ris"  # Force active data for test
    st.session_state.ris_dataframes["test_proj"] = {"test.ris": pd.DataFrame({'id':['art1','art2'],'title':['Title1','Title2'],'abstract':['Abs1','Abs2']})}
    active_df_to_display = st.session_state.ris_dataframes["test_proj"]["test.ris"]
    current_gui_workflow_config = get_current_project_workflow()


    if st.button("🚀 Start Actual Review (Test Post-Processing)", disabled=st.session_state.review_in_progress):
        st.session_state.review_in_progress = True; st.session_state.review_log = ["Building..."]; st.session_state.review_progress = 5; st.rerun()

    if st.session_state.review_in_progress and st.session_state.review_log[-1].startswith("Building..."):
        wf_instance = build_lattereview_workflow_from_config(current_gui_workflow_config, "test_key", [])
        if wf_instance:
            st.session_state.review_log.append("Workflow built. Running..."); st.session_state.review_progress = 10; st.session_state.review_status_message = "Running..."; st.rerun()

    if st.session_state.review_in_progress and st.session_state.review_log[-1].startswith("Workflow built."):
        try:
            with st.spinner("Processing..."):
                # This is where asyncio.run(wf_instance(data=...)) would be
                # For this step, wf_instance is a DummyWorkflow that calls a mock real output generator
                results_df_raw = asyncio.run(wf_instance(data=active_df_to_display, return_type="pandas"))

            st.session_state.review_log.append("Raw results received from backend.")
            st.session_state.review_status_message = "Post-processing results..."
            st.session_state.review_progress = 90

            # ***** START OF NEW POST-PROCESSING LOGIC *****
            processed_df = results_df_raw.copy()
            # For debugging in a live environment:
            # st.subheader("Raw Workflow Output Columns"); st.write(processed_df.columns.tolist())
            # st.subheader("Raw Workflow Output Head"); st.dataframe(processed_df.head())

            processed_df['final_decision'] = "N/A"
            processed_df['final_score'] = pd.NA
            processed_df['reasoning_summary'] = ""
            new_detailed_log_col_list = [] # Changed name to avoid conflict

            num_rounds_in_cfg = len(current_gui_workflow_config.get("rounds", []))
            round_cfg_ids = [chr(ord('A') + r) for r in range(num_rounds_in_cfg)]

            if num_rounds_in_cfg > 0:
                last_round_id_char_cfg = round_cfg_ids[-1]
                last_round_agents_cfg = current_gui_workflow_config["rounds"][-1].get("agents", [])

                for index, row_raw in processed_df.iterrows():
                    current_row_event_logs = []
                    for col in processed_df.columns: # Consolidate all per-agent/round outputs into one log
                        # Exclude original base columns and already processed summary columns from this detailed log
                        if col not in ['id','title','abstract','final_decision','final_score','reasoning_summary','detailed_workflow_log','extracted_concepts', '_selected'] and pd.notna(row_raw[col]) and row_raw[col] != "":
                            current_row_event_logs.append(f"{col}: {row_raw[col]}")

                    final_decision_val = "N/A" # Default for current row
                    final_score_val = pd.NA    # Default for current row
                    reasoning_sum_val = ""   # Default for current row

                    if last_round_agents_cfg:
                        # Simplistic: use first agent of last configured round for final decision/score
                        # More robust: find actual last round columns in results_df_raw if they differ from config
                        first_agent_name_lr_cfg = last_round_agents_cfg[0]["name"]

                        eval_col = f"round-{last_round_id_char_cfg}_{first_agent_name_lr_cfg}_evaluation"
                        score_col = f"round-{last_round_id_char_cfg}_{first_agent_name_lr_cfg}_score"
                        reason_col = f"round-{last_round_id_char_cfg}_{first_agent_name_lr_cfg}_reasoning"

                        if eval_col in row_raw and pd.notna(row_raw[eval_col]): final_decision_val = row_raw[eval_col]
                        if score_col in row_raw and pd.notna(row_raw[score_col]):
                            try: final_score_val = float(row_raw[score_col])
                            except: final_score_val = pd.NA # Keep as NA if not convertible
                        if reason_col in row_raw and pd.notna(row_raw[reason_col]):
                            reasoning_sum_val = str(row_raw[reason_col])
                            if len(reasoning_sum_val) > 200 : reasoning_sum_val = reasoning_sum_val[:200] + "..." # Truncate summary

                    processed_df.loc[index, 'final_decision'] = final_decision_val
                    processed_df.loc[index, 'final_score'] = final_score_val
                    processed_df.loc[index, 'reasoning_summary'] = reasoning_sum_val
                    new_detailed_log_col_list.append("\n".join(current_row_event_logs))

                processed_df['detailed_workflow_log'] = new_detailed_log_col_list
            else: # No rounds in workflow config
                 processed_df['detailed_workflow_log'] = ["Error: Workflow had no rounds in config" for _ in range(len(processed_df))]

            st.session_state.review_results = processed_df # Store processed results
            # ***** END OF NEW POST-PROCESSING LOGIC *****

            st.session_state.review_log.append(f"Results processed. Articles: {len(st.session_state.review_results)}")
            st.session_state.review_status_message = "Actual Review Complete! Results processed."
            st.session_state.review_progress = 100; st.balloons()
        except Exception as e:
            st.session_state.review_log.append(f"Error during review: {e}"); st.error(f"Review failed: {e}"); st.session_state.review_status_message = f"Error: {e}"
        finally:
            st.session_state.review_in_progress = False; st.rerun()

    # Display results (Simplified)
    if st.session_state.review_results is not None:
        st.subheader("Processed Review Results")
        # Display relevant columns, including new summary ones and the detailed log
        display_cols = ['id', 'title', 'final_decision', 'final_score', 'reasoning_summary', 'detailed_workflow_log']
        # Filter out columns not present in the dataframe to avoid errors
        display_cols = [col for col in display_cols if col in st.session_state.review_results.columns]
        st.dataframe(st.session_state.review_results[display_cols].head())

if __name__ == "__main__":
    main()
