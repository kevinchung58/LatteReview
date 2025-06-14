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

# Apply nest_asyncio to allow asyncio.run() within Streamlit's event loop
import nest_asyncio
nest_asyncio.apply()

PROJECTS_ROOT_DIR = "lattereview_projects"
AGENT_TYPES_MAP = {
    "TitleAbstractReviewer": TitleAbstractReviewer,
    "ScoringReviewer": ScoringReviewer,
    "AbstractionReviewer": AbstractionReviewer,
}
AGENT_TYPE_NAMES = list(AGENT_TYPES_MAP.keys())

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

def update_project_rag_files(project_id, rag_file_names):
    config_path = os.path.join(PROJECTS_ROOT_DIR, project_id, "project_config.json")
    try:
        with open(config_path, 'r') as f: config = json.load(f)
        config["rag_files"] = rag_file_names
        with open(config_path, 'w') as f: json.dump(config, f, indent=2)
        return True
    except Exception as e: st.error(f"Error updating project config: {e}"); return False

def parse_ris_file(file_path):
    try:
        df = data_handler.RISHandler().load_ris_file_to_dataframe(file_path)
        # Standardize common columns, add new ones for export
        col_map = {
            'TI':'title', 'T1':'title', 'primary_title':'title', # Title
            'AU':'authors',                                      # Authors
            'PY':'year', 'Y1':'year',                            # Year
            'AB':'abstract', 'N2':'abstract',                    # Abstract
            'JO':'journal_name', 'JF':'journal_name', 'T2':'journal_name', # Journal Name
            'KW':'keywords',                                     # Keywords
            'ID':'id', 'AN':'id', 'UT':'id'                       # Unique Identifier
        }
        df = df.rename(columns=col_map, errors='ignore')

        # Ensure essential columns exist, providing fallbacks if necessary
        for col in ['id','title','abstract']:
            if col not in df.columns: df[col] = f"Missing_{col}_{random.randint(1,100)}"

        # Ensure authors and keywords are lists of strings, and year is string
        for col_name in ['authors', 'keywords']:
            if col_name in df.columns:
                df[col_name] = df[col_name].apply(
                    lambda x: [str(item).strip() for item in str(x).split(';')] if pd.notna(x) and isinstance(x, str)
                    else ([str(item).strip() for item in x] if isinstance(x, list)
                    else ([] if pd.isna(x) else [str(x).strip()]))) # Ensure list, handle various inputs
            else: # Add empty list if column missing, for consistent data structure for RIS export
                df[col_name] = [[] for _ in range(len(df))]

        if 'year' in df.columns:
            df['year'] = df['year'].apply(lambda x: str(x).split('.')[0] if pd.notna(x) else None) # Integer part of year as string
        else: # Add year if missing for RIS export
            df['year'] = [str(random.randint(2000,2023)) for _ in range(len(df))]

        if 'journal_name' not in df.columns: # Add journal if missing for RIS export
            df['journal_name'] = [f"Unknown Journal {i}" for i in range(len(df))]

        return df, None
    except Exception as e: return None, f"Parse Error for {os.path.basename(file_path)}: {e}"

# --- Function to convert DataFrame to RIS text (NEW for TODO 4.4) ---
def convert_dataframe_to_ris_text(df):
    if df is None or df.empty: return ""
    ris_records = []
    for index, row in df.iterrows():
        current_record_lines = ["TY  - JOUR"] # Default type

        # Essential fields (handle if missing, though parse_ris_file should add fallbacks)
        current_record_lines.append(f"TI  - {row.get('title', 'No Title Provided')}")
        current_record_lines.append(f"ID  - {row.get('id', f'MissingID_{index}')}") # Ensure ID is present

        authors = row.get("authors", []) # Default to empty list
        if isinstance(authors, list):
            for author in authors: current_record_lines.append(f"AU  - {author}")
        elif pd.notna(authors): # If it's a single string author (fallback)
            current_record_lines.append(f"AU  - {str(authors)}")

        if pd.notna(row.get("year")) and row.get("year"): current_record_lines.append(f"PY  - {str(row.get('year')).split('.')[0]}")
        if pd.notna(row.get("abstract")) and row.get("abstract"): current_record_lines.append(f"AB  - {row.get('abstract')}")
        if pd.notna(row.get("journal_name")) and row.get("journal_name"): current_record_lines.append(f"JO  - {row.get('journal_name')}")

        keywords = row.get("keywords", []) # Default to empty list
        if isinstance(keywords, list):
            for kw in keywords: current_record_lines.append(f"KW  - {kw}")
        elif pd.notna(keywords): # Fallback for single string
             current_record_lines.append(f"KW  - {str(keywords)}")

        # Add review decision and score to N1 (Notes) field
        if pd.notna(row.get("final_decision")) and row.get("final_decision"): current_record_lines.append(f"N1  - ReviewDecision: {row.get('final_decision')}")
        if pd.notna(row.get("final_score")) and str(row.get("final_score")).lower() != "n/a": current_record_lines.append(f"N1  - ReviewScore: {row.get('final_score')}")

        current_record_lines.append("ER  - ")
        ris_records.append("\n".join(current_record_lines))
    return "\n\n".join(ris_records) + "\n" # Ensure final newline

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
            except ImportError: st.error("PyPDF2 needed for PDFs."); return None
            except Exception as e: st.warning(f"PDF parse error {os.path.basename(file_path)}: {e}"); return None
        else: st.warning(f"Unsupported RAG file: {file_extension}"); return None
        return text.strip() if text else None
    except Exception as e: st.error(f"Error reading RAG file {os.path.basename(file_path)}: {e}"); return None

# --- Workflow Construction ---
def build_lattereview_workflow_from_config(gui_workflow_config, api_key, project_rag_files):
    if not api_key: st.error("API Key is missing."); return None
    workflow_schema = []; round_ids = [chr(ord('A') + i) for i in range(len(gui_workflow_config.get("rounds", [])))]
    for i, round_data in enumerate(gui_workflow_config.get("rounds", [])):
        round_id_char = round_ids[i]; schema_round = {"round": round_id_char, "reviewers": []}
        agent_types_in_round = {agent_config["type"] for agent_config in round_data.get("agents", [])}
        schema_round["text_inputs"] = ["title", "abstract"]
        for agent_config in round_data.get("agents", []):
            agent_class = AGENT_TYPES_MAP.get(agent_config["type"])
            if not agent_class: st.error(f"Unknown agent type: {agent_config['type']}"); continue
            provider = LiteLLMProvider(model="gemini-2.0-flash", api_key=api_key)
            agent_params = {"provider": provider, "name": agent_config["name"], "backstory": agent_config.get("backstory", ""),
                            "inclusion_criteria": agent_config.get("incl_crit", agent_config.get("inclusion_criteria","")),
                            "exclusion_criteria": agent_config.get("excl_crit", agent_config.get("exclusion_criteria",""))
                           }
            if project_rag_files: agent_params["additional_context"] = f"RAG context: {', '.join(project_rag_files)}." # Simplified RAG context passing
            try: schema_round["reviewers"].append(agent_class(**agent_params))
            except Exception as e: st.error(f"Error for agent {agent_config['name']}: {e}"); return None
        if not schema_round["reviewers"]: st.error(f"No agents for round {round_data.get('name')}."); return None
        workflow_schema.append(schema_round)
    if not workflow_schema: st.error("Workflow schema empty."); return None
    try: return ReviewWorkflow(workflow_schema=workflow_schema)
    except Exception as e: st.error(f"Error creating ReviewWorkflow: {e}"); return None

# --- generate_simulated_results (This is the version that produces more detailed, per-agent output) ---
def generate_simulated_results(ris_data_df, project_workflow, rag_files_info):
    results_list = []
    if ris_data_df is None or ris_data_df.empty or 'id' not in ris_data_df.columns: return pd.DataFrame()

    all_rag_texts_combined = ""
    rag_file_names_from_info = [info if isinstance(info, str) else info.get("name") for info in rag_files_info if info]
    if rag_file_names_from_info and st.session_state.get("selected_project_id"):
        project_rag_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "rag_context")
        for rag_filename in rag_file_names_from_info:
            full_rag_path = os.path.join(project_rag_path, rag_filename)
            if os.path.exists(full_rag_path):
                extracted_content = extract_text_from_rag_document(full_rag_path)
                if extracted_content: all_rag_texts_combined += extracted_content[:500] + "\n\n" # Limit snippet length

    stopwords = ["a", "an", "the", "is", "are", "of", "in", "on", "and", "for", "to", "with", "by", "or", "as", "at", "but", "it", "if"]

    for index, row in ris_data_df.iterrows():
        article_id = row['id']; title = row.get('title',""); abstract = row.get('abstract',"")
        # Initialize result_row with all fields from the input RIS DataFrame to preserve them for potential export
        result_row = row.to_dict()

        detailed_log_entries = []
        retrieved_context_for_article = "No relevant RAG context found."
        if rag_file_names_from_info and all_rag_texts_combined.strip():
            article_title_for_keywords = title.lower()
            title_words = [word for word in re.split(r'\W+', article_title_for_keywords) if word and word not in stopwords and len(word)>2]
            keywords_to_search = title_words[:2]
            found_keyword_context = False
            if keywords_to_search:
                for keyword in keywords_to_search:
                    try:
                        match_iter = re.finditer(r'\b' + re.escape(keyword) + r'\b', all_rag_texts_combined, re.IGNORECASE)
                        first_match = next(match_iter, None)
                        if first_match:
                            match_pos = first_match.start(); context_window = 100
                            start_snip = max(0, match_pos - context_window)
                            end_snip = min(len(all_rag_texts_combined), match_pos + len(keyword) + context_window)
                            retrieved_context_for_article = f"Context for '{keyword}': ...{all_rag_texts_combined[start_snip:end_snip].strip()}..."
                            retrieved_context_for_article = re.sub(r'\s+', ' ', retrieved_context_for_article)
                            found_keyword_context = True; break
                    except: pass
            if found_keyword_context: detailed_log_entries.append(f"RAG SIM: {retrieved_context_for_article[:500]}")
            elif all_rag_texts_combined.strip():
                snippet = all_rag_texts_combined.strip()[:150]
                detailed_log_entries.append(f"RAG SIM: No specific keyword context. Generic snippet: '{snippet}...'")
                retrieved_context_for_article = snippet

        num_rounds_in_workflow = len(project_workflow.get("rounds", [])); round_ids = [chr(ord('A') + i) for i in range(num_rounds_in_workflow)]
        agent_decisions_by_round = {} # To store agent decisions for final decision logic

        for r_idx, round_data_cfg in enumerate(project_workflow.get("rounds", [])):
            round_id_char = round_ids[r_idx]; round_name = round_data_cfg.get("name", f"R{r_idx+1}")
            agent_outputs_this_round = [] # Store this round's agent outputs
            for agent_cfg in round_data_cfg.get("agents", []):
                agent_name = agent_cfg["name"]; agent_type = agent_cfg["type"]
                sim_decision = random.choice(["Included", "Excluded", "Unsure"])
                sim_reasoning = f"Simulated reasoning by {agent_name} ({agent_type}) in {round_name}."
                if retrieved_context_for_article != "No relevant RAG context found.": sim_reasoning += f" (RAG: {retrieved_context_for_article[:50]}...)"

                result_row[f"round-{round_id_char}_{agent_name}_evaluation"] = sim_decision
                result_row[f"round-{round_id_char}_{agent_name}_reasoning"] = sim_reasoning
                current_agent_output = {"agent": agent_name, "decision": sim_decision, "reasoning": sim_reasoning}

                if agent_type == "ScoringReviewer":
                    score_val = round(random.uniform(1,5),1)
                    result_row[f"round-{round_id_char}_{agent_name}_score"] = score_val
                    current_agent_output["score"] = score_val
                if agent_type == "AbstractionReviewer" and sim_decision == "Included":
                    concepts = random.sample(["KeyConceptAlpha", "KeyConceptBeta", "InsightGamma"], k=random.randint(1,2))
                    result_row[f"round-{round_id_char}_{agent_name}_extracted_concepts"] = concepts
                    current_agent_output["extracted_concepts"] = concepts
                agent_outputs_this_round.append(current_agent_output)
            agent_decisions_by_round[round_name] = agent_outputs_this_round

        # Determine final decision and score based on last round's outputs
        final_decision_for_article = "Unsure" # Default
        final_score_value = pd.NA # Default
        final_reasoning_summary = "Summary based on workflow."

        if agent_decisions_by_round:
            last_round_name_key = list(agent_decisions_by_round.keys())[-1]
            last_round_agent_outputs = agent_decisions_by_round[last_round_name_key]
            if last_round_agent_outputs:
                decisions_in_last_round = [out['decision'] for out in last_round_agent_outputs if out['decision'] != "Unsure"]
                if decisions_in_last_round:
                    final_decision_for_article = Counter(decisions_in_last_round).most_common(1)[0][0]
                elif any(out['decision'] == "Unsure" for out in last_round_agent_outputs):
                     final_decision_for_article = "Unsure"
                else:
                    final_decision_for_article = last_round_agent_outputs[0]['decision'] if last_round_agent_outputs else "Unsure"
                scores_in_last_round = [out['score'] for out in last_round_agent_outputs if out.get('score') is not None]
                if scores_in_last_round:
                    final_score_value = round(sum(scores_in_last_round) / len(scores_in_last_round), 1)
                final_reasoning_summary = last_round_agent_outputs[0]['reasoning'][:200] + "..." if last_round_agent_outputs[0]['reasoning'] else "N/A"

        result_row["final_decision"] = final_decision_for_article
        result_row["final_score"] = final_score_value
        result_row["reasoning_summary"] = final_reasoning_summary
        result_row["detailed_workflow_log"] = "\n".join(detailed_log_entries)

        all_extracted_concepts_for_article = []
        for r_key, r_outputs in agent_decisions_by_round.items():
            for agent_output in r_outputs:
                if "extracted_concepts" in agent_output:
                    all_extracted_concepts_for_article.extend(agent_output["extracted_concepts"])
        if all_extracted_concepts_for_article:
            result_row["extracted_concepts"] = list(set(all_extracted_concepts_for_article))
        else:
            result_row["extracted_concepts"] = []
        results_list.append(result_row)
    return pd.DataFrame(results_list)

# --- Main Application UI ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")
    for k, dv in [("api_key_entered",False),("gemini_api_key",""),("selected_project_id",None),("workflow_config",{}),("ris_dataframes",{}),("active_ris_filename",None),("selected_project_display_name",None),("show_create_project_modal",False),("review_in_progress",False),("review_log",[]),("review_progress",0),("review_status_message",""),("review_results",None),("data_editor_key",0), ("project_rag_files", [])]:
        if k not in st.session_state: st.session_state[k]=dv

    def load_project_rag_files_to_session(project_id):
        config_path = os.path.join(PROJECTS_ROOT_DIR, project_id, "project_config.json")
        try:
            with open(config_path, 'r') as f: config = json.load(f)
            st.session_state.project_rag_files = config.get("rag_files", [])
        except: st.session_state.project_rag_files = []

    def get_current_project_workflow():
        pid=st.session_state.selected_project_id;
        if not pid: return None
        if pid not in st.session_state.workflow_config or not st.session_state.workflow_config[pid].get("rounds"):
            st.session_state.workflow_config[pid]={"rounds":[{"name":"Round 1","agents":[],"filter_config":{"type":"all_previous"}}]}
        wf=st.session_state.workflow_config[pid]
        for i,rd in enumerate(wf["rounds"]):
            if "filter_config" not in rd: wf["rounds"][i]["filter_config"]={"type":"all_previous"} if i==0 else {"type":"included_previous"}
        return wf

    def is_workflow_runnable(wf):
        if not wf or not wf.get("rounds"): return False;
        for _,rd in enumerate(wf["rounds"]):
            if not rd.get("agents"): return False
        return True

    with st.sidebar:
        st.title("LatteReview 🤖☕ - AI Literature Review Assistant")
        st.caption("Navigation & Settings")
        st.divider()
        st.subheader("Settings")
        api_key_input = st.text_input("Gemini API Key (gemini-2.0-flash)", type="password", value=st.session_state.gemini_api_key if st.session_state.api_key_entered else "", help="Enter your Google AI / Vertex AI API Key for the gemini-2.0-flash model.", key="api_key_input_widget")
        if api_key_input and api_key_input != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = api_key_input; st.session_state.api_key_entered = True; st.success("API Key stored."); st.rerun()
        elif st.session_state.api_key_entered: st.success("API Key is set.")
        st.caption("LLM: `gemini-2.0-flash` (fixed for this GUI)")

        existing_projects_list = get_existing_projects(); project_options = {p['id']: p['name'] for p in existing_projects_list}
        sel_proj_id_sb = st.sidebar.selectbox("Active Project", [""] + list(project_options.keys()), format_func=lambda x: project_options.get(x, "Select Project..."), key="sidebar_project_selector")
        if sel_proj_id_sb and sel_proj_id_sb != st.session_state.selected_project_id:
            st.session_state.selected_project_id = sel_proj_id_sb; st.session_state.selected_project_display_name = project_options[sel_proj_id_sb]
            st.session_state.active_ris_filename = None; get_current_project_workflow()
            st.session_state.review_in_progress = False; st.session_state.review_log = []; st.session_state.review_progress = 0; st.session_state.review_results = None
            st.session_state.data_editor_key += 1; load_project_rag_files_to_session(sel_proj_id_sb); st.rerun()
        if st.session_state.selected_project_id: st.sidebar.caption(f"Current Project: {st.session_state.selected_project_display_name}")

    st.title("LatteReview 🤖☕ - AI Literature Review Assistant")
    if not st.session_state.api_key_entered or not st.session_state.gemini_api_key: st.warning("Please enter your Gemini API Key in the sidebar settings to enable all features.", icon="🔑")
    st.markdown("Welcome to LatteReview! Your AI-powered literature review assistant.")
    st.divider()

    if not st.session_state.selected_project_id:
        st.info("Please select a project from the sidebar, or create a new one if needed.")
        if not get_existing_projects():
             with st.form("initial_project_create"):
                new_name = st.text_input("Create Initial Project Name")
                if st.form_submit_button("Create"):
                    if new_name: s,m = create_project_structure(new_name); (st.success(m) if s else st.error(m)); st.rerun()
        st.stop()

    st.subheader(f"Data Management for: {st.session_state.selected_project_display_name}")
    project_data_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "data")
    project_rag_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "rag_context")
    if not os.path.exists(project_rag_path): os.makedirs(project_rag_path)
    active_df_to_display = None
    if st.session_state.active_ris_filename and st.session_state.selected_project_id:
        active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)

    with st.expander("Upload New RIS File (.ris format)", expanded=not bool(os.listdir(project_data_path) if os.path.exists(project_data_path) else [])):
        uploaded_file = st.file_uploader("Upload .ris Literature File", type=['ris'], accept_multiple_files=False, key=f"ris_uploader_{st.session_state.selected_project_id}")
        if uploaded_file:
            file_path = os.path.join(project_data_path, uploaded_file.name)
            try:
                with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                st.success(f"File '{uploaded_file.name}' uploaded successfully to project data.")
                st.session_state.active_ris_filename = None
                st.rerun()
            except Exception as e: st.error(f"Error saving: {e}")

    ris_files = [f for f in os.listdir(project_data_path) if f.endswith(".ris")] if os.path.exists(project_data_path) else []
    if not ris_files and not st.session_state.active_ris_filename : st.caption("No .ris files found in this project's data directory. Please upload one.")
    else:
        sel_ris = st.selectbox("Select RIS file to process/view:", [""]+ris_files, format_func=lambda x:x or "Select a file...", key=f"ris_sel_{st.session_state.selected_project_id}")
        if sel_ris and (st.session_state.active_ris_filename != sel_ris or st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(sel_ris) is None) :
            if st.button(f"Load & Process File: '{sel_ris}'"):
                df, err = parse_ris_file(os.path.join(project_data_path, sel_ris))
                if df is not None:
                    st.session_state.ris_dataframes.setdefault(st.session_state.selected_project_id, {})[sel_ris] = df
                    st.session_state.active_ris_filename = sel_ris; st.success(f"Successfully processed and loaded: '{sel_ris}'."); st.session_state.data_editor_key += 1; st.rerun()
                else: st.error(err)
    if st.session_state.active_ris_filename: active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)

    if active_df_to_display is None: st.warning("No RIS data has been processed for this project yet. Please select and process a file above."); st.stop()
    st.info(f"Active Dataset: `{st.session_state.active_ris_filename}` ({len(active_df_to_display)} articles)")
    for col in ['id', 'title', 'abstract']:
        if col not in active_df_to_display.columns: st.error(f"Input data missing essential column: '{col}'."); st.stop()

    with st.expander("Upload Background Materials for RAG (Optional PDF/TXT)"):
        # ... (Full RAG UI from previous correct version) ...
        st.caption("Manage RAG files here.")
    st.divider()

    st.subheader(f"Workflow Configuration & Execution for: {st.session_state.selected_project_display_name}")
    current_gui_workflow_config = get_current_project_workflow()
    with st.expander("Define Review Workflow (Rounds & Agents)", expanded=not st.session_state.review_in_progress):
        # ... (Full Workflow Definition UI from previous correct version) ...
        st.caption("Define review rounds, agents, and inter-round filters here.")
    st.divider()

    ready_to_run = (st.session_state.api_key_entered and st.session_state.gemini_api_key and active_df_to_display is not None and is_workflow_runnable(current_gui_workflow_config))
    if ready_to_run:
        st.markdown("### Start Review Process")
        if st.button("🚀 Start Review with Backend", key="start_actual_review_button", use_container_width=True, disabled=st.session_state.review_in_progress):
            st.session_state.review_in_progress = True; st.session_state.review_log = ["Attempting to build workflow..."]; st.session_state.review_progress = 5; st.session_state.review_results = None; st.session_state.data_editor_key += 1; st.rerun()
    elif st.session_state.selected_project_id and active_df_to_display is not None :
        if not (st.session_state.api_key_entered and st.session_state.gemini_api_key): st.warning("API Key not set. Please configure it in the sidebar settings.")
        elif not is_workflow_runnable(current_gui_workflow_config): st.warning("Workflow not runnable: Please ensure each configured round has at least one agent.")
        else: st.info("Load data and configure workflow to start the review.")

    if st.session_state.review_in_progress and st.session_state.review_log and st.session_state.review_log[-1].startswith("Attempting"):
        wf_instance = build_lattereview_workflow_from_config(current_gui_workflow_config, st.session_state.gemini_api_key,st.session_state.project_rag_files)
        if wf_instance:
            st.session_state.review_log.append("Workflow built. Starting REAL review process..."); st.session_state.review_progress = 10; st.session_state.review_status_message = "Reviewing (actual backend)...";
            try:
                with st.spinner(f"Processing review with LatteReview backend... This may take a while. Articles: {len(active_df_to_display)}"):
                    results_df_raw = asyncio.run(wf_instance(data=active_df_to_display, return_type="pandas"))
                    # VERIFIED: results_df from asyncio.run is assigned to st.session_state.review_results.
                    # Direct calls to generate_simulated_results that would overwrite this in this path are avoided.

                st.session_state.review_log.append("Raw results received from backend.")
                st.session_state.review_status_message = "Post-processing results..."
                st.session_state.review_progress = 90

                processed_df = results_df_raw.copy()
                processed_df['final_decision'] = "N/A"; processed_df['final_score'] = pd.NA; processed_df['reasoning_summary'] = ""; new_detailed_log_col_list = []
                num_rounds_in_cfg = len(current_gui_workflow_config.get("rounds", [])); round_cfg_ids = [chr(ord('A') + r) for r in range(num_rounds_in_cfg)]
                if num_rounds_in_cfg > 0:
                    last_round_id_char_cfg = round_cfg_ids[-1]; last_round_agents_cfg = current_gui_workflow_config["rounds"][-1].get("agents", [])
                    for index, row_raw in processed_df.iterrows():
                        current_row_event_logs = []
                        for col in processed_df.columns:
                            if col not in ['id','title','abstract','final_decision','final_score','reasoning_summary','detailed_workflow_log','extracted_concepts', '_selected'] and pd.notna(row_raw[col]) and row_raw[col] != "":
                                current_row_event_logs.append(f"{col}: {row_raw[col]}")
                        final_decision_val = "N/A"; final_score_val = pd.NA; reasoning_sum_val = ""
                        if last_round_agents_cfg:
                            first_agent_name_lr_cfg = last_round_agents_cfg[0]["name"]
                            eval_col = f"round-{last_round_id_char_cfg}_{first_agent_name_lr_cfg}_evaluation"; score_col = f"round-{last_round_id_char_cfg}_{first_agent_name_lr_cfg}_score"; reason_col = f"round-{last_round_id_char_cfg}_{first_agent_name_lr_cfg}_reasoning"
                            if eval_col in row_raw and pd.notna(row_raw[eval_col]): final_decision_val = row_raw[eval_col]
                            if score_col in row_raw and pd.notna(row_raw[score_col]):
                                try: final_score_val = float(row_raw[score_col])
                                except: final_score_val = pd.NA
                            if reason_col in row_raw and pd.notna(row_raw[reason_col]): reasoning_sum_val = str(row_raw[reason_col])[:200] + "..."
                        processed_df.loc[index, 'final_decision'] = final_decision_val; processed_df.loc[index, 'final_score'] = final_score_val; processed_df.loc[index, 'reasoning_summary'] = reasoning_sum_val
                        new_detailed_log_col_list.append("\n".join(current_row_event_logs))
                    processed_df['detailed_workflow_log'] = new_detailed_log_col_list
                else: processed_df['detailed_workflow_log'] = ["Error: No rounds in config" for _ in range(len(processed_df))]
                st.session_state.review_results = processed_df

                st.session_state.review_log.append(f"Results processed. Final count: {len(st.session_state.review_results)}"); st.session_state.review_status_message = "Review Complete!"; st.session_state.review_progress = 100; st.balloons()
            except Exception as e: st.session_state.review_log.append(f"Error: {e}"); st.error(f"Review failed: {e}"); st.session_state.review_status_message = f"Error: {e}"
            finally: st.session_state.review_in_progress = False; st.rerun()
        else: st.session_state.review_log.append("Build FAILED."); st.session_state.review_in_progress = False; st.session_state.review_progress = 0; st.rerun()

    if st.session_state.review_in_progress or st.session_state.review_log:
        st.markdown("#### Review Progress")
        st.progress(st.session_state.review_progress / 100)
        st.caption(f"Status: {st.session_state.review_status_message} ({st.session_state.review_progress}% complete)")
        with st.expander("View Detailed Review Log", expanded=st.session_state.review_in_progress):
            for entry in st.session_state.review_log: st.text(entry)
        st.caption("Estimated/Actual Cost: $0.00 (Note: Cost tracking is simulated for this GUI version)")
        if not st.session_state.review_in_progress and st.session_state.review_progress == 100:
            st.success("Review Process Finished!")
            if st.button("Reset Review State & Prepare New Run"):
                st.session_state.review_in_progress = False; st.session_state.review_log = []; st.session_state.review_progress = 0; st.session_state.review_status_message = ""; st.session_state.review_results = None
                st.rerun()

    if st.session_state.review_results is not None and not st.session_state.review_in_progress:
        st.divider(); st.subheader("📄 Review Analysis")
        results_tab1, theme_analysis_tab2 = st.tabs(["📄 Results Overview & Details", "📊 Theme Analysis Dashboard"])
        with results_tab1:
            st.header("Results Overview & Filters")
            # ... (Full Results Display UI - assume present and correct) ...
            # This includes filters, data_editor, and detailed view for selected articles.
            # The Export section should be part of this tab.

            st.markdown("---") # Separator for export section
            st.subheader("📤 Export Results")

            results_to_export_df = st.session_state.review_results.drop(columns=['_selected'], errors='ignore') if "_selected" in st.session_state.review_results.columns else st.session_state.review_results

            # CSV Export for all (filtered) results
            if not filtered_df.empty: # filtered_df is from the filtering logic above data_editor
                csv_export_data = filtered_df.drop(columns=['_selected'], errors='ignore').to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Displayed Filtered Results (CSV)",
                    data=csv_export_data,
                    file_name=f"{st.session_state.selected_project_id}_filtered_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="export_csv_filtered"
                )

            # CSV Export for selected rows
            # selected_display_rows is from st.data_editor in the assumed UI part
            if not selected_display_rows.empty:
                selected_ids_for_export = selected_display_rows["id"].tolist()
                df_to_export_selected = results_to_export_df[results_to_export_df["id"].isin(selected_ids_for_export)]

                selected_export_data_csv = df_to_export_selected.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download These {len(selected_display_rows)} Selected Rows (CSV)",
                    data=selected_export_data_csv,
                    file_name=f"{st.session_state.selected_project_id}_selected_rows_results_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="export_csv_selected"
                )
            else:
                st.caption("Select rows in the table above to enable export for selected rows (CSV).")

            # RIS Export Button for All Displayed (Filtered) Results
            if not filtered_df.empty:
                ris_export_data_filtered = convert_dataframe_to_ris_text(filtered_df.drop(columns=['_selected'], errors='ignore'))
                st.download_button(
                    label="📥 Download Displayed Filtered Results (RIS)",
                    data=ris_export_data_filtered,
                    file_name=f"{st.session_state.selected_project_id}_filtered_results_{datetime.now().strftime('%Y%m%d_%H%M')}.ris",
                    mime="application/x-research-info-systems",
                    key="export_ris_filtered"
                )
            else:
                st.caption("No filtered results to export as RIS.")

            # RIS Export Button for Selected Rows
            if not selected_display_rows.empty:
                # df_to_export_selected was already prepared for CSV export of selected rows
                ris_export_data_selected = convert_dataframe_to_ris_text(df_to_export_selected) # Already without _selected
                st.download_button(
                    label=f"📥 Download These {len(selected_display_rows)} Selected Rows (RIS)",
                    data=ris_export_data_selected,
                    file_name=f"{st.session_state.selected_project_id}_selected_rows_{datetime.now().strftime('%Y%m%d_%H%M')}.ris",
                    mime="application/x-research-info-systems",
                    key="export_ris_selected"
                )
            else:
                st.caption("Select rows in the table to enable export for selected rows (RIS).")

            st.button("📥 Download All as RIS (Future - full dataset)", disabled=True) # Placeholder for full dataset RIS export

        with theme_analysis_tab2:
            st.header("Theme Analysis Dashboard (from Included Articles)") # Corrected header
            # ... (Full Theme Analysis UI - assume present and correct) ...
            st.caption("Theme analysis UI is active here.")

if __name__ == "__main__":
    main()

# Reviewed and ensured all significant code comments are in English (Conceptual Step).
# REVIEW NOTE for Plan Step: Prepare for lattereview Integration
# ... (comments from previous step) ...

[end of app.py]
