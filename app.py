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
# (sanitize_project_name, create_project_structure, get_existing_projects, parse_ris_file - Unchanged)
def sanitize_project_name(name):
    name = name.strip(); name = re.sub(r'[^a-zA-Z0-9_\-\s]', '', name); name = re.sub(r'\s+', '_', name)
    return name
def create_project_structure(project_name):
    # ... (implementation) ...
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
    # ... (implementation) ...
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
    # ... (implementation) ...
    try:
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


# --- TODO 5.2: Reviewer Debate Workflow - Conceptual Design ---
# Task A: Conceptual Design
# 1. Trigger: Automatically initiated for an article if agents in a designated
#    multi-agent round (e.g., a round with 2+ TitleAbstractReviewer or ScoringReviewer instances)
#    disagree on the inclusion/exclusion decision.
# 2. Participants: The agents from that round who disagreed on the specific article.
# 3. Mechanism (Simulated):
#    a. Each participating agent receives the decision and (a summary of) the
#       reasoning from the other agent(s) they disagreed with.
#    b. The agent is then prompted to re-evaluate their initial decision in light
#       of the peer feedback.
#    c. The agent provides a final stance (which could be their original decision or a changed one)
#       and a brief rebuttal or confirmation statement.
#    d. This "debate" interaction (peer feedback received, re-evaluation, final stance, rebuttal)
#       will be recorded in the article’s detailed workflow log.
# 4. Outcome: The final decisions from the debate round could then be used by a subsequent
#    expert/tie-breaker round, or a majority vote from the debate round could determine outcome.
#    (For simulation, we primarily focus on logging the debate interaction).
# 5. UI Implication (Minor consideration for TODO 5.2 Task D):
#    - No explicit UI toggle for enabling debate in this phase. It’s an implicit behavior.
#    - Future: Could add a checkbox to a round’s config: "Enable debate on disagreement".
# --- End TODO 5.2 Conceptual Design ---

def generate_simulated_results(ris_data_df, project_workflow):
    results_list = []
    if ris_data_df is None or ris_data_df.empty or 'id' not in ris_data_df.columns: return pd.DataFrame()

    has_scorer_in_workflow = any(a.get("type") == "ScoringReviewer" for r in project_workflow.get("rounds", []) for a in r.get("agents", []))

    for index, row in ris_data_df.iterrows():
        article_id = row['id']; title = row.get('title', f"Unknown Title for {article_id}"); abstract = row.get('abstract', "N/A")

        article_decisions_by_round = {} # Store decisions for potential debate
        detailed_log_entries = []

        # Simulate initial rounds
        for r_idx, round_data in enumerate(project_workflow.get("rounds", [])):
            round_name = round_data.get("name", f"Round {r_idx+1}")
            agent_decisions_this_round = []

            for a_idx, agent_data in enumerate(round_data.get("agents", [])):
                agent_name = agent_data.get("name", f"Agent {a_idx+1}")
                # Simulate individual agent decision
                current_agent_decision = random.choice(["Included", "Excluded", "Unsure"])
                agent_reasoning = f"Simulated reasoning by {agent_name} for {title[:20]}... decided {current_agent_decision}."
                detailed_log_entries.append(f"**{round_name} - {agent_name}**: Decided '{current_agent_decision}'. Justification: {agent_reasoning}")
                agent_decisions_this_round.append({"agent": agent_name, "decision": current_agent_decision, "reasoning": agent_reasoning})

            article_decisions_by_round[round_name] = agent_decisions_this_round

            # TODO 5.2 B & C: Simulate Debate Round if applicable and log it
            # For this simulation, let's assume a debate happens if the *first configured round* has >=2 agents and they disagree.
            if r_idx == 0 and len(agent_decisions_this_round) >= 2: # Assuming first round is the potential debate round
                decisions_set = {d["decision"] for d in agent_decisions_this_round}
                # Disagreement if more than one unique decision (excluding "Unsure" for simplicity of debate trigger)
                if len({d for d in decisions_set if d != "Unsure"}) > 1:
                    detailed_log_entries.append(f"**{round_name} - DEBATE TRIGGERED** due to disagreement.")

                    # Simulate each agent in the debate responding to others
                    for debater_idx, debater_decision_info in enumerate(agent_decisions_this_round):
                        debater_name = debater_decision_info["agent"]
                        original_debater_decision = debater_decision_info["decision"]

                        # Collate peer feedback for this debater
                        peer_feedback_summary = []
                        for peer_idx, peer_decision_info in enumerate(agent_decisions_this_round):
                            if peer_idx != debater_idx: # Don't give agent its own feedback
                                peer_feedback_summary.append(f"Peer {peer_decision_info['agent']} decided '{peer_decision_info['decision']}' because '{peer_decision_info['reasoning'][:50]}...'")

                        feedback_str = "; ".join(peer_feedback_summary) if peer_feedback_summary else "No differing peer feedback."

                        # Simulate re-evaluation and final stance
                        final_stance = original_debater_decision # Agent might stick to their guns
                        rebuttal = "After reviewing peer feedback, I maintain my original assessment."
                        if random.random() < 0.3: # 30% chance agent changes mind
                            # Ensure the new decision is different from the original if possible
                            possible_new_decisions = [d for d in ["Included", "Excluded"] if d != original_debater_decision]
                            final_stance = random.choice(possible_new_decisions) if possible_new_decisions else original_debater_decision
                            rebuttal = f"Having considered peer feedback, I've revised my stance to '{final_stance}'."

                        detailed_log_entries.append(
                            f"**{round_name} - DEBATE - {debater_name}**: "
                            f"Received peer feedback: [{feedback_str}]. "
                            f"Original decision: '{original_debater_decision}'. "
                            f"Re-evaluated. Final Stance: '{final_stance}'. Rebuttal: {rebuttal}"
                        )
                        # Update this agent's decision for this round if it changed during debate
                        # This is for logging; the actual 'final_decision_for_article' below will determine the article's fate
                        agent_decisions_this_round[debater_idx]["decision_after_debate"] = final_stance
                        agent_decisions_this_round[debater_idx]["reasoning"] += f" | DEBATE FINALIZED ({final_stance}): {rebuttal}"


        # Determine overall "Final Decision" for the article (e.g., from last round's consensus or first agent)
        final_decision_for_article = "Unsure"
        if article_decisions_by_round:
            last_round_name = list(article_decisions_by_round.keys())[-1]
            last_round_decisions_info = article_decisions_by_round[last_round_name]

            # If a debate happened in the first round, its outcome might influence this final decision
            # For simplicity, we'll use the (potentially updated) decisions from the last round simulated.
            # If a debate happened, agent_decisions_this_round (for r_idx==0) would have updated decisions.

            final_decisions_from_last_round = [d.get("decision_after_debate", d["decision"]) for d in last_round_decisions_info]

            if final_decisions_from_last_round:
                # Simple consensus: most common decision (excluding "Unsure" if others exist)
                decision_counts = Counter(d for d in final_decisions_from_last_round if d != "Unsure")
                if decision_counts:
                    final_decision_for_article = decision_counts.most_common(1)[0][0]
                elif "Unsure" in final_decisions_from_last_round: # All were "Unsure" or became "Unsure"
                    final_decision_for_article = "Unsure"
                else: # Fallback if list was empty after filtering Unsure (should not happen if agents exist)
                    final_decision_for_article = final_decisions_from_last_round[0]


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
            "Detailed Workflow Log": "\n\n".join(detailed_log_entries), # Use double newline for readability
            "Extracted Concepts": extracted_concepts if extracted_concepts else []
        })
    return pd.DataFrame(results_list)

def execute_review_workflow_stub(project_workflow, ris_data_df): # Unchanged structure, but uses updated generate_simulated_results
    st.session_state.review_log.append("Starting review (sim)..."); st.session_state.review_status_message = "Initializing..."; st.session_state.review_results = None
    # ... (simulation loop for progress bar - unchanged) ...
    st.session_state.review_results = generate_simulated_results(ris_data_df, project_workflow)
    st.session_state.review_log.append("Review (sim) completed!"); st.session_state.review_status_message = "Sim Complete! Results ready."
    st.session_state.review_progress = 100; st.session_state.review_in_progress = False

# --- Main Application UI ---
def main():
    # ... (Session state init, helper functions, Sidebar, Title, Project/Data Management - condensed for brevity) ...
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

    with st.sidebar: st.title("LatteReview Settings")
    st.title("LatteReview 🤖☕")
    if not st.session_state.selected_project_id: st.info("Select/create project."); st.stop()
    active_df_to_display = None
    if st.session_state.active_ris_filename and st.session_state.selected_project_id:
        active_df_to_display = st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)
    if active_df_to_display is None: st.warning("No RIS data processed."); st.stop()

    st.subheader(f"Workflow & Execution")
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

        with results_tab1:
            st.header("Results Overview & Details")
            results_df = st.session_state.review_results.copy()
            if "_selected" not in results_df.columns: results_df.insert(0, "_selected", False)

            # Filters (condensed)
            # ... (Assume filtering UI is present and functional) ...

            st.info(f"Displaying {len(results_df)} results (filtering UI condensed).") # Simplified

            editor_key = f"data_editor_tab_{st.session_state.selected_project_id}_{st.session_state.active_ris_filename}_{st.session_state.data_editor_key}"
            disp_cols = ["_selected", "Article ID", "Title", "Final Decision", "Avg Score"]
            final_disp_cols = [c for c in disp_cols if c in results_df.columns]

            edited_display_df = st.data_editor(results_df[final_disp_cols] if final_disp_cols else results_df, key=editor_key, hide_index=True, num_rows="dynamic", disabled=[c for c in final_disp_cols if c != "_selected"])
            selected_display_rows = edited_display_df[edited_display_df["_selected"]]

            # Detailed View (TODO 4.3 - updated to show the new 'Detailed Workflow Log')
            if not selected_display_rows.empty:
                st.markdown("---"); st.subheader("Selected Article Details")
                selected_article_ids = selected_display_rows["Article ID"].tolist()
                selected_original_rows = st.session_state.review_results[st.session_state.review_results["Article ID"].isin(selected_article_ids)]

                for _, orig_row in selected_original_rows.iterrows():
                    st.markdown(f"#### {orig_row.get('Title', 'N/A')}")
                    st.caption(f"ID: {orig_row.get('Article ID', 'N/A')}")
                    # ... (metrics for decision/score) ...
                    with st.expander("View Abstract", expanded=False):
                        st.markdown(orig_row.get('Abstract', "No abstract available."))
                    with st.expander("View Reasoning Summary", expanded=False):
                        st.markdown(orig_row.get('Reasoning Summary', "No summary available."))
                    with st.expander("View Detailed Workflow Log (includes simulated debate)", expanded=True): # Expanded by default now
                        # Use st.text for preformatted-like display if the log has newlines
                        st.text(orig_row.get('Detailed Workflow Log', "No detailed log available."))
                    st.markdown("---")

            # ... (Export Functionality - assume present) ...


        with theme_analysis_tab2:
            # ... (Theme Analysis Dashboard code - assume present and functional) ...
            st.header("Theme Analysis Dashboard")
            st.caption("Theme analysis: concept frequencies and word cloud.")


if __name__ == "__main__":
    main()
