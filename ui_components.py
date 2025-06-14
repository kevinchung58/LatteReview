import streamlit as st
import os
import pandas as pd
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from pyvis.network import Network
from itertools import combinations
from datetime import datetime

# Import the utility module that contains non-UI helper functions
import gui_utils

# AGENT_TYPE_NAMES for selectboxes. Sourced from gui_utils.
try:
    AGENT_TYPE_NAMES = list(gui_utils.AGENT_TYPES_MAP.keys())
except AttributeError:
    AGENT_TYPE_NAMES = ["TitleAbstractReviewer", "ScoringReviewer", "AbstractionReviewer"] # Fallback

# --- UI Rendering Functions ---

def render_sidebar():
    with st.sidebar:
        st.title("LatteReview Settings")
        api_key_input = st.text_input("Gemini API Key (gemini-2.0-flash)", type="password",
                                      value=st.session_state.gemini_api_key if st.session_state.api_key_entered else "",
                                      help="Enter your Google AI / Vertex AI API Key for the gemini-2.0-flash model.",
                                      key="api_key_input_widget")
        if api_key_input and api_key_input != st.session_state.gemini_api_key:
            st.session_state.gemini_api_key = api_key_input
            st.session_state.api_key_entered = True
            st.success("API Key stored.")
            st.rerun()
        elif st.session_state.api_key_entered:
            st.success("API Key is set.")
        st.caption("LLM: `gemini-2.0-flash` (fixed for this GUI)")

        st.divider()
        st.subheader("Project Selection")
        existing_projects_list = gui_utils.get_existing_projects()
        project_options = {proj['id']: proj['name'] for proj in existing_projects_list}

        selected_proj_id_sidebar = st.selectbox("Active Project", options=[""] + list(project_options.keys()),
                                                 format_func=lambda x: project_options.get(x, "Select Project..."),
                                                 key="sidebar_project_selector")
        if selected_proj_id_sidebar and selected_proj_id_sidebar != st.session_state.selected_project_id:
            st.session_state.selected_project_id = selected_proj_id_sidebar
            st.session_state.selected_project_display_name = project_options[selected_proj_id_sidebar]
            st.session_state.active_ris_filename = None

            project_id = st.session_state.selected_project_id
            if project_id not in st.session_state.workflow_config or not st.session_state.workflow_config[project_id].get("rounds"):
                 st.session_state.workflow_config[project_id] = {"rounds": [{"name": "Round 1", "agents": [], "filter_config": {"type": "all_previous"}}]}

            if st.session_state.selected_project_id:
                st.session_state.project_rag_files = gui_utils.get_project_rag_files_from_config(st.session_state.selected_project_id)

            st.session_state.review_in_progress = False; st.session_state.review_log = [];
            st.session_state.review_progress = 0; st.session_state.review_results = None;
            st.session_state.generated_graph_html_path = None
            st.session_state.data_editor_key += 1
            st.rerun()

        if st.session_state.selected_project_id:
            st.caption(f"Current Project: {st.session_state.selected_project_display_name}")
            if st.button("✖️ Close Project", use_container_width=True, key="close_project_sidebar"):
                 st.session_state.selected_project_id = None; st.session_state.selected_project_display_name = None;
                 st.session_state.active_ris_filename = None; st.session_state.project_rag_files = [];
                 st.session_state.review_results = None; st.session_state.generated_graph_html_path = None
                 st.rerun()

def render_project_management_ui():
    if not st.session_state.selected_project_id:
        st.subheader("Create New Project")
        with st.form("ui_comp_new_project_form"):
            new_project_name_input = st.text_input("New Project Name:")
            submitted_new_project = st.form_submit_button("Create Project")
            if submitted_new_project:
                if new_project_name_input:
                    success, message = gui_utils.create_project_structure(new_project_name_input)
                    if success: st.success(message)
                    else: st.error(message)
                    st.rerun()
                else: st.error("Project name cannot be empty.")

def _render_rag_file_manager_ui_internal(project_rag_path, project_id): # Made private
    with st.expander("RAG Background Materials (Optional PDF/TXT)", expanded=True):
        uploaded_rag_files = st.file_uploader(
            "Upload background documents (1-5 files, PDF/TXT):", type=["pdf", "txt"],
            accept_multiple_files=True, key=f"rag_uploader_{project_id}_uicomp")
        if uploaded_rag_files:
            newly_uploaded_filenames = []
            for uploaded_file in uploaded_rag_files:
                if len(st.session_state.project_rag_files) + len(newly_uploaded_filenames) >= 5:
                    st.warning(f"Limit (5) reached. Cannot upload '{uploaded_file.name}'.")
                    break
                file_path = os.path.join(project_rag_path, uploaded_file.name)
                try:
                    with open(file_path, "wb") as f: f.write(uploaded_file.getbuffer())
                    newly_uploaded_filenames.append(uploaded_file.name)
                except Exception as e: st.error(f"Error saving '{uploaded_file.name}': {e}")
            if newly_uploaded_filenames:
                st.success(f"Uploaded: {', '.join(newly_uploaded_filenames)}")
                current_set = set(st.session_state.project_rag_files); current_set.update(newly_uploaded_filenames)
                st.session_state.project_rag_files = sorted(list(current_set))
                gui_utils.update_project_rag_files(project_id, st.session_state.project_rag_files)
                st.rerun()

        st.write("**Currently Uploaded RAG Files:**")
        if st.session_state.project_rag_files:
            for rag_file_name in list(st.session_state.project_rag_files):
                col1, col2 = st.columns([0.8, 0.2])
                col1.caption(rag_file_name)
                if col2.button(f"🗑️##{rag_file_name}", key=f"del_rag_ui_{rag_file_name}_{project_id}", help=f"Delete {rag_file_name}"):
                    try:
                        os.remove(os.path.join(project_rag_path, rag_file_name))
                        st.session_state.project_rag_files.remove(rag_file_name)
                        gui_utils.update_project_rag_files(project_id, st.session_state.project_rag_files)
                        st.success(f"Deleted: {rag_file_name}"); st.rerun()
                    except Exception as e: st.error(f"Error deleting '{rag_file_name}': {e}")
        else: st.caption("No RAG documents uploaded.")
        if st.session_state.project_rag_files: st.info("Simulated: Vector store would update if files changed.")

def render_data_management_ui():
    st.subheader(f"Data & Context Management for: {st.session_state.selected_project_display_name}")
    project_data_path = os.path.join(gui_utils.PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "data")
    project_rag_path = os.path.join(gui_utils.PROJECTS_ROOT_DIR, st.session_state.selected_project_id, "rag_context")

    with st.expander("RIS Literature Files (.ris)", expanded=not st.session_state.active_ris_filename):
        uploaded_ris_file = st.file_uploader("Upload new .ris Literature File", type=["ris"], key=f"ris_uploader_main_{st.session_state.selected_project_id}")
        if uploaded_ris_file:
            save_path = os.path.join(project_data_path, uploaded_ris_file.name)
            try:
                with open(save_path, "wb") as f: f.write(uploaded_ris_file.getbuffer())
                st.success(f"File '{uploaded_ris_file.name}' uploaded."); st.session_state.active_ris_filename = None; st.rerun()
            except Exception as e: st.error(f"Error saving RIS: {e}")

        ris_files = [f for f in os.listdir(project_data_path) if f.endswith(".ris")] if os.path.exists(project_data_path) else []
        idx = 0
        if st.session_state.active_ris_filename and st.session_state.active_ris_filename in ris_files:
            idx = ris_files.index(st.session_state.active_ris_filename) + 1

        sel_ris = st.selectbox("Select RIS file to process/view:", [""]+ris_files, index=idx, format_func=lambda x:x or "Select...", key=f"sel_ris_main_{st.session_state.selected_project_id}")

        if sel_ris and (st.session_state.active_ris_filename != sel_ris or sel_ris not in st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {})):
            if st.button(f"Load & Process: '{sel_ris}'", key=f"proc_ris_main_{sel_ris}"):
                df, err = gui_utils.parse_ris_file(os.path.join(project_data_path, sel_ris))
                if df is not None:
                    st.session_state.ris_dataframes.setdefault(st.session_state.selected_project_id, {})[sel_ris] = df
                    st.session_state.active_ris_filename = sel_ris
                    st.session_state.review_results = None; st.session_state.data_editor_key +=1
                    st.success(f"Loaded: '{sel_ris}'."); st.rerun()
                else: st.error(err or f"Failed to parse.")
        elif sel_ris and st.session_state.active_ris_filename == sel_ris: st.caption(f"'{sel_ris}' is active.")
        elif not ris_files: st.caption("No .ris files. Upload one.")

    _render_rag_file_manager_ui_internal(project_rag_path, st.session_state.selected_project_id)
    return st.session_state.ris_dataframes.get(st.session_state.selected_project_id, {}).get(st.session_state.active_ris_filename)

def _render_agent_config_form_ui_internal(agent_config, round_idx, agent_idx, project_id_key, agent_type_names_list): # Made private
    agent_config["name"] = st.text_input("Agent Name:", value=agent_config.get("name", f"Agent {agent_idx+1}"), key=f"an_ui_{round_idx}_{agent_idx}_{project_id_key}", disabled=st.session_state.review_in_progress)
    current_agent_type_index = agent_type_names_list.index(agent_config["type"]) if agent_config.get("type") in agent_type_names_list else 0
    agent_config["type"] = st.selectbox("Agent Type:", options=agent_type_names_list, index=current_agent_type_index, key=f"at_ui_{round_idx}_{agent_idx}_{project_id_key}", disabled=st.session_state.review_in_progress)
    agent_config["backstory"] = st.text_area("Agent Backstory/Persona:", value=agent_config.get("backstory", ""), key=f"ab_ui_{round_idx}_{agent_idx}_{project_id_key}", height=75, disabled=st.session_state.review_in_progress)

    # Conditional inputs based on agent type
    if agent_config["type"] in ["TitleAbstractReviewer", "ScoringReviewer"]:
        agent_config["inclusion_criteria"] = st.text_area("Inclusion Criteria (one per line):", value=agent_config.get("inclusion_criteria", "- Criterion 1"), key=f"aic_ui_{round_idx}_{agent_idx}_{project_id_key}", height=75, disabled=st.session_state.review_in_progress)
        agent_config["exclusion_criteria"] = st.text_area("Exclusion Criteria (one per line):", value=agent_config.get("exclusion_criteria", "- Criterion A"), key=f"aec_ui_{round_idx}_{agent_idx}_{project_id_key}", height=75, disabled=st.session_state.review_in_progress)
    elif agent_config["type"] == "AbstractionReviewer":
        agent_config["inclusion_criteria"] = st.text_area("Abstraction Focus/Prompt (e.g., 'Extract key methods and findings related to AI ethics.'):", value=agent_config.get("inclusion_criteria", "Extract key methods and findings."), key=f"aic_abs_ui_{round_idx}_{agent_idx}_{project_id_key}", height=100, disabled=st.session_state.review_in_progress)
        # AbstractionReviewer might not use exclusion_criteria in the same way
        if "exclusion_criteria" in agent_config: del agent_config["exclusion_criteria"]

def _render_inter_round_filter_ui_internal(round_data, previous_round_data, round_idx, project_id_key): # Made private
    st.markdown("##### Article Source & Filtering for this Round")
    prev_round_agents = previous_round_data.get("agents", [])
    prev_round_has_scorer = any(a.get("type") == "ScoringReviewer" for a in prev_round_agents)

    filter_options = {"included_previous": "Only 'Included' articles from previous round", "all_previous": "All articles from previous round", "excluded_previous": "Only 'Excluded' articles from previous round", "disagreement_previous": "Articles with disagreement from previous round"}
    if prev_round_has_scorer: filter_options["score_above_threshold"] = "Articles with score above X from previous round"

    current_filter_type = round_data.get("filter_config", {}).get("type", "included_previous")
    if current_filter_type not in filter_options: current_filter_type = "included_previous" # Fallback

    selected_filter_key = st.selectbox("Source of Articles:", options=list(filter_options.keys()), format_func=lambda x: filter_options[x], index=list(filter_options.keys()).index(current_filter_type), key=f"filter_type_ui_{round_idx}_{project_id_key}", disabled=st.session_state.review_in_progress)
    round_data["filter_config"]["type"] = selected_filter_key

    if selected_filter_key == "score_above_threshold":
        current_thresh = round_data.get("filter_config", {}).get("threshold", 3.0)
        score_thresh = st.number_input("Score Threshold:", min_value=0.0, max_value=5.0, value=current_thresh, step=0.1, key=f"filter_score_ui_{round_idx}_{project_id_key}", disabled=st.session_state.review_in_progress)
        round_data["filter_config"]["threshold"] = score_thresh
    elif "threshold" in round_data.get("filter_config", {}): del round_data["filter_config"]["threshold"]

def render_workflow_config_ui(current_gui_workflow_config): # Main wrapper
    with st.expander("Define Review Workflow (Rounds & Agents)", expanded=not st.session_state.review_in_progress):
        col_add, col_rem, _ = st.columns([1,1,3])
        with col_add:
            if st.button("➕ Add New Review Round", key="add_round_main_ui", disabled=st.session_state.review_in_progress):
                new_name = f"Round {len(current_gui_workflow_config['rounds']) + 1}"
                current_gui_workflow_config["rounds"].append({"name": new_name, "agents": [], "filter_config": {"type": "included_previous"}})
                st.rerun()
        with col_rem:
            if len(current_gui_workflow_config["rounds"]) > 1:
                if st.button("➖ Remove Last Review Round", key="rem_round_main_ui", type="secondary", disabled=st.session_state.review_in_progress):
                    current_gui_workflow_config["rounds"].pop(); st.rerun()

        tab_titles = [r.get('name', f'R {idx+1}') for idx, r in enumerate(current_gui_workflow_config["rounds"])]
        tabs = st.tabs(tab_titles)
        for i, tab_content in enumerate(tabs):
            with tab_content:
                round_data = current_gui_workflow_config['rounds'][i]
                st.markdown(f"**Settings for: {round_data.get('name', f'Round {i+1}')}**")
                new_r_name = st.text_input("Edit Round Name:", value=round_data.get('name',''), key=f"rn_main_ui_{i}_{st.session_state.selected_project_id}", disabled=st.session_state.review_in_progress)
                if new_r_name != round_data.get('name',''): round_data['name'] = new_r_name; st.rerun()

                if i > 0: _render_inter_round_filter_ui_internal(round_data, current_gui_workflow_config["rounds"][i-1], i, st.session_state.selected_project_id)
                st.markdown("---"); st.write(f"**Configured Agents in this Round:** {len(round_data.get('agents',[]))}")
                if st.button(f"➕ Add Agent to this Round", key=f"aa_main_ui_{i}", disabled=st.session_state.review_in_progress):
                    round_data.setdefault("agents",[]).append({"name":f"Agent {len(round_data.get('agents',[]))+1}","type":AGENT_TYPE_NAMES[0],"backstory":"","inclusion_criteria":"","exclusion_criteria":""}); st.rerun()
                for agent_idx, acfg in enumerate(list(round_data.get("agents",[]))): # Iterate copy for safe removal
                    with st.expander(f"Configure Agent: {acfg.get('name')} ({acfg.get('type')})", expanded=True):
                        _render_agent_config_form_ui_internal(acfg, i, agent_idx, st.session_state.selected_project_id, AGENT_TYPE_NAMES)
                        if st.button(f"➖ Remove This Agent",key=f"ra_main_ui_{i}_{agent_idx}",type="secondary", disabled=st.session_state.review_in_progress):
                            round_data["agents"].pop(agent_idx);st.rerun()
                        st.markdown("---")

def render_review_execution_ui(active_df_to_display, current_gui_workflow_config):
    # ... (Same as in app.py, uses gui_utils.is_workflow_runnable) ...
    st.subheader(f"Review Execution")
    if gui_utils.is_workflow_runnable(current_gui_workflow_config): # Example use of util
        # ... (button and progress display logic) ...
        pass
    else:
        st.warning("Workflow not runnable. Please configure agents in each round.")


def _render_results_table_and_details_ui_internal(results_df, data_editor_key, project_id): # Made private
    if "_selected" not in results_df.columns: results_df.insert(0, "_selected", False)
    filter_cols = st.columns([2,2,1]); decision_opts = results_df["final_decision"].unique().tolist() if "final_decision" in results_df.columns else []
    sel_decs = filter_cols[0].multiselect("Filter by Final Decision:", decision_opts, default=decision_opts, key=f"res_dec_filt_ui_{data_editor_key}")

    sel_score_rng = None; has_num_scores = 'final_score' in results_df.columns and pd.to_numeric(results_df['final_score'], errors='coerce').notna().any()
    if has_num_scores:
        num_scores = pd.to_numeric(results_df['final_score'], errors='coerce'); min_s, max_s = float(num_scores.min()), float(num_scores.max())
        sel_score_rng = filter_cols[1].slider("Filter by Final Score:", min_s, max_s, (min_s,max_s), 0.1, key=f"res_score_filt_ui_{data_editor_key}", disabled=min_s==max_s)
    else: filter_cols[1].caption("Score filter N/A.")

    filtered_df = results_df.copy()
    if sel_decs and "final_decision" in filtered_df.columns: filtered_df = filtered_df[filtered_df["final_decision"].isin(sel_decs)]
    if has_num_scores and sel_score_rng and "final_score" in filtered_df.columns:
        num_s_col = pd.to_numeric(filtered_df['final_score'], errors='coerce'); mask = (num_s_col >= sel_score_rng[0]) & (num_s_col <= sel_score_rng[1])
        if pd.api.types.is_string_dtype(filtered_df['final_score']): mask |= (filtered_df['final_score'] == "N/A")
        filtered_df = filtered_df[mask]

    st.info(f"Displaying {len(filtered_df)} of {len(results_df)} total results based on current filters.")
    editor_key = f"data_editor_ui_{project_id}_{st.session_state.active_ris_filename}_{data_editor_key}"
    disp_cols = ["_selected", "id", "title", "final_decision", "final_score"]; final_disp_cols = [c for c in disp_cols if c in filtered_df.columns]

    edited_df = st.data_editor(filtered_df[final_disp_cols] if final_disp_cols else filtered_df, key=editor_key, hide_index=True, num_rows="dynamic", disabled=[c for c in final_disp_cols if c != "_selected"])
    selected_rows = edited_df[edited_df["_selected"]]

    if not selected_rows.empty:
        st.markdown("---"); st.subheader("🔍 Selected Article Details")
        sel_ids = selected_rows["id"].tolist()
        sel_orig_rows = results_df[results_df["id"].isin(sel_ids)]
        for _, r_orig in sel_orig_rows.iterrows():
            st.markdown(f"#### {r_orig.get('title', 'N/A')}"); st.caption(f"ID: {r_orig.get('id', 'N/A')}")
            c1,c2=st.columns(2);c1.metric("Decision",r_orig.get('final_decision','N/A'));c2.metric("Score",str(r_orig.get('final_score','N/A')))
            with st.expander("Abstract"): st.markdown(r_orig.get('abstract', "N/A"))
            with st.expander("Reasoning Summary"): st.markdown(r_orig.get('reasoning_summary', "N/A"))
            with st.expander("Detailed Workflow Log"): st.text(r_orig.get('detailed_workflow_log', "N/A"))
            st.markdown("---")
    return filtered_df, selected_rows # Return for export options

def _render_export_options_ui_internal(filtered_df_to_export, selected_rows_to_export, all_results_df, project_id_str): # Made private
    st.markdown("---"); st.subheader("📤 Export Results")
    if not filtered_df_to_export.empty:
        csv_filt = filtered_df_to_export.drop(columns=["_selected"], errors='ignore').to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Filtered (CSV)", csv_filt, f"{project_id_str}_filtered.csv", "text/csv", key="exp_filt_csv_ui")
        ris_filt = gui_utils.convert_dataframe_to_ris_text(filtered_df_to_export.drop(columns=["_selected"], errors='ignore'))
        st.download_button("📥 Download Filtered (RIS)", ris_filt, f"{project_id_str}_filtered.ris", "application/x-research-info-systems", key="exp_filt_ris_ui")
    else: st.caption("No filtered data to export.")

    if not selected_rows_to_export.empty:
        sel_ids = selected_rows_to_export["id"].tolist()
        df_sel_exp = all_results_df[all_results_df["id"].isin(sel_ids)] # Use original full data for selected rows
        csv_sel = df_sel_exp.drop(columns=["_selected"], errors='ignore').to_csv(index=False).encode('utf-8')
        st.download_button(f"📥 Download Selected ({len(selected_rows_to_export)}) (CSV)", csv_sel, f"{project_id_str}_selected.csv", "text/csv", key="exp_sel_csv_ui")
        ris_sel = gui_utils.convert_dataframe_to_ris_text(df_sel_exp.drop(columns=["_selected"], errors='ignore'))
        st.download_button(f"📥 Download Selected ({len(selected_rows_to_export)}) (RIS)", ris_sel, f"{project_id_str}_selected.ris", "application/x-research-info-systems", key="exp_sel_ris_ui")
    else: st.caption("Select rows in table to enable export of selection.")


def render_results_overview_tab_ui(): # Wrapper for this tab
    st.header("Results Overview & Filters")
    if st.session_state.review_results is None or st.session_state.review_results.empty:
        st.info("No review results to display yet. Please run a review."); return

    filtered_df, selected_rows = _render_results_table_and_details_ui_internal(
        st.session_state.review_results,
        st.session_state.data_editor_key,
        st.session_state.selected_project_id
    )
    _render_export_options_ui_internal(
        filtered_df,
        selected_rows,
        st.session_state.review_results, # Pass original full results for selected export
        st.session_state.selected_project_id
    )

def _render_concept_network_graph_ui_internal(included_articles_df, concept_columns, all_concepts_list, project_id_str): # Made private
    st.markdown("---"); st.write("#### Concept Network Graph (Co-occurrence based)")
    try:
        co_occurrence = Counter()
        article_concept_sets = []
        if concept_columns:
            for _, row in included_articles_df.iterrows():
                current_set = set()
                for col in concept_columns:
                    concepts = row.get(col)
                    if isinstance(concepts, list): current_set.update(concepts)
                if len(current_set) > 1: article_concept_sets.append(list(current_set))

        if article_concept_sets:
            for concept_set in article_concept_sets:
                for c1, c2 in combinations(sorted(list(set(concept_set))), 2):
                    co_occurrence[tuple(sorted((c1, c2)))] += 1

        if co_occurrence:
            net = Network(notebook=True, height="700px", width="100%", cdn_resources='remote', directed=False, select_menu=True, filter_menu=True)
            net.repulsion(node_distance=150, spring_length=200)
            overall_freq = Counter(all_concepts_list)
            for node, freq in overall_freq.items(): net.add_node(str(node), label=str(node), value=freq, title=f"{node} (Freq: {freq})")
            for edge, weight in co_occurrence.items():
                if weight > 0: net.add_edge(str(edge[0]), str(edge[1]), value=weight, title=f"Co-occur: {weight}")

            results_path = os.path.join(gui_utils.PROJECTS_ROOT_DIR, project_id_str, "results")
            os.makedirs(results_path, exist_ok=True)
            graph_path = os.path.join(results_path, "concept_network.html")
            net.save_graph(graph_path)
            st.session_state.generated_graph_html_path = graph_path
        else: st.caption("No significant co-occurrences to build network."); st.session_state.generated_graph_html_path = None

        if st.session_state.get("generated_graph_html_path") and os.path.exists(st.session_state.generated_graph_html_path):
            with open(st.session_state.generated_graph_html_path, 'r', encoding='utf-8') as f: html_source = f.read()
            st.components.v1.html(html_source, height=750, scrolling=True)
            st.caption("Interactive concept network. Node size by frequency, edge width by co-occurrence.")
        elif co_occurrence: st.warning("Graph generated but HTML path issue.")
    except ImportError: st.error("Pyvis library needed.")
    except Exception as e: st.error(f"Graph error: {e}")


def render_theme_analysis_tab_ui(): # Wrapper for this tab
    st.header("Theme Analysis Dashboard (from Included Articles)")
    if st.session_state.review_results is None or st.session_state.review_results.empty:
        st.info("No review results to analyze themes."); return

    included_df = st.session_state.review_results[st.session_state.review_results.get("final_decision") == "Included"]
    if included_df.empty: st.info("No 'Included' articles found."); return

    all_concepts = []; concept_cols = [col for col in included_df.columns if "extracted_concepts" in col.lower()]
    if not concept_cols: st.warning("No 'extracted_concepts' columns in results."); return

    for col in concept_cols:
        series = included_df[col].dropna()
        for c_list in series:
            if isinstance(c_list, list): all_concepts.extend(c_list)
            elif isinstance(c_list, str): all_concepts.extend([c.strip() for c in c_list.split(',')])

    if not all_concepts: st.info("No concepts extracted from 'Included' articles."); return

    st.markdown("#### Top Extracted Concepts"); concept_counts = Counter(all_concepts)
    common_df = pd.DataFrame(concept_counts.most_common(15), columns=['Concept', 'Frequency'])
    c1,c2 = st.columns(2); c1.write("Frequency Table:"); c1.dataframe(common_df,use_container_width=True)
    if not common_df.empty:
        c2.write("Frequency Chart:"); common_df['Concept'] = common_df['Concept'].astype(str)
        try: c2.bar_chart(common_df.set_index('Concept'), height=350)
        except Exception as e: c2.error(f"Chart error: {e}")

    st.markdown("---"); st.write("#### Word Cloud of Extracted Concepts")
    text_wc = " ".join(all_concepts)
    if text_wc:
        try:
            wc_img = WordCloud(width=800,height=400,background_color='white',collocations=True).generate(text_wc)
            fig, ax = plt.subplots(figsize=(10,5)); ax.imshow(wc_img,interpolation='bilinear'); ax.axis("off"); st.pyplot(fig)
        except Exception as e: st.error(f"Word cloud error: {e}")
    else: st.caption("Not enough data for word cloud.")

    _render_concept_network_graph_ui_internal(included_df, concept_cols, all_concepts, st.session_state.selected_project_id)


def render_results_main_ui(): # Main wrapper for results section
    if st.session_state.review_results is not None and not st.session_state.review_in_progress:
        st.divider(); st.subheader("📄 Review Analysis")
        results_tab1, theme_analysis_tab2 = st.tabs(["📄 Results Overview & Details", "📊 Theme Analysis Dashboard"])
        with results_tab1:
            render_results_overview_tab_ui()
        with theme_analysis_tab2:
            render_theme_analysis_tab_ui()

# No main() function in ui_components.py
# These functions will be called by app.py's main()
