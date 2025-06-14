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

# --- Helper Functions (Assume complete and correct from previous versions) ---
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
    proj_list = []
    for item in os.listdir(PROJECTS_ROOT_DIR): # Simplified - real version has more error handling
        if os.path.isdir(os.path.join(PROJECTS_ROOT_DIR, item)):
             proj_list.append({"id": item, "name": item, "rag_files": []})
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

# --- Workflow Construction (build_lattereview_workflow_from_config - Assumed complete) ---
def build_lattereview_workflow_from_config(gui_workflow_config, api_key, project_rag_files): # Simplified
    class DummyWorkflow: # Returns a callable dummy for testing
        async def __call__(self, data, return_type):
            return generate_simulated_results(data, gui_workflow_config, project_rag_files)
    return DummyWorkflow()

# --- generate_simulated_results (MODIFIED with Keyword RAG Retrieval) ---
def generate_simulated_results(ris_data_df, project_workflow, rag_files_info): # rag_files_info is list of filenames
    results_list = []
    if ris_data_df is None or ris_data_df.empty or 'id' not in ris_data_df.columns: return pd.DataFrame()

    all_rag_texts_combined = ""
    rag_file_names_from_info = [info if isinstance(info, str) else info.get("name") for info in rag_files_info if info]

    if rag_file_names_from_info and st.session_state.get("selected_project_id"): # Check if selected_project_id exists
        project_rag_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "rag_context")
        for rag_filename in rag_file_names_from_info:
            full_rag_path = os.path.join(project_rag_path, rag_filename)
            if os.path.exists(full_rag_path):
                extracted_content = extract_text_from_rag_document(full_rag_path)
                if extracted_content: all_rag_texts_combined += extracted_content + "\n\n---RAG DOC SEPARATOR---\n\n"
            # else:
                # st.warning(f"RAG file {rag_filename} not found at {full_rag_path} during simulation.")

    stopwords = ["a", "an", "the", "is", "are", "of", "in", "on", "and", "for", "to", "with", "by", "or", "as", "at", "but", "it", "if"]


    for index, row in ris_data_df.iterrows():
        article_id = row['id']; title = row.get('title',""); abstract = row.get('abstract',"")
        result_row = {"id": article_id, "title": title, "abstract": abstract}
        detailed_log_entries = []

        retrieved_context_for_article = "No relevant RAG context found." # Default
        if rag_file_names_from_info and all_rag_texts_combined.strip():
            article_title_for_keywords = title.lower()
            title_words = [word for word in re.split(r'\W+', article_title_for_keywords) if word and word not in stopwords and len(word)>2]
            keywords_to_search = title_words[:2] # Take up to 2 significant keywords

            found_keyword_context = False
            if keywords_to_search:
                for keyword in keywords_to_search:
                    try:
                        match_iter = re.finditer(r'\b' + re.escape(keyword) + r'\b', all_rag_texts_combined, re.IGNORECASE)
                        first_match = next(match_iter, None)
                        if first_match:
                            match_pos = first_match.start(); context_window = 100 # characters around keyword
                            start_snip = max(0, match_pos - context_window)
                            end_snip = min(len(all_rag_texts_combined), match_pos + len(keyword) + context_window)
                            retrieved_context_for_article = f"Context for '{keyword}': ...{all_rag_texts_combined[start_snip:end_snip].strip()}..."
                            retrieved_context_for_article = re.sub(r'\s+', ' ', retrieved_context_for_article) # Clean whitespace
                            found_keyword_context = True; break
                    except: pass # Ignore regex errors on specific keywords

            if found_keyword_context:
                 detailed_log_entries.append(f"RAG SIM: {retrieved_context_for_article[:500]}") # Log up to 500 chars
            elif all_rag_texts_combined.strip():
                detailed_log_entries.append(f"RAG SIM: No specific keyword context found for title keywords. General RAG background considered (first 150 chars shown): '{all_rag_texts_combined[:150].strip()}...'")
                retrieved_context_for_article = all_rag_texts_combined.strip()[:150] # Fallback to generic snippet
        elif rag_file_names_from_info :
             detailed_log_entries.append(f"RAG SIM: RAG files listed, but no text content was loaded from them.")
        # else: No RAG files configured / no st.session_state.selected_project_id to find them

        # Simulate Rounds, Agents, etc.
        agent_example_log = f"AgentFoo processed article."
        if retrieved_context_for_article != "No relevant RAG context found.":
            agent_example_log += f" (Used RAG: {retrieved_context_for_article[:70]}...)"
        detailed_log_entries.append(agent_example_log)
        # ... (rest of the result row population as before) ...
        result_row["final_decision"] = random.choice(["Included", "Excluded"])
        result_row["detailed_workflow_log"] = "\n".join(detailed_log_entries)
        results_list.append(result_row)

    return pd.DataFrame(results_list)

# --- Main UI (Simplified for test focus) ---
def main():
    st.set_page_config(page_title="LatteReview RAG Test", layout="wide")
    # Init session state (simplified)
    for k, dv in [("selected_project_id",None), ("project_rag_files",[]), ("review_results",None)]:
        if k not in st.session_state: st.session_state[k]=dv

    if st.session_state.selected_project_id is None: # Setup a dummy project for testing
        st.session_state.selected_project_id = "test_rag_proj"
        p_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "rag_context")
        if not os.path.exists(p_path): os.makedirs(p_path, exist_ok=True)
        # Create a dummy RAG file for testing
        dummy_rag_file_path = os.path.join(p_path, "my_research_notes.txt")
        if not os.path.exists(dummy_rag_file_path):
            with open(dummy_rag_file_path, "w") as f:
                f.write("This document discusses AI in radiology. Another important topic is deep learning for cancer detection. We also focus on patient outcomes.")
            st.session_state.project_rag_files = ["my_research_notes.txt"]


    st.title("Test RAG Snippet Retrieval")
    st.write(f"Project: {st.session_state.selected_project_id}")
    st.write(f"RAG Files: {st.session_state.project_rag_files}")

    mock_df = pd.DataFrame({
        'id': ['art1', 'art2', 'art3'],
        'title': ['AI in Medicine', 'Cancer Diagnosis with Deep Learning', 'Exploring Patient Outcomes'],
        'abstract': ['Ab1', 'Ab2', 'Ab3']
    })
    mock_workflow = {"rounds": [{"name":"R1", "agents":[{"name":"A1", "type":"TitleAbstractReviewer"}]}]}

    if st.button("Generate Simulated Results with Enhanced RAG"):
        st.session_state.review_results = generate_simulated_results(mock_df, mock_workflow, st.session_state.project_rag_files)

    if st.session_state.review_results is not None:
        st.subheader("Results (note 'detailed_workflow_log' for RAG info):")
        st.dataframe(st.session_state.review_results[["id", "title", "detailed_workflow_log"]])

if __name__ == "__main__":
    main()
