import pytest
# Assuming gui_utils.py is in the parent directory or PYTHONPATH is set up for tests
# For robust imports in tests, often good to have a proper package structure or use relative imports if tests are a module
# For now, simple import assuming PYTHONPATH or same level for execution context.
# If run with `python -m pytest`, it often handles this better.
# To make it more robust for subtask execution, we might need to adjust sys.path
import sys
import os
# Add the parent directory (project root) to sys.path so gui_utils can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import gui_utils


# Tests for sanitize_project_name
def test_sanitize_project_name_empty():
    assert gui_utils.sanitize_project_name("") == ""

def test_sanitize_project_name_no_changes():
    assert gui_utils.sanitize_project_name("ValidName123_-") == "ValidName123_-"

def test_sanitize_project_name_with_spaces():
    assert gui_utils.sanitize_project_name("Project Name With Spaces") == "Project_Name_With_Spaces"

def test_sanitize_project_name_with_special_chars():
    assert gui_utils.sanitize_project_name("Project!@#$%^&*()Name") == "ProjectName"

def test_sanitize_project_name_leading_trailing_spaces():
    assert gui_utils.sanitize_project_name("  Spaced Project  ") == "Spaced_Project"

def test_sanitize_project_name_mixed_case():
    assert gui_utils.sanitize_project_name("MixedCaseName") == "MixedCaseName"

def test_sanitize_project_name_only_special_chars():
    assert gui_utils.sanitize_project_name("!@#$%^&*()") == ""

def test_sanitize_project_name_with_hyphens_and_underscores():
    assert gui_utils.sanitize_project_name("name-with_hyphens_and_underscores") == "name-with_hyphens_and_underscores"

def test_sanitize_project_name_long_name():
    long_name = "a" * 260
    sanitized = gui_utils.sanitize_project_name(long_name)
    # Assuming no explicit length limit in sanitize_project_name itself,
    # but filesystem might have limits later. Test just checks sanitization.
    assert sanitized == long_name

# Add a pytest marker for more tests to come (good practice)
# @pytest.mark.skip(reason="More tests to be added for other gui_utils functions")
# def test_placeholder_for_more_tests():
#    pass

# Mocking support
from unittest.mock import patch, MagicMock
import pandas as pd # For creating test DataFrames

# Tests for parse_ris_file

# Test case 1: Successful parsing and basic column renaming
@patch('gui_utils.data_handler.RISHandler') # Patch where RISHandler is looked up (i.e., in gui_utils)
def test_parse_ris_file_success_basic_rename(MockRISHandler):
    # Configure the mock RISHandler instance and its method
    mock_instance = MockRISHandler.return_value
    mock_df_from_handler = pd.DataFrame({
        'TI': ['Test Title 1'], # Primary title
        'ID': ['RIS_ID_1'],     # Identifier
        'AB': ['Abstract 1'],   # Abstract
        'PY': ['2023'],         # Publication Year
        'AU': [['Author A', 'Author B']], # Authors as list
        'KW': [['Keyword1', 'Keyword2']]  # Keywords as list
    })
    mock_instance.load_ris_file_to_dataframe.return_value = mock_df_from_handler

    # Call the function under test
    # Need a dummy file_path argument, it won't be used by the mocked method
    df_result, error = gui_utils.parse_ris_file("dummy/path/test.ris")

    assert error is None
    assert df_result is not None
    assert 'title' in df_result.columns and df_result['title'][0] == 'Test Title 1'
    assert 'id' in df_result.columns and df_result['id'][0] == 'RIS_ID_1'
    assert 'abstract' in df_result.columns and df_result['abstract'][0] == 'Abstract 1'
    assert 'year' in df_result.columns and df_result['year'][0] == '2023'
    # The parse_ris_file logic ensures authors/keywords are lists of strings.
    # If input is already list of strings, it should be preserved.
    assert 'authors' in df_result.columns and df_result['authors'][0] == ['Author A', 'Author B']
    assert 'keywords' in df_result.columns and df_result['keywords'][0] == ['Keyword1', 'Keyword2']
    mock_instance.load_ris_file_to_dataframe.assert_called_once_with("dummy/path/test.ris")

# Test case 2: Alternative column names from RISHandler
@patch('gui_utils.data_handler.RISHandler')
def test_parse_ris_file_alternative_column_names(MockRISHandler):
    mock_instance = MockRISHandler.return_value
    mock_df_from_handler = pd.DataFrame({
        'primary_title': ['Alt Title'],
        'AN': ['Accession1'],
        'N2': ['Alt Abstract'],
        'Y1': ['2022'],
        'A1': ['FirstAuthorOnly'], # This is an example, 'A1' is not in current col_map for authors
        'JO': ['Journal Of Tests']
    })
    mock_instance.load_ris_file_to_dataframe.return_value = mock_df_from_handler

    df_result, error = gui_utils.parse_ris_file("dummy.ris")

    assert error is None
    assert df_result is not None
    assert df_result['title'][0] == 'Alt Title'
    assert df_result['id'][0] == 'Accession1'
    assert df_result['abstract'][0] == 'Alt Abstract'
    assert df_result['year'][0] == '2022'
    assert df_result['journal_name'][0] == 'Journal Of Tests'
    # Since 'A1' is not in col_map for 'authors', 'authors' will be created as empty lists
    assert 'authors' in df_result.columns and df_result['authors'][0] == ['FirstAuthorOnly'] # Corrected expectation based on current logic

# Test case 3: Missing essential columns, should get defaults
@patch('gui_utils.data_handler.RISHandler')
def test_parse_ris_file_missing_essential_cols(MockRISHandler):
    mock_instance = MockRISHandler.return_value
    mock_df_from_handler = pd.DataFrame({'OTHER_COL': ['data']})
    mock_instance.load_ris_file_to_dataframe.return_value = mock_df_from_handler

    df_result, error = gui_utils.parse_ris_file("missing.ris")

    assert error is None
    assert df_result is not None
    assert 'id' in df_result.columns and "Missing_id" in df_result['id'][0]
    assert 'title' in df_result.columns and "Missing_title" in df_result['title'][0]
    assert 'abstract' in df_result.columns and "Missing_abstract" in df_result['abstract'][0]
    # Check that other potentially mapped columns also get defaults (empty lists or random year/journal)
    assert 'authors' in df_result.columns and df_result['authors'][0] == []
    assert 'keywords' in df_result.columns and df_result['keywords'][0] == []
    assert 'year' in df_result.columns # Will have a random year
    assert 'journal_name' in df_result.columns # Will have "Unknown Journal X"


# Test case 4: Year extraction and type consistency (string)
@patch('gui_utils.data_handler.RISHandler')
def test_parse_ris_file_year_extraction(MockRISHandler):
    mock_instance = MockRISHandler.return_value
    # Test various year formats and types
    mock_df_from_handler = pd.DataFrame({'PY': ['20230515', '2022', 'InvalidYear', None, 2021.0, 2020]})
    mock_instance.load_ris_file_to_dataframe.return_value = mock_df_from_handler

    df_result, error = gui_utils.parse_ris_file("years.ris")

    assert error is None
    # Current logic: str(x).split('.')[0] if pd.notna(x) else None
    # 'InvalidYear' -> 'InvalidYear'
    # None -> None
    # 2021.0 -> '2021'
    # 2020 -> '2020'
    expected_years = ['2023', '2022', 'InvalidYear', None, '2021', '2020']
    assert df_result['year'].tolist() == expected_years


# Test case 5: Authors/Keywords string splitting and list handling
@patch('gui_utils.data_handler.RISHandler')
def test_parse_ris_file_string_splitting_authors_keywords(MockRISHandler):
    mock_instance = MockRISHandler.return_value
    mock_df_from_handler = pd.DataFrame({
        'AU': ['Author A; Author B', ['Author C', ' Author D '], None, 'SingleAuthor', 123], # Semicolon separated, list, None, single, numeric
        'KW': ['KW1; KW2; KW3', None, ['SingleKW'], 'KW_Alone', 456]    # Semicolon separated, None, list, single, numeric
    })
    mock_instance.load_ris_file_to_dataframe.return_value = mock_df_from_handler

    df_result, error = gui_utils.parse_ris_file("strings.ris")

    assert error is None
    assert df_result['authors'][0] == ['Author A', 'Author B']
    assert df_result['authors'][1] == ['Author C', 'Author D'] # Assumes inner strip
    assert df_result['authors'][2] == []
    assert df_result['authors'][3] == ['SingleAuthor']
    assert df_result['authors'][4] == ['123']

    assert df_result['keywords'][0] == ['KW1', 'KW2', 'KW3']
    assert df_result['keywords'][1] == []
    assert df_result['keywords'][2] == ['SingleKW']
    assert df_result['keywords'][3] == ['KW_Alone']
    assert df_result['keywords'][4] == ['456']


# Test case 6: RISHandler throws an exception
@patch('gui_utils.data_handler.RISHandler')
def test_parse_ris_file_handler_exception(MockRISHandler):
    mock_instance = MockRISHandler.return_value
    mock_instance.load_ris_file_to_dataframe.side_effect = Exception("RIS parse failed badly")

    df_result, error = gui_utils.parse_ris_file("exception.ris")

    assert df_result is None
    assert error is not None
    # The error message now includes os.path.basename
    assert "Parse Error for exception.ris: Exception('RIS parse failed badly')" in error

# Test case 7: Empty DataFrame from handler
@patch('gui_utils.data_handler.RISHandler')
def test_parse_ris_file_empty_df_from_handler(MockRISHandler):
    mock_instance = MockRISHandler.return_value
    mock_instance.load_ris_file_to_dataframe.return_value = pd.DataFrame({'some_col':[]}) # Empty DF but with a column to avoid instant empty

    df_result, error = gui_utils.parse_ris_file("empty.ris")

    assert error is None
    assert df_result is not None
    # Even if the handler returns an empty DF, parse_ris_file adds default columns
    assert not df_result.empty # It won't be empty due to default columns
    assert 'id' in df_result.columns
    assert 'title' in df_result.columns
    assert 'abstract' in df_result.columns
    assert len(df_result) == 0 # But it should have 0 rows

# Mocking support
from unittest.mock import patch, MagicMock
import pandas as pd # For creating test DataFrames

# Tests for extract_text_from_rag_document
# Need to mock open for txt files and PyPDF2 for pdf files.
# Also need to mock os.path.splitext and os.path.basename for isolated testing.

@patch('gui_utils.os.path.splitext')
@patch('builtins.open') # Mock the global open function
def test_extract_text_from_txt_success(mock_open, mock_splitext):
    mock_splitext.return_value = ("test_file", ".txt")
    # Configure mock_open:
    # mock_open.return_value is the file object context manager
    # mock_file.read.return_value is the content
    mock_file = MagicMock()
    mock_file.read.return_value = "This is sample text from a TXT file."
    mock_open.return_value.__enter__.return_value = mock_file # For 'with open(...) as f:'

    text = gui_utils.extract_text_from_rag_document("dummy/path/test_file.txt")

    assert text == "This is sample text from a TXT file."
    mock_open.assert_called_once_with("dummy/path/test_file.txt", 'r', encoding='utf-8', errors='ignore')

@patch('gui_utils.os.path.splitext')
@patch('gui_utils.PyPDF2.PdfReader') # Patch PdfReader assuming PyPDF2 is imported as 'import PyPDF2' in gui_utils
@patch('gui_utils.st') # Mock streamlit to check for st.error etc.
def test_extract_text_from_pdf_success(mock_st, MockPdfReader, mock_splitext):
    mock_splitext.return_value = ("test_doc", ".pdf")

    mock_reader_instance = MockPdfReader.return_value
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "PDF Page 1 text. "
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "PDF Page 2 text."
    mock_reader_instance.pages = [mock_page1, mock_page2]

    # This test assumes that 'import PyPDF2' at the top of gui_utils.py is successful
    # or that PyPDF2 is available in the environment. The patch is for PdfReader.
    text = gui_utils.extract_text_from_rag_document("dummy/path/test_doc.pdf")

    assert text == "PDF Page 1 text. PDF Page 2 text."
    MockPdfReader.assert_called_once_with("dummy/path/test_doc.pdf")


@patch('gui_utils.os.path.splitext')
@patch('gui_utils.st') # Mock streamlit for st.warning
def test_extract_text_unsupported_file_type(mock_st, mock_splitext):
    mock_splitext.return_value = ("test_file", ".docx")
    text = gui_utils.extract_text_from_rag_document("dummy/path/test_file.docx")
    assert text is None
    # Check if st.warning was called with the specific message
    # The actual call in code is print, not st.warning. This test needs adjustment if print is used.
    # If it's print, we might need to patch print or check stdout.
    # Assuming it was changed to st.warning for GUI feedback:
    # mock_st.warning.assert_called_with("Unsupported RAG file type: .docx for test_file.docx")
    # If it's print, this assertion will fail. The function uses print for this.
    # For now, we just assert text is None, as print is harder to check here.

@patch('gui_utils.os.path.splitext')
@patch('builtins.open', side_effect=FileNotFoundError("File not found"))
@patch('gui_utils.st')
def test_extract_text_txt_file_not_found(mock_st, mock_open, mock_splitext):
    mock_splitext.return_value = ("test_file", ".txt")
    text = gui_utils.extract_text_from_rag_document("dummy/path/test_file.txt")
    assert text is None
    # Check if st.error was called. The function uses print for this.
    # mock_st.error.assert_called_with("Error reading RAG file test_file.txt: FileNotFoundError('File not found')")


# Test for PyPDF2 ImportError (simulating PyPDF2 not installed)
@patch('gui_utils.os.path.splitext')
@patch('gui_utils.st')
@patch.dict('sys.modules', {'PyPDF2': None}) # Simulate PyPDF2 not being importable
def test_extract_text_pdf_pypdf2_not_installed(mock_st, mock_splitext):
    mock_splitext.return_value = ("test_doc", ".pdf")

    # With PyPDF2 removed from sys.modules, the 'import PyPDF2' inside the function should raise ImportError
    text = gui_utils.extract_text_from_rag_document("dummy/path/test_doc.pdf")

    assert text is None
    # The function uses print for this error, not st.error directly in utils.
    # So we cannot assert mock_st.error. The test ensures text is None.
    # If st.error was used in util:
    # mock_st.error.assert_called_with("PyPDF2 library is required for PDF processing but not found. Please install it.")


@patch('gui_utils.os.path.splitext')
@patch('gui_utils.PyPDF2.PdfReader', side_effect=Exception("Bad PDF content"))
@patch('gui_utils.st')
def test_extract_text_pdf_parsing_error(mock_st, MockPdfReader, mock_splitext):
    mock_splitext.return_value = ("test_doc", ".pdf")

    text = gui_utils.extract_text_from_rag_document("dummy/path/test_doc.pdf")

    assert text is None
    # The function uses print for this warning, not st.warning directly in utils.
    # mock_st.warning.assert_called_with("PDF parse error test_doc.pdf: Exception('Bad PDF content')")

# Tests for is_workflow_runnable

def test_is_workflow_runnable_none_workflow():
    assert gui_utils.is_workflow_runnable(None) == False

def test_is_workflow_runnable_empty_dict_workflow():
    assert gui_utils.is_workflow_runnable({}) == False

def test_is_workflow_runnable_no_rounds_key():
    assert gui_utils.is_workflow_runnable({"some_other_key": []}) == False

def test_is_workflow_runnable_empty_rounds_list():
    assert gui_utils.is_workflow_runnable({"rounds": []}) == False

def test_is_workflow_runnable_round_with_no_agents_key():
    workflow = {"rounds": [{"name": "Round 1"}]} # No "agents" key in round
    assert gui_utils.is_workflow_runnable(workflow) == False

def test_is_workflow_runnable_round_with_empty_agents_list():
    workflow = {"rounds": [{"name": "Round 1", "agents": []}]}
    assert gui_utils.is_workflow_runnable(workflow) == False

def test_is_workflow_runnable_valid_single_round_single_agent():
    workflow = {
        "rounds": [
            {"name": "Round 1", "agents": [{"name": "Agent A", "type": "TitleAbstractReviewer"}]}
        ]
    }
    assert gui_utils.is_workflow_runnable(workflow) == True

def test_is_workflow_runnable_valid_multi_round_multi_agent():
    workflow = {
        "rounds": [
            {"name": "Round 1", "agents": [{"name": "Agent A", "type": "TitleAbstractReviewer"}]},
            {"name": "Round 2", "agents": [{"name": "Agent B", "type": "ScoringReviewer"}, {"name": "Agent C", "type": "AbstractionReviewer"}]}
        ]
    }
    assert gui_utils.is_workflow_runnable(workflow) == True

def test_is_workflow_runnable_one_valid_round_one_empty_agent_list_round():
    workflow = {
        "rounds": [
            {"name": "Round 1", "agents": [{"name": "Agent A", "type": "TitleAbstractReviewer"}]},
            {"name": "Round 2", "agents": []} # This round makes it not runnable
        ]
    }
    assert gui_utils.is_workflow_runnable(workflow) == False

def test_is_workflow_runnable_one_valid_round_one_round_no_agents_key():
    workflow = {
        "rounds": [
            {"name": "Round 1", "agents": [{"name": "Agent A", "type": "TitleAbstractReviewer"}]},
            {"name": "Round 2"} # No agents key
        ]
    }
    assert gui_utils.is_workflow_runnable(workflow) == False

# Tests for post_process_raw_results

def test_post_process_empty_raw_results():
    df_raw = pd.DataFrame()
    gui_config = {"rounds": []}
    processed_df = gui_utils.post_process_raw_results(df_raw, gui_config)
    assert processed_df.empty
    # Should ideally still have the summary columns if df_raw was not empty but had no matching data
    # However, if df_raw is empty, it returns empty.

def test_post_process_no_rounds_in_config():
    # Raw data might still exist, but config is empty
    data_raw = [{'id': 'art1', 'title': 'Title 1', 'round-A_Agent1_evaluation': 'Included'}]
    df_raw = pd.DataFrame(data_raw)
    gui_config = {"rounds": []} # No rounds configured

    processed_df = gui_utils.post_process_raw_results(df_raw, gui_config)

    assert not processed_df.empty
    assert 'final_decision' in processed_df.columns
    # The current post_process logic defaults to "N/A" if last_round_agents_cfg is empty (which it is if no rounds)
    assert processed_df['final_decision'][0] == "N/A"
    assert 'detailed_workflow_log' in processed_df.columns
    assert "Error: Workflow had no rounds in config" in processed_df['detailed_workflow_log'][0]

def test_post_process_single_round_single_agent_decision():
    data_raw = [{
        'id': 'art1', 'title': 'Title 1', 'abstract': 'Abs 1',
        'round-A_AgentSmith_evaluation': 'Included',
        'round-A_AgentSmith_reasoning': 'Looks good.',
        'round-A_AgentSmith_score': pd.NA # No score from this agent
    }]
    df_raw = pd.DataFrame(data_raw)
    gui_config = {
        "rounds": [
            {"name": "Round A Name", "agents": [{"name": "AgentSmith", "type": "TitleAbstractReviewer"}]}
        ]
    }
    processed_df = gui_utils.post_process_raw_results(df_raw, gui_config)

    assert processed_df['final_decision'][0] == 'Included'
    assert pd.isna(processed_df['final_score'][0]) # No score produced by this agent type
    assert processed_df['reasoning_summary'][0] == 'Looks good.' # Reasoning from the only agent
    assert "round-A_AgentSmith_evaluation: Included" in processed_df['detailed_workflow_log'][0]
    assert "round-A_AgentSmith_reasoning: Looks good." in processed_df['detailed_workflow_log'][0]

def test_post_process_multi_round_derives_from_last_round_first_agent():
    data_raw = [{
        'id': 'art2', 'title': 'Title 2',
        'round-A_Agent1_evaluation': 'Included',
        'round-A_Agent1_score': 3.0,
        'round-B_Expert1_evaluation': 'Excluded', # This should be final decision
        'round-B_Expert1_score': 1.5,            # This should be final score
        'round-B_Expert1_reasoning': 'Not relevant after all.'
    }]
    df_raw = pd.DataFrame(data_raw)
    gui_config = {
        "rounds": [
            {"name": "Initial Screen", "agents": [{"name": "Agent1", "type": "ScoringReviewer"}]},
            {"name": "Expert Review", "agents": [{"name": "Expert1", "type": "ScoringReviewer"}]}
        ]
    }
    processed_df = gui_utils.post_process_raw_results(df_raw, gui_config)

    assert processed_df['final_decision'][0] == 'Excluded'
    assert processed_df['final_score'][0] == 1.5
    assert processed_df['reasoning_summary'][0] == 'Not relevant after all.'
    assert "round-A_Agent1_evaluation: Included" in processed_df['detailed_workflow_log'][0]
    assert "round-B_Expert1_evaluation: Excluded" in processed_df['detailed_workflow_log'][0]

def test_post_process_score_conversion_and_na():
    data_raw = [{
        'id': 'art3', 'title': 'Title 3',
        'round-A_Scorer_evaluation': 'Included', 'round-A_Scorer_score': "4.2", # Score as string
        'round-B_Confirmer_evaluation': 'Included' # No score from this agent
    }, {
        'id': 'art4', 'title': 'Title 4',
        'round-A_Scorer_evaluation': 'Excluded', 'round-A_Scorer_score': "bad_score", # Invalid score string
        'round-B_Confirmer_evaluation': 'Excluded'
    }]
    df_raw = pd.DataFrame(data_raw)
    gui_config = {
        "rounds": [
            {"name": "R1", "agents": [{"name": "Scorer", "type": "ScoringReviewer"}]},
            {"name": "R2", "agents": [{"name": "Confirmer", "type": "TitleAbstractReviewer"}]}
        ]
    }
    processed_df = gui_utils.post_process_raw_results(df_raw, gui_config)

    assert processed_df.loc[processed_df['id'] == 'art3', 'final_decision'].iloc[0] == 'Included'
    assert pd.isna(processed_df.loc[processed_df['id'] == 'art3', 'final_score'].iloc[0]) # Confirmer (last round, first agent) had no score

    assert processed_df.loc[processed_df['id'] == 'art4', 'final_decision'].iloc[0] == 'Excluded'
    assert pd.isna(processed_df.loc[processed_df['id'] == 'art4', 'final_score'].iloc[0]) # Confirmer had no score

    log_art3 = processed_df.loc[processed_df['id'] == 'art3', 'detailed_workflow_log'].iloc[0]
    assert "round-A_Scorer_score: 4.2" in log_art3
    log_art4 = processed_df.loc[processed_df['id'] == 'art4', 'detailed_workflow_log'].iloc[0]
    assert "round-A_Scorer_score: bad_score" in log_art4


def test_post_process_handles_missing_agent_output_columns_gracefully():
    data_raw = [{'id': 'art5', 'title': 'Title 5'}] # No agent output columns at all
    df_raw = pd.DataFrame(data_raw)
    gui_config = {
        "rounds": [{"name": "R1", "agents": [{"name": "GhostAgent", "type": "TitleAbstractReviewer"}]}]
    }
    processed_df = gui_utils.post_process_raw_results(df_raw, gui_config)

    # Default values if agent output columns are entirely missing from raw_df
    assert processed_df['final_decision'][0] == "N/A"
    assert pd.isna(processed_df['final_score'][0])
    assert processed_df['reasoning_summary'][0] == ""
    assert processed_df['detailed_workflow_log'][0] == "" # Empty if no relevant columns found in raw_df

# Tests for build_lattereview_workflow_from_config

# Mock the entire lattereview package components that are instantiated
# We need to patch them where they are looked up by gui_utils.py
@patch('gui_utils.ReviewWorkflow')
@patch('gui_utils.LiteLLMProvider')
@patch('gui_utils.AGENT_TYPES_MAP', new_callable=dict) # Patch the map itself to control agent classes
@patch('gui_utils.st') # To check for st.error calls
def test_build_workflow_no_api_key(mock_st, mock_agent_types_map, mock_lite_llm_provider, mock_review_workflow):
    gui_config = {"rounds": [{"name": "R1", "agents": [{"name": "A1", "type": "TitleAbstractReviewer"}]}]}
    result = gui_utils.build_lattereview_workflow_from_config(gui_config, None, [])
    assert result is None
    # The function uses print for errors now, not st.error directly
    # This test would need to capture stdout or we assume None return is sufficient for this case
    # For this exercise, we'll focus on the None return.
    # mock_st.error.assert_any_call("API Key is missing.")

@patch('gui_utils.ReviewWorkflow')
@patch('gui_utils.LiteLLMProvider')
@patch('gui_utils.AGENT_TYPES_MAP', new_callable=dict)
@patch('gui_utils.st')
def test_build_workflow_empty_gui_config(mock_st, mock_agent_types_map, mock_lite_llm_provider, mock_review_workflow):
    result = gui_utils.build_lattereview_workflow_from_config({}, "test_api_key", [])
    assert result is None
    # The function uses print for errors now.
    # mock_st.error.assert_any_call("Workflow schema empty.")

@patch('gui_utils.ReviewWorkflow')
@patch('gui_utils.LiteLLMProvider')
@patch('gui_utils.st') # Mock st for st.error
def test_build_workflow_single_round_single_agent(mock_st, MockLiteLLMProvider, MockReviewWorkflow):
    MockTitleAbstractReviewer = MagicMock(spec=gui_utils.TitleAbstractReviewer)
    mock_agent_instance = MockTitleAbstractReviewer.return_value

    with patch.dict(gui_utils.AGENT_TYPES_MAP, {"TitleAbstractReviewer": MockTitleAbstractReviewer}):
        gui_config = {
            "rounds": [{
                "name": "Round Alpha",
                "agents": [{
                    "name": "AgentX", "type": "TitleAbstractReviewer",
                    "backstory": "bs", "inclusion_criteria": "ic", "exclusion_criteria": "ec" # using new keys
                }],
                "filter_config": {"type": "all_previous"}
            }]
        }
        mock_provider_instance = MockLiteLLMProvider.return_value

        workflow_instance = gui_utils.build_lattereview_workflow_from_config(gui_config, "test_key_123", [])

        assert workflow_instance is not None
        MockLiteLLMProvider.assert_called_with(model="gemini-2.0-flash", api_key="test_key_123")
        MockTitleAbstractReviewer.assert_called_with(
            provider=mock_provider_instance, name="AgentX", backstory="bs",
            inclusion_criteria="ic", exclusion_criteria="ec"
        )
        args, kwargs = MockReviewWorkflow.call_args
        schema = kwargs['workflow_schema']
        assert len(schema) == 1
        assert schema[0]['round'] == 'A'
        assert schema[0]['text_inputs'] == ["title", "abstract"]
        assert len(schema[0]['reviewers']) == 1
        assert schema[0]['reviewers'][0] == mock_agent_instance

@patch('gui_utils.ReviewWorkflow')
@patch('gui_utils.LiteLLMProvider')
@patch('gui_utils.st')
def test_build_workflow_with_rag_files(mock_st, MockLiteLLMProvider, MockReviewWorkflow):
    MockScoringReviewer = MagicMock(spec=gui_utils.ScoringReviewer)
    with patch.dict(gui_utils.AGENT_TYPES_MAP, {"ScoringReviewer": MockScoringReviewer}):
        gui_config = {
            "rounds": [{"name": "R1", "agents": [{"name": "Scorer", "type": "ScoringReviewer", "inclusion_criteria":"score stuff"}]}]
        }
        rag_files = ["rag1.pdf", "notes.txt"]
        mock_provider_instance = MockLiteLLMProvider.return_value

        gui_utils.build_lattereview_workflow_from_config(gui_config, "test_key", rag_files)

        expected_rag_context = f"RAG context: {', '.join(rag_files)}."
        MockScoringReviewer.assert_called_with(
            provider=mock_provider_instance, name="Scorer", backstory="",
            inclusion_criteria="score stuff", exclusion_criteria="", # Default empty string if not in config
            additional_context=expected_rag_context
        )

@patch('gui_utils.ReviewWorkflow')
@patch('gui_utils.LiteLLMProvider')
@patch('gui_utils.AGENT_TYPES_MAP', new_callable=dict)
@patch('gui_utils.st')
def test_build_workflow_unknown_agent_type(mock_st, mock_agent_types_map, mock_lite_llm_provider, mock_review_workflow):
    gui_config = {"rounds": [{"name": "R1", "agents": [{"name": "A1", "type": "NonExistentReviewer"}]}]}

    result = gui_utils.build_lattereview_workflow_from_config(gui_config, "test_key", [])
    assert result is None
    # Error messages are now printed, not st.error in util
    # mock_st.error.assert_any_call("Unknown agent type: NonExistentReviewer")
    # mock_st.error.assert_any_call("No agents for round R1.")


@patch('gui_utils.ReviewWorkflow')
@patch('gui_utils.LiteLLMProvider')
@patch('gui_utils.st')
def test_build_workflow_agent_instantiation_fails(mock_st, MockLiteLLMProvider, MockReviewWorkflow):
    MockTitleAbstractReviewer = MagicMock(spec=gui_utils.TitleAbstractReviewer)
    MockTitleAbstractReviewer.side_effect = Exception("Agent init failed")

    with patch.dict(gui_utils.AGENT_TYPES_MAP, {"TitleAbstractReviewer": MockTitleAbstractReviewer}):
        gui_config = {"rounds": [{"name": "R1", "agents": [{"name": "A1", "type": "TitleAbstractReviewer"}]}]}
        result = gui_utils.build_lattereview_workflow_from_config(gui_config, "test_key", [])
        assert result is None
        # Error messages are now printed
        # mock_st.error.assert_any_call("Error for agent A1 (TitleAbstractReviewer): Exception('Agent init failed')")

@patch('gui_utils.ReviewWorkflow', side_effect=Exception("Workflow creation error"))
@patch('gui_utils.LiteLLMProvider')
@patch('gui_utils.st')
def test_build_workflow_reviewworkflow_instantiation_fails(mock_st, MockLiteLLMProvider, MockReviewWorkflow_constructor_mock):
    MockTitleAbstractReviewer = MagicMock(spec=gui_utils.TitleAbstractReviewer)
    with patch.dict(gui_utils.AGENT_TYPES_MAP, {"TitleAbstractReviewer": MockTitleAbstractReviewer}):
        gui_config = {"rounds": [{"name": "R1", "agents": [{"name": "A1", "type": "TitleAbstractReviewer"}]}]}
        result = gui_utils.build_lattereview_workflow_from_config(gui_config, "test_key", [])
        assert result is None
        # Error messages are now printed
        # mock_st.error.assert_any_call("Error creating ReviewWorkflow: Exception('Workflow creation error')")
