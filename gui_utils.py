import streamlit as st # For decorators and potentially other UI elements if any are moved here
import os
import re
from datetime import datetime
import json
import pandas as pd
import random # For fallbacks in parse_ris_file etc.

# Assuming data_handler and agent/workflow classes are imported where they are used (e.g. in app.py or here if needed for helpers)
# For functions moved from app.py that depend on these, they might need to be passed as args or imported here.
# For now, data_handler is used by parse_ris_file, so it's needed here.
from lattereview.utils import data_handler
from lattereview.agents import TitleAbstractReviewer, ScoringReviewer, AbstractionReviewer
from lattereview.providers import LiteLLMProvider
from lattereview.workflows import ReviewWorkflow
from collections import Counter # If used by any moved helper, e.g. post_process_review_results
from itertools import combinations # If used by any moved helper

# --- Constants ---
PROJECTS_ROOT_DIR = "lattereview_projects"
AGENT_TYPES_MAP = {
    "TitleAbstractReviewer": TitleAbstractReviewer,
    "ScoringReviewer": ScoringReviewer,
    "AbstractionReviewer": AbstractionReviewer,
}
AGENT_TYPE_NAMES = list(AGENT_TYPES_MAP.keys())


# --- Helper Functions moved from app.py ---

def sanitize_project_name(name):
    name = name.strip(); name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name); name = re.sub(r'\s+', '_', name)
    return name

def create_project_structure(project_name):
    sanitized_name = sanitize_project_name(project_name)
    if not sanitized_name: return False, "Invalid project name."
    project_path = os.path.join(PROJECTS_ROOT_DIR, sanitized_name)
    if os.path.exists(project_path): return False, f"Project '{sanitized_name}' already exists."
    try:
        os.makedirs(project_path); os.makedirs(os.path.join(project_path, "data")); os.makedirs(os.path.join(project_path, "results")); os.makedirs(os.path.join(project_path, "rag_context"))
        ct = datetime.now().isoformat()
        with open(os.path.join(project_path, "project_config.json"), 'w') as f: json.dump({"project_name": project_name, "sanitized_name": sanitized_name, "created_at": ct, "rag_files": []}, f, indent=2)
        return True, f"Project '{project_name}' created successfully."
    except OSError as e: return False, f"Error: {e}"

def get_existing_projects():
    if not os.path.exists(PROJECTS_ROOT_DIR): return []
    projects = []
    for item in os.listdir(PROJECTS_ROOT_DIR):
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)):
            dn = item; rf = []
            try:
                with open(os.path.join(PROJECTS_ROOT_DIR, item, "project_config.json"), 'r') as f: cfg = json.load(f)
                dn = cfg.get("project_name", item); rf = cfg.get("rag_files", [])
                projects.append({"id": item, "name": dn, "rag_files": rf})
            except Exception: projects.append({"id": item, "name": item, "rag_files": rf})
    return sorted(projects, key=lambda x: x["name"])

def get_project_rag_files_from_config(project_id): # New helper based on app.py logic
    config_path = os.path.join(PROJECTS_ROOT_DIR, project_id, "project_config.json")
    try:
        with open(config_path, 'r') as f: config = json.load(f)
        return config.get("rag_files", [])
    except: return []


def update_project_rag_files(project_id, rag_file_names):
    config_path = os.path.join(PROJECTS_ROOT_DIR, project_id, "project_config.json")
    try:
        with open(config_path, 'r') as f: config = json.load(f)
        config["rag_files"] = rag_file_names
        with open(config_path, 'w') as f: json.dump(config, f, indent=2)
        return True
    except Exception as e:
        # st.error(f"Error updating project config: {e}") # Cannot use st.error directly in utils if not running Streamlit page
        print(f"Error updating project config for {project_id}: {e}") # Log to console
        return False

@st.cache_data # Added decorator
def parse_ris_file(file_path_or_uploaded_file): # Can accept path or UploadedFile
    try:
        # If it's an UploadedFile, use its getbuffer() method, otherwise assume it's a path
        # data_handler.RISHandler might need adjustment or this function needs to handle both.
        # For now, assuming RISHandler can take a path. If UploadedFile, need to save it first or pass bytes.
        # The app.py logic currently saves UploadedFile then passes path, so this should be fine.

        df = data_handler.RISHandler().load_ris_file_to_dataframe(file_path_or_uploaded_file)
        col_map = {
            'TI':'title', 'T1':'title', 'primary_title':'title',
            'AU':'authors', 'PY':'year', 'Y1':'year', 'AB':'abstract', 'N2':'abstract',
            'JO':'journal_name', 'JF':'journal_name', 'T2':'journal_name',
            'KW':'keywords', 'ID':'id', 'AN':'id', 'UT':'id'
        }
        df = df.rename(columns=col_map, errors='ignore')
        for col in ['id','title','abstract']:
            if col not in df.columns: df[col] = f"Missing_{col}_{random.randint(1,100)}"
        for col_name in ['authors', 'keywords']:
            if col_name in df.columns:
                df[col_name] = df[col_name].apply(
                    lambda x: [str(item).strip() for item in str(x).split(';')] if pd.notna(x) and isinstance(x, str)
                    else ([str(item).strip() for item in x] if isinstance(x, list)
                    else ([] if pd.isna(x) else [str(x).strip()])))
            else: df[col_name] = [[] for _ in range(len(df))]
        if 'year' in df.columns:
            df['year'] = df['year'].apply(lambda x: str(x).split('.')[0] if pd.notna(x) else None)
        else: df['year'] = [str(random.randint(2000,2023)) for _ in range(len(df))]
        if 'journal_name' not in df.columns: df['journal_name'] = [f"Unknown Journal {i}" for i in range(len(df))]
        return df, None
    except Exception as e: return None, f"Parse Error for {str(file_path_or_uploaded_file)}: {e}" # Use str() for UploadedFile name

@st.cache_data # Added decorator
def extract_text_from_rag_document(file_path):
    _, file_extension = os.path.splitext(file_path); text = ""
    try:
        if file_extension.lower() == '.txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: text = f.read()
        elif file_extension.lower() == '.pdf':
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(file_path)
                for page_num in range(len(reader.pages)): text += reader.pages[page_num].extract_text() or ""
            except ImportError:
                # st.error("PyPDF2 needed for PDFs.") # Cannot use st.error directly
                print("PyPDF2 library is required for PDF processing but not found.")
                return None
            except Exception as e:
                # st.warning(f"PDF parse error {os.path.basename(file_path)}: {e}")
                print(f"PDF parse error {os.path.basename(file_path)}: {e}")
                return None
        else:
            # st.warning(f"Unsupported RAG file: {file_extension}")
            print(f"Unsupported RAG file: {file_extension} for {os.path.basename(file_path)}")
            return None
        return text.strip() if text else None
    except Exception as e:
        # st.error(f"Error reading RAG file {os.path.basename(file_path)}: {e}")
        print(f"Error reading RAG file {os.path.basename(file_path)}: {e}")
        return None

def build_lattereview_workflow_from_config(gui_workflow_config, api_key, project_rag_files):
    if not api_key: return None # Error handling should be in app.py calling this
    workflow_schema = []; round_ids = [chr(ord('A') + i) for i in range(len(gui_workflow_config.get("rounds", [])))]
    for i, round_data in enumerate(gui_workflow_config.get("rounds", [])):
        round_id_char = round_ids[i]; schema_round = {"round": round_id_char, "reviewers": []}
        schema_round["text_inputs"] = ["title", "abstract"]
        for agent_config in round_data.get("agents", []):
            agent_class = AGENT_TYPES_MAP.get(agent_config["type"])
            if not agent_class: continue # Error handling in app.py
            provider = LiteLLMProvider(model="gemini-2.0-flash", api_key=api_key)
            agent_params = {"provider": provider, "name": agent_config["name"], "backstory": agent_config.get("backstory", ""),
                            "inclusion_criteria": agent_config.get("inclusion_criteria",""), # Corrected key
                            "exclusion_criteria": agent_config.get("exclusion_criteria","")  # Corrected key
                           }
            if project_rag_files: agent_params["additional_context"] = f"RAG context: {', '.join(project_rag_files)}."
            try: schema_round["reviewers"].append(agent_class(**agent_params))
            except Exception as e: return None # Error handling in app.py
        if not schema_round["reviewers"]: return None # Error handling in app.py
        workflow_schema.append(schema_round)
    if not workflow_schema: return None # Error handling in app.py
    try: return ReviewWorkflow(workflow_schema=workflow_schema)
    except Exception as e: return None # Error handling in app.py

def convert_dataframe_to_ris_text(df):
    if df is None or df.empty: return ""
    ris_records = []
    for index, row in df.iterrows():
        lines = ["TY  - JOUR"]
        for tag, col_name in [("TI", "title"), ("ID", "id"), ("AB", "abstract"), ("PY", "year"), ("JO", "journal_name")]:
            if pd.notna(row.get(col_name)) and row.get(col_name): lines.append(f"{tag}  - {row.get(col_name)}")
        for author in row.get("authors", []): lines.append(f"AU  - {author}")
        for kw in row.get("keywords", []): lines.append(f"KW  - {kw}")
        if pd.notna(row.get("final_decision")): lines.append(f"N1  - ReviewDecision: {row.get('final_decision')}")
        if pd.notna(row.get("final_score")) and str(row.get("final_score")).lower() != 'n/a': lines.append(f"N1  - ReviewScore: {row.get('final_score')}")
        lines.append("ER  - ")
        ris_records.append("\n".join(lines))
    return "\n\n".join(ris_records) + "\n"

def is_workflow_runnable(wf):
    if not wf or not wf.get("rounds"): return False
    for r in wf["rounds"]:
        if not r.get("agents"): return False
    return True

def post_process_review_results(results_df_raw, gui_workflow_config):
    if results_df_raw is None: return pd.DataFrame()
    processed_df = results_df_raw.copy()
    summary_cols = ['final_decision', 'final_score', 'reasoning_summary', 'detailed_workflow_log', 'extracted_concepts']
    for col in summary_cols: # Initialize if not present from a direct backend output
        if col not in processed_df.columns:
            if col == 'final_score': processed_df[col] = pd.NA
            elif col == 'extracted_concepts': processed_df[col] = [[] for _ in range(len(processed_df))]
            else: processed_df[col] = "N/A"

    num_r_cfg = len(gui_workflow_config.get("rounds",[])); r_cfg_ids = [chr(ord('A')+r) for r in range(num_r_cfg)]
    if num_r_cfg > 0:
        last_r_id_cfg = r_cfg_ids[-1]; last_r_agents_cfg = gui_workflow_config["rounds"][-1].get("agents",[])
        for idx, raw_row in processed_df.iterrows():
            logs = []; concepts_this_article = set()
            for r_idx_iter, r_data_iter in enumerate(gui_workflow_config.get("rounds",[])): # Iterate through GUI config rounds
                r_id_iter = r_cfg_ids[r_idx_iter]
                for agent_cfg_iter in r_data_iter.get("agents",[]):
                    agent_name_iter = agent_cfg_iter["name"]
                    for suffix in ["evaluation", "score", "reasoning", "extracted_concepts", "error"]:
                        col_name = f"round-{r_id_iter}_{agent_name_iter}_{suffix}"
                        if col_name in raw_row and pd.notna(raw_row[col_name]) and raw_row[col_name] != "":
                            logs.append(f"{col_name}: {raw_row[col_name]}")
                            if suffix == "extracted_concepts" and isinstance(raw_row[col_name], list):
                                concepts_this_article.update(raw_row[col_name])

            processed_df.loc[idx, 'detailed_workflow_log'] = "\n".join(logs)
            if concepts_this_article: processed_df.loc[idx, 'extracted_concepts'] = list(concepts_this_article)

            if last_r_agents_cfg: # Derive final decision/score from last configured round
                first_agent_lr = last_r_agents_cfg[0]["name"]
                eval_col = f"round-{last_r_id_cfg}_{first_agent_lr}_evaluation"
                score_col = f"round-{last_r_id_cfg}_{first_agent_lr}_score"
                reason_col = f"round-{last_r_id_cfg}_{first_agent_lr}_reasoning"
                if eval_col in raw_row and pd.notna(raw_row[eval_col]): processed_df.loc[idx,'final_decision'] = raw_row[eval_col]
                if score_col in raw_row and pd.notna(raw_row[score_col]):
                    try: processed_df.loc[idx,'final_score'] = float(raw_row[score_col])
                    except: pass # Keep pd.NA
                if reason_col in raw_row and pd.notna(raw_row[reason_col]): processed_df.loc[idx,'reasoning_summary'] = str(raw_row[reason_col])[:200]+"..."
    return processed_df

# Note: generate_simulated_results is now only used if build_lattereview_workflow_from_config returns a DummyWorkflow
# For actual LatteReview execution, the output of workflow_instance() is used directly.
# The DummyWorkflow's generate_simulated_results should produce a "raw" looking output that post_process_review_results can then summarize.

# --- UI Rendering Functions (render_sidebar, render_project_management_ui etc. - assumed complete from app.py) ---
# These would be defined here in a full gui_utils.py
# For this subtask, we are only concerned with the helper functions above.
# Example:
# def render_rag_file_manager(project_rag_path, project_id):
#   st.write("RAG File Manager UI (from gui_utils)")
# def render_workflow_configuration_editor(workflow_config, agent_type_names_list):
#   st.write("Workflow Config Editor UI (from gui_utils)")
# def render_results_overview_tab(review_results_df, data_editor_key_val):
#   st.write("Results Overview Tab UI (from gui_utils)")
# def render_theme_analysis_tab(review_results_df, project_id_val):
#   st.write("Theme Analysis Tab UI (from gui_utils)")

# (No main() function in gui_utils.py)
# Reviewed and ensured all significant code comments are in English (Conceptual Step).
# REVIEW NOTE for Plan Step: Prepare for lattereview Integration
# ... (comments from previous step) ...
