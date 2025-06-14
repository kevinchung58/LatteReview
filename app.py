import streamlit as st
import os
import pandas as pd # Keep for potential direct use in main or for type hinting
import asyncio
import nest_asyncio

import gui_utils # Non-UI helper functions
import ui_components # UI rendering functions

nest_asyncio.apply()

# --- Main Application Orchestration ---
def main():
    st.set_page_config(page_title="LatteReview 🤖☕", layout="wide")

    # Initialize session state (this should be the single source of truth for init)
    default_session_keys = {
        "api_key_entered": False, "gemini_api_key": "", "selected_project_id": None,
        "workflow_config": {}, "ris_dataframes": {}, "active_ris_filename": None,
        "selected_project_display_name": None, "show_create_project_modal": False, # Though create modal is now in project_management_ui
        "review_in_progress": False, "review_log": [], "review_progress": 0,
        "review_status_message": "", "review_results": None, "data_editor_key": 0,
        "project_rag_files": [], "generated_graph_html_path": None
    }
    for k, dv in default_session_keys.items():
        if k not in st.session_state: st.session_state[k] = dv

    # --- Render Sidebar ---
    # get_existing_projects is needed here to pass to the sidebar for project selection
    existing_projects_list = gui_utils.get_existing_projects()
    ui_components.render_sidebar(existing_projects_list)

    # --- Main Page Title & Welcome ---
    st.title("LatteReview 🤖☕ - AI Literature Review Assistant")
    if not st.session_state.api_key_entered or not st.session_state.gemini_api_key:
        st.warning("Please enter your Gemini API Key in the sidebar settings to enable all features.", icon="🔑")
    # Welcome message can be part of main or a specific dashboard component if one exists
    # st.markdown("Welcome to LatteReview! Your AI-powered literature review assistant.")

    # --- Project Management UI (Create New Project if none selected) ---
    if not st.session_state.selected_project_id:
        ui_components.render_project_management_ui() # Handles new project creation form
        st.divider()
        st.info("Select or create a project to begin.")
        st.stop() # Stop further rendering if no project selected

    # --- Main Application Flow (Runs if a project IS selected) ---
    st.markdown(f"### Project: **{st.session_state.selected_project_display_name}** (`{st.session_state.selected_project_id}`)")
    st.divider()

    # --- Data Management UI ---
    # This function now handles RIS processing and RAG file management internally
    # It returns the active_df_to_display or None if not ready
    active_df_to_display = ui_components.render_data_management_ui()

    if active_df_to_display is None:
        # Message already shown in render_data_management_ui if no file selected/processed
        st.stop()

    # Essential column check (remains in main app logic as it's a critical gate)
    for col in ['id', 'title', 'abstract']: # These are essential for the core review process
        if col not in active_df_to_display.columns:
            st.error(f"Input data ('{st.session_state.active_ris_filename}') is missing essential column: '{col}'. Cannot proceed with review.")
            st.stop()

    st.info(f"Active Dataset: `{st.session_state.active_ris_filename}` ({len(active_df_to_display)} articles)")
    st.divider()

    # --- Workflow Configuration UI ---
    # get_current_project_workflow_config_from_session is defined in app.py and uses session_state
    # It could be moved to gui_utils if it doesn't directly render UI, but it modifies session_state.
    # For now, keep it here or ensure ui_components.render_workflow_config_ui can access/modify it.
    # The ui_components.render_workflow_config_ui takes the config dict as an argument.

    # Ensure workflow config for current project is loaded/initialized
    current_gui_workflow_config = st.session_state.workflow_config.get(st.session_state.selected_project_id)
    if not current_gui_workflow_config:
        current_gui_workflow_config = {"rounds": [{"name": "Round 1", "agents": [], "filter_config": {"type": "all_previous"}}]}
        st.session_state.workflow_config[st.session_state.selected_project_id] = current_gui_workflow_config

    ui_components.render_workflow_config_ui(current_gui_workflow_config)
    st.divider()

    # --- Review Execution UI & Logic ---
    ui_components.render_review_execution_ui(active_df_to_display, current_gui_workflow_config)

    # Actual review execution logic (triggered by button inside render_review_execution_ui via rerun)
    if st.session_state.review_in_progress and st.session_state.review_log and st.session_state.review_log[-1].startswith("Building workflow..."):
        lattereview_workflow_instance = gui_utils.build_lattereview_workflow_from_config(
            current_gui_workflow_config,
            st.session_state.gemini_api_key,
            st.session_state.project_rag_files
        )
        if lattereview_workflow_instance:
            st.session_state.review_log.append("Workflow built. Starting REAL review process...");
            st.session_state.review_progress = 10; st.session_state.review_status_message = "Reviewing (backend)...";
            # No st.rerun() here, let the async call proceed
            try:
                with st.spinner(f"Processing review with LatteReview backend... Articles: {len(active_df_to_display)}"):
                    results_df_raw = asyncio.run(lattereview_workflow_instance(data=active_df_to_display, return_type="pandas"))
                st.session_state.review_log.append("Raw results received from backend.");
                st.session_state.review_status_message = "Post-processing results..."; st.session_state.review_progress = 90;

                processed_df = gui_utils.post_process_review_results(results_df_raw, current_gui_workflow_config)
                st.session_state.review_results = processed_df

                st.session_state.review_log.append(f"Results processed. Final count: {len(st.session_state.review_results) if st.session_state.review_results is not None else 'N/A'}");
                st.session_state.review_status_message = "Actual Review Complete!"; st.session_state.review_progress = 100; st.balloons()
            except RuntimeError as e:
                if "cannot be called from a running event loop" in str(e):
                    st.error("Asyncio event loop error. nest_asyncio might not be fully effective. Try rerunning.")
                    st.session_state.review_log.append("Asyncio error caught. User should retry.")
                else:
                    st.session_state.review_log.append(f"Runtime error during review: {e}"); st.error(f"Review failed: {e}")
                st.session_state.review_status_message = f"Error: {e}"
            except Exception as e:
                st.session_state.review_log.append(f"Error during review: {e}"); st.error(f"Review failed: {e}")
                st.session_state.review_status_message = f"Error: {e}"
            finally:
                st.session_state.review_in_progress = False; st.rerun()
        else: # Workflow build failed
            st.session_state.review_log.append("Workflow build FAILED.");
            st.session_state.review_in_progress = False; st.session_state.review_progress = 0; st.rerun()

    # --- Results Display UI ---
    if st.session_state.review_results is not None and not st.session_state.review_in_progress:
        ui_components.render_results_main_ui()

if __name__ == "__main__":
    main()
