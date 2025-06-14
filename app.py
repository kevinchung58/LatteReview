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
from pyvis.network import Network # For Concept Network Graph
from itertools import combinations # For Concept Network Graph edge generation
import asyncio
import nest_asyncio
nest_asyncio.apply()

PROJECTS_ROOT_DIR = "lattereview_projects"
AGENT_TYPES_MAP = {"TitleAbstractReviewer": TitleAbstractReviewer, "ScoringReviewer": ScoringReviewer, "AbstractionReviewer": AbstractionReviewer}
AGENT_TYPE_NAMES = list(AGENT_TYPES_MAP.keys())

# --- Helper Functions (Assume complete and correct from previous versions) ---
def sanitize_project_name(name): return re.sub(r'\s+', '_', re.sub(r'[^a-zA-Z0-9_\-\s]', '', name.strip()))
def create_project_structure(project_name): # Simplified
    s_name=sanitize_project_name(project_name); p_path=os.path.join(PROJECTS_ROOT_DIR,s_name)
    if not s_name or os.path.exists(p_path): return False, "Error"
    try:
        for sub_dir in ["", "data", "results", "rag_context"]: os.makedirs(os.path.join(p_path, sub_dir), exist_ok=True)
        with open(os.path.join(p_path, "project_config.json"),'w') as f: json.dump({"project_name":project_name,"sanitized_name":s_name,"created_at":datetime.now().isoformat(),"rag_files":[]},f,indent=2)
        return True, "Project created."
    except: return False, "Error"
def get_existing_projects(): return [{"id": "sample_project", "name": "Sample Project", "rag_files": []}] # Dummy
def update_project_rag_files(project_id, rag_file_names): return True
def parse_ris_file(file_path): # Simplified
    try: df = pd.DataFrame({'id':['art1','art2'],'title':['Title1','Title2'],'abstract':['Abs1','Abs2']}); return df, None
    except Exception as e: return None, f"Parse Error: {e}"
def extract_text_from_rag_document(file_path): return "Sample RAG text..." # Simplified

def build_lattereview_workflow_from_config(gui_workflow_config, api_key, project_rag_files): # Simplified
    class DummyWorkflow: # Returns a callable dummy for testing
        async def __call__(self, data, return_type):
            return generate_simulated_results(data, gui_workflow_config, project_rag_files)
    return DummyWorkflow()

def generate_simulated_results(ris_data_df, project_workflow, rag_files_info): # Assumed complete from previous steps
    results_list = [] # Simplified for focus
    if ris_data_df is None or ris_data_df.empty: return pd.DataFrame()
    for idx, row in ris_data_df.iterrows():
        # Create a row with id, title, abstract, final_decision, and round-X_Agent_extracted_concepts
        res = {"id": row.get("id",f"art{idx}"), "title": row.get("title", f"Title {idx}"), "abstract": row.get("abstract", f"Abs {idx}")}
        res["final_decision"] = random.choice(["Included", "Excluded"])
        # Simulate AbstractionReviewer output for included items
        if res["final_decision"] == "Included":
            concepts = random.sample(["AI", "Healthcare", "Deep Learning", "Radiology", "Cancer", "Ethics"], k=random.randint(2,4))
            # Assume one AbstractionReviewer named "AbsAgent" in first round 'A'
            res["round-A_AbsAgent_extracted_concepts"] = concepts
        results_list.append(res)
    return pd.DataFrame(results_list)

# --- Main Application UI ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")
    # Session state init
    for k, dv in [("api_key_entered",True),("gemini_api_key","test_key"),("selected_project_id",None),("workflow_config",{}),("ris_dataframes",{}),("active_ris_filename",None),("selected_project_display_name",None),("review_in_progress",False),("review_results",None),("data_editor_key",0), ("project_rag_files", []), ("generated_graph_html_path", None)]: # Added generated_graph_html_path
        if k not in st.session_state: st.session_state[k]=dv

    # Simplified Project & Data Setup for focused testing
    if st.session_state.selected_project_id is None:
        st.session_state.selected_project_id = "sample_project"
        st.session_state.selected_project_display_name = "Sample Project"
        if st.session_state.selected_project_id not in st.session_state.ris_dataframes:
            st.session_state.ris_dataframes[st.session_state.selected_project_id] = {"sample.ris": pd.DataFrame({'id': [f'Art{i}' for i in range(10)], 'title': [f'Sample Title {i}' for i in range(10)], 'abstract': [f'Abstract {i}' for i in range(10)]})}
            st.session_state.active_ris_filename = "sample.ris"
        if st.session_state.selected_project_id not in st.session_state.workflow_config: # Ensure workflow for AbsAgent
             st.session_state.workflow_config[st.session_state.selected_project_id] = {"rounds": [{"name": "R1", "agents": [{"name": "AbsAgent", "type": "AbstractionReviewer", "incl_crit":"Focus on AI."}]}]}


    active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)
    current_gui_workflow_config = st.session_state.workflow_config.get(st.session_state.selected_project_id)

    st.title("LatteReview 🤖☕ - Concept Network Graph Test")

    if st.session_state.review_results is None: # Simulate review run if no results yet
        if active_df_to_display is not None and current_gui_workflow_config is not None:
            wf_instance = build_lattereview_workflow_from_config(current_gui_workflow_config, "test_key", [])
            if wf_instance:
                 st.session_state.review_results = asyncio.run(wf_instance(data=active_df_to_display, return_type="pandas"))
                 st.success("Simulated review results generated for testing.")
        else: st.error("Could not generate test results."); st.stop()
    if st.session_state.review_results is None: st.error("Results still none"); st.stop()


    # --- Results Display Section ---
    st.divider(); st.subheader("📄 Review Analysis")
    results_tab1, theme_analysis_tab2 = st.tabs(["Results Overview & Details", "Theme Analysis Dashboard"])

    with results_tab1: st.header("Results Overview (Simplified)") # Placeholder

    with theme_analysis_tab2:
        st.header("Theme Analysis Dashboard")
        if st.session_state.review_results.empty: st.info("No results."); st.stop()

        included_articles_df = st.session_state.review_results[st.session_state.review_results.get("final_decision", pd.Series(dtype=str)) == "Included"]
        all_concepts = [] # From previous logic: aggregate from concept columns
        concept_columns_for_graph = [col for col in included_articles_df.columns if "extracted_concepts" in col.lower()]
        if concept_columns_for_graph:
            for _, row_concepts in included_articles_df.iterrows():
                for col_concepts in concept_columns_for_graph:
                    concept_list_val = row_concepts.get(col_concepts)
                    if isinstance(concept_list_val, list): all_concepts.extend(concept_list_val)

        if not all_concepts: st.info("No concepts found for analysis.")
        else:
            # ... (Concept Freq Table & Chart - Assume present) ...
            # ... (Word Cloud - Assume present) ...
            st.markdown("---"); st.write("#### Concept Network Graph (Co-occurrence based)")
            try:
                # Graph generation logic
                concept_co_occurrence = Counter()
                article_concept_sets = []
                if concept_columns_for_graph:
                    for index, row_graph in included_articles_df.iterrows():
                        article_specific_concepts = set()
                        for col_graph in concept_columns_for_graph:
                            concepts_in_col = row_graph.get(col_graph)
                            if isinstance(concepts_in_col, list): article_specific_concepts.update(concepts_in_col)
                        if article_specific_concepts and len(article_specific_concepts) > 1: article_concept_sets.append(list(article_specific_concepts))

                if article_concept_sets:
                    for concept_set_graph in article_concept_sets:
                        # Create combinations of 2 from the sorted unique concepts in this article
                        unique_concepts_in_set = sorted(list(set(concept_set_graph)))
                        for c1, c2 in combinations(unique_concepts_in_set, 2):
                            concept_co_occurrence[tuple(sorted((c1, c2)))] += 1 # Store pair alphabetically

                if concept_co_occurrence:
                    net = Network(notebook=True, height="700px", width="100%", cdn_resources='remote', directed=False, select_menu=True, filter_menu=True)
                    net.repulsion(node_distance=150, spring_length=200) # Adjust physics for better layout

                    # Add nodes with size based on overall frequency
                    concept_overall_freq = Counter(all_concepts)
                    for node_c, freq in concept_overall_freq.items():
                        net.add_node(str(node_c), label=str(node_c), value=freq, title=f"{node_c} (Frequency: {freq})") # Size by freq

                    for edge_g, weight_g in concept_co_occurrence.items():
                        if weight_g > 0: # Add edge only if there is co-occurrence
                           net.add_edge(str(edge_g[0]), str(edge_g[1]), value=weight_g, title=f"Co-occurrences: {weight_g}")

                    project_results_path = os.path.join(PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "results")
                    if not os.path.exists(project_results_path): os.makedirs(project_results_path, exist_ok=True)
                    graph_html_path = os.path.join(project_results_path, "concept_network.html")

                    try:
                        net.save_graph(graph_html_path)
                        st.session_state.generated_graph_html_path = graph_html_path
                    except Exception as e_save:
                        st.error(f"Error saving graph HTML: {e_save}")
                        st.session_state.generated_graph_html_path = None

                else:
                    st.caption("No significant co-occurrences (pairs of concepts) found in the included articles to build a network graph.")
                    st.session_state.generated_graph_html_path = None # Ensure no old graph is shown

                # Display logic using st.components.v1.html
                if st.session_state.get("generated_graph_html_path") and os.path.exists(st.session_state.generated_graph_html_path):
                    try:
                        with open(st.session_state.generated_graph_html_path, 'r', encoding='utf-8') as f_html:
                            source_code = f_html.read()
                        st.components.v1.html(source_code, height=750, scrolling=True)
                        st.caption("Interactive concept network. Drag nodes, zoom. Node size by frequency, edge width by co-occurrence.")
                    except Exception as e_display_graph:
                        st.error(f"Could not display concept network graph: {e_display_graph}")
                elif concept_co_occurrence:
                     st.warning("Graph generated but HTML file not found or path issue.")
            except ImportError: st.error("Pyvis library needed for network graph. Please install it.")
            except Exception as e_main_graph: st.error(f"Error during graph generation or display: {e_main_graph}")


if __name__ == "__main__":
    main()
