LatteReview enables you to create custom literature review workflows with multiple AI reviewers. Each reviewer can use different models and providers based on your needs. Please follow the below steps to perform a review task with LatteReview.

## Step 1: Set Up API Keys

To use LatteReview with different LLM engines (OpenAI, Anthropic, Google, etc.), you'll need to set up the API keys for the specific providers you plan to use. For example, if you're only using OpenAI models, you only need the OpenAI API key. Here are three ways to set up your API keys:

1. Using python-dotenv (Recommended):
   - Create a `.env` file in your project directory and add only the keys you need:

```text
# .env file - Example keys (add only what you need)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

- Load it in your code:

```python
from dotenv import load_dotenv
load_dotenv()  # Load before importing any providers
```

2. Setting environment variables directly:

```bash
# Example: Set only the keys for providers you're using
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

3. Passing API keys directly to providers (supported by some providers):

```python
from lattereview.providers import OpenAIProvider
provider = OpenAIProvider(api_key="your-openai-key")  # Optional, will use environment variable if not provided
```

Note: No API keys are needed if you're exclusively using local models through Ollama.

## Step 2: Prepare Your Data

Your input data should be in a CSV or Excel file with columns for the content you want to review. The column names should match the `inputs` specified in your workflow:

```python
# Load your data
data = pd.read_excel("articles.xlsx")

# Example data structure:
data = pd.DataFrame({
    'title': ['Paper 1 Title', 'Paper 2 Title'],
    'abstract': ['Paper 1 Abstract', 'Paper 2 Abstract']
})
```

## Step 3: Create Reviewers

Create reviewer agents by configuring `ScoringReviewer` objects. Each reviewer needs:

- A provider (e.g., LiteLLMProvider, OpenAIProvider, OllamaProvider)
- A unique name
- A scoring task and rules
- Optional configuration like temperature and model parameters

```python
# Example of creating a scoring reviewer
reviewer1 = ScoringReviewer(
    provider=LiteLLMProvider(model="gpt-4o-mini"),  # Choose your model provider
    name="Alice",                                    # Unique name for the reviewer
    scoring_task="Your review task description",     # What to evaluate
    score_set=[1, 2, 3, 4, 5],                      # Possible scores
    scoring_rules="Rules for assigning scores",      # How to score
    model_args={"temperature": 0.1}                  # Model configuration
)
```

## Step 4: Create Review Workflow

Define your workflow by specifying review rounds, reviewers, and input columns. The workflow automatically creates output columns for each reviewer based on their name and review round. For each reviewer, three columns are created:

- `round-{ROUND}_{REVIEWER_NAME}_output`: Full output dictionary
- `round-{ROUND}_{REVIEWER_NAME}_score`: Extracted score
- `round-{ROUND}_{REVIEWER_NAME}_reasoning`: Extracted reasoning

These automatically generated columns can be used as inputs in subsequent rounds, allowing later reviewers to access and evaluate the outputs of previous reviewers:

```python
workflow = ReviewWorkflow(
    workflow_schema=[
        {
            "round": 'A',               # First round
            "reviewers": [reviewer1, reviewer2],
            "inputs": ["title", "abstract"]  # Original data columns
        },
        {
            "round": 'B',               # Second round
            "reviewers": [expert],
            # Access both original columns and previous reviewers' outputs
            "inputs": ["title", "abstract", "round-A_reviewer1_output", "round-A_reviewer2_score"],
            # Optional filter to review only certain cases
            "filter": lambda row: row["round-A_reviewer1_score"] != row["round-A_reviewer2_score"]
        }
    ]
)
```

In this example, the expert reviewer in round B can access both the original data columns and the outputs from round A's reviewers. The filter ensures the expert only reviews cases where the first two reviewers disagreed.

## Step 5: Run the Workflow

Execute the workflow and get results:

```python
# Run workflow
results = asyncio.run(workflow(data))  # Returns DataFrame with all results

# Results include original columns plus new columns for each reviewer:
# - round-{ROUND}_{REVIEWER_NAME}_output: Full output dictionary
# - round-{ROUND}_{REVIEWER_NAME}_score: Extracted score
# - round-{ROUND}_{REVIEWER_NAME}_reasoning: Extracted reasoning
```

## Complete Working Example

```python
from lattereview.providers import LiteLLMProvider
from lattereview.agents import ScoringReviewer
from lattereview.workflows import ReviewWorkflow
import pandas as pd
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# First Reviewer: Conservative approach
reviewer1 = ScoringReviewer(
    provider=LiteLLMProvider(model="gpt-4o-mini"),
    name="Alice",
    backstory="a radiologist with expertise in systematic reviews",
    scoring_task="Evaluate how relevant the article is to artificial intelligence applications in radiology",
    score_set=[1, 2, 3, 4, 5],
    scoring_rules="Rate the relevance on a scale of 1 to 5, where 1 means not relevant to AI in radiology, and 5 means directly focused on AI in radiology",
    model_args={"temperature": 0.1}
)

# Second Reviewer: More exploratory approach
reviewer2 = ScoringReviewer(
    provider=LiteLLMProvider(model="gemini/gemini-1.5-flash"),
    name="Bob",
    backstory="a computer scientist specializing in medical AI",
    scoring_task="Evaluate how relevant the article is to artificial intelligence applications in radiology",
    score_set=[1, 2, 3, 4, 5],
    scoring_rules="Rate the relevance on a scale of 1 to 5, where 1 means not relevant to AI in radiology, and 5 means directly focused on AI in radiology",
    model_args={"temperature": 0.8}
)

# Expert Reviewer: Resolves disagreements
expert = ScoringReviewer(
    provider=LiteLLMProvider(model="gpt-4o"),
    name="Carol",
    backstory="a professor of AI in medical imaging",
    scoring_task="Review Alice and Bob's relevance assessments of this article to AI in radiology",
    score_set=[1, 2],
    scoring_rules='Score 1 if you agree with Alice\'s assessment, 2 if you agree with Bob\'s assessment',
    model_args={"temperature": 0.1}
)

# Define workflow
workflow = ReviewWorkflow(
    workflow_schema=[
        {
            "round": 'A',  # First round: Initial review by both reviewers
            "reviewers": [reviewer1, reviewer2],
            "inputs": ["title", "abstract"]
        },
        {
            "round": 'B',  # Second round: Expert reviews only disagreements
            "reviewers": [expert],
            "inputs": ["title", "abstract", "round-A_Alice_output", "round-A_Bob_output"],
            "filter": lambda row: row["round-A_Alice_score"] != row["round-A_Bob_score"]
        }
    ]
)

# Load and process your data
data = pd.read_excel("articles.xlsx")  # Must have 'title' and 'abstract' columns
results = asyncio.run(workflow(data))  # Returns a pandas DataFrame with all original and output columns

# Save results
results.to_csv("review_results.csv", index=False)
```
