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
from wordcloud import WordCloud # For TODO 5.1 B
import matplotlib.pyplot as plt # For displaying wordcloud

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

def create_project_structure(project_name): # Unchanged
    sanitized_name = sanitize_project_name(project_name)
    if not sanitized_name: return False, "Invalid project name."
    project_path = os.path.join(PROJECTS_ROOT_DIR, sanitized_name)
    if os.path.exists(project_path): return False, f"Project '{sanitized_name}' already exists."
    try:
        os.makedirs(project_path); os.makedirs(os.path.join(project_path, "data")); os.makedirs(os.path.join(project_path, "results"))
        ct = datetime.now().isoformat()
        with open(os.path.join(project_path, "project_config.json"), 'w') as f: json.dump({"project_name": project_name, "sanitized_name": sanitized_name, "created_at": ct}, f, indent=2)
        return True, f"Project '{project_name}' created."
    except OSError as e: return False, f"Error: {e}"

def get_existing_projects(): # Unchanged
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

def parse_ris_file(file_path): # Unchanged
    try:
        df = data_handler.RISHandler().load_ris_file_to_dataframe(file_path)
        if 'title' not in df.columns and ('TI' in df.columns or 'primary_title' in df.columns):
            df = df.rename(columns={'TI': 'title', 'primary_title': 'title'}, errors='ignore')
        if 'id' not in df.columns:
            for id_col in ['ID', 'AN', 'UT']: # Common ID fields
                if id_col in df.columns: df = df.rename(columns={id_col: 'id'}, errors='ignore'); break
            if 'id' not in df.columns: df['id'] = [f"Art{i}" for i in range(len(df))]
        if 'abstract' not in df.columns and 'AB' in df.columns: df = df.rename(columns={'AB': 'abstract'}, errors='ignore')
        return df, None
    except Exception as e: return None, f"Error parsing '{os.path.basename(file_path)}': {e}"

def generate_simulated_results(ris_data_df, project_workflow): # Unchanged (already adds concepts)
    results_list = []
    if ris_data_df is None or ris_data_df.empty or 'id' not in ris_data_df.columns: return pd.DataFrame()
    has_scorer = any(a.get("type") == "ScoringReviewer" for r in project_workflow.get("rounds", []) for a in r.get("agents", []))
    for index, row in ris_data_df.iterrows():
        article_id = row['id']; title = row.get('title', f"Unknown Title for {article_id}"); abstract = row.get('abstract', "N/A")
        decision = random.choice(["Included", "Excluded", "Unsure"]); score = round(random.uniform(1.0, 5.0),1) if has_scorer else "N/A"
        summary = f"Simulated summary for '{title[:30]}...'"; detailed_log = ""
        for r_idx, r_data in enumerate(project_workflow.get("rounds",[])):
            for a_idx, a_data in enumerate(r_data.get("agents",[])): detailed_log += f"R{r_idx+1}-{a_data.get('name')}: ...\n"
        extracted_concepts = []
        if decision == "Included":
            base_concepts = ["AI", "Machine Learning", "Healthcare", "Diagnostics", "Treatment", "Clinical Trials", "Radiology", "Pathology", "Genomics", "Drug Discovery", "Literature Review", "Systematic Review", "Meta-Analysis"]
            extracted_concepts = random.sample(base_concepts, k=random.randint(2,6))
            if "AI" in extracted_concepts and random.random() > 0.6: extracted_concepts.append("Deep Learning")
            if "Healthcare" in extracted_concepts and random.random() > 0.6: extracted_concepts.append("Patient Outcomes")
            if "Radiology" in extracted_concepts and random.random() > 0.5: extracted_concepts.append("Medical Imaging")
        results_list.append({"Article ID": article_id, "Title": title, "Abstract": abstract, "Final Decision": decision, "Avg Score": score, "Reasoning Summary": summary, "Detailed Workflow Log": detailed_log.strip(), "Extracted Concepts": extracted_concepts if extracted_concepts else [] })
    return pd.DataFrame(results_list)

def execute_review_workflow_stub(project_workflow, ris_data_df): # Unchanged
    st.session_state.review_log.append("Starting review (sim)..."); st.session_state.review_status_message = "Initializing..."; st.session_state.review_results = None
    # ... (simulation logic) ...
    st.session_state.review_results = generate_simulated_results(ris_data_df, project_workflow)
    st.session_state.review_log.append("Review (sim) completed!"); st.session_state.review_status_message = "Sim Complete! Results ready."
    st.session_state.review_progress = 100; st.session_state.review_in_progress = False


# --- Main Application UI ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")
    for k, dv in [("api_key_entered",False),("gemini_api_key",""),("selected_project_id",None),("workflow_config",{}),("ris_dataframes",{}),("active_ris_filename",None),("selected_project_display_name",None),("show_create_project_modal",False),("review_in_progress",False),("review_log",[]),("review_progress",0),("review_status_message",""),("review_results",None),("data_editor_key",0)]:
        if k not in st.session_state: st.session_state[k]=dv

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
    # ... (Assume these sections are present and functional) ...
    with st.sidebar: st.title("LatteReview Settings") # Simplified
    st.title("LatteReview 🤖☕")
    if not st.session_state.selected_project_id: st.info("Select/create project."); st.stop()
    active_df_to_display = None
    if st.session_state.active_ris_filename and st.session_state.selected_project_id:
        active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)
    if active_df_to_display is None: st.warning("No RIS data processed."); st.stop()

    # Workflow Config & Execution (condensed)
    # ... (Assume this section is present and functional) ...
    st.subheader(f"Workflow & Execution") # Simplified
    current_workflow = get_current_project_workflow()
    if (st.session_state.api_key_entered and active_df_to_display is not None and is_workflow_runnable(current_workflow)):
        if st.button("🚀 Start Review (Sim)", disabled=st.session_state.review_in_progress):
             st.session_state.review_in_progress=True; st.session_state.review_log=[]; st.session_state.review_progress=0
             execute_review_workflow_stub(current_workflow, active_df_to_display); st.session_state.data_editor_key+=1; st.rerun()
    if st.session_state.review_in_progress or st.session_state.review_progress==100: st.caption(f"Progress: {st.session_state.review_progress}%")


    # --- Results Display Section ---
    if st.session_state.review_results is not None and not st.session_state.review_in_progress:
        st.divider(); st.subheader("📄 Review Analysis")
        results_tab1, theme_analysis_tab2 = st.tabs(["Results Overview & Details", "Theme Analysis Dashboard"])

        with results_tab1: # Results Overview & Details
            # ... (Results overview, filtering, details, export - assume present from previous steps) ...
            st.header("Results Overview")
            st.caption("Detailed results, filtering, and export options are available here.")


        with theme_analysis_tab2: # Theme Analysis Dashboard
            st.header("Theme Analysis Dashboard")

            if st.session_state.review_results is None or st.session_state.review_results.empty:
                st.info("No review results available to analyze themes. Please run a review.")
                st.stop()

            included_articles_df = st.session_state.review_results[
                st.session_state.review_results["Final Decision"] == "Included"
            ]

            all_concepts = []
            if "Extracted Concepts" in included_articles_df.columns:
                for concept_list in included_articles_df["Extracted Concepts"].dropna():
                    if isinstance(concept_list, list): all_concepts.extend(concept_list)

            if not all_concepts:
                st.info("No concepts found in included articles for theme analysis.")
            else:
                # Concept Aggregation (TODO 5.1 A - Done)
                st.markdown("#### Top Extracted Concepts (from Included Articles)")
                concept_counts = Counter(all_concepts)
                common_concepts_df = pd.DataFrame(concept_counts.most_common(15), columns=['Concept', 'Frequency']) # Show more concepts
                col1_concepts, col2_concepts = st.columns(2)
                with col1_concepts:
                    st.write("Frequency Table:"); st.dataframe(common_concepts_df, use_container_width=True)
                with col2_concepts:
                    if not common_concepts_df.empty:
                        st.write("Frequency Chart:"); common_concepts_df['Concept'] = common_concepts_df['Concept'].astype(str)
                        st.bar_chart(common_concepts_df.set_index('Concept'), height=350)
                st.markdown("---")

                # Word Cloud (TODO 5.1 B)
                st.write("#### Word Cloud of Extracted Concepts")
                try:
                    # Join all concepts into a single string
                    text_for_wordcloud = " ".join(all_concepts)
                    if text_for_wordcloud:
                        # Generate WordCloud object
                        # Added common English stopwords to make the cloud more meaningful
                        # Can customize width, height, background_color, collocations, etc.
                        stopwords = set(["and", "or", "the", "of", "in", "to", "a", "is", "for", "on", "with", "as", "by", "an"]) # Basic stopwords
                        wordcloud_img = WordCloud(
                            width=800, height=300,
                            background_color='white',
                            stopwords=stopwords,
                            min_font_size=10,
                            collocations=True # Allow collocations (multi-word phrases if they appear together often)
                        ).generate(text_for_wordcloud)

                        fig, ax = plt.subplots(figsize=(12,4)) # Adjust figure size for better layout
                        ax.imshow(wordcloud_img, interpolation='bilinear')
                        ax.axis("off")
                        st.pyplot(fig, use_container_width=True) # Make it responsive
                    else:
                        st.caption("Not enough concept data to generate a word cloud.")
                except ImportError:
                    st.error("WordCloud or Matplotlib library not found. Please ensure they are installed.")
                except Exception as e:
                    st.error(f"Could not generate word cloud: {e}")


            st.markdown("---")
            st.write("#### Concept Network Graph (Placeholder - TODO 5.1 C)")
            st.caption("Concept network graph (pyvis/plotly) coming soon.")


if __name__ == "__main__":
    main()
