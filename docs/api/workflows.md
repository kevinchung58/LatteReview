# Workflows Module Documentation

This module provides workflow management functionality for the LatteReview package, implementing multi-agent review orchestration.

## Overview

The workflows module consists of one main class:

- `ReviewWorkflow`: A class that orchestrates multi-agent review processes with support for sequential rounds and filtering

## ReviewWorkflow

### Description

The `ReviewWorkflow` class manages review workflows where multiple agents can review items across different rounds. It handles the orchestration of reviews, manages outputs, and provides content validation and cost tracking.

### Class Definition

```python
class ReviewWorkflow(pydantic.BaseModel):
    workflow_schema: List[Dict[str, Any]]
    memory: List[Dict] = list()
    reviewer_costs: Dict = dict()
    total_cost: float = 0.0
    verbose: bool = True
```

### Key Attributes

- `workflow_schema`: List of dictionaries defining the review process structure
- `memory`: List storing the workflow's execution history
- `reviewer_costs`: Dictionary tracking costs per reviewer and round
- `total_cost`: Total accumulated cost of all reviews
- `verbose`: Flag to enable/disable logging output
- `reviewer_names`: Automatically generated list of reviewer identifiers

### Methods

#### `__call__()`

Execute the workflow on provided data.

```python
async def __call__(self, data: Union[pd.DataFrame, Dict[str, Any]]) -> pd.DataFrame:
    # Execute workflow on DataFrame or dictionary input
    # Returns DataFrame with review results
```

#### `run()`

Core method to execute the review workflow.

```python
async def run(self, data: pd.DataFrame) -> pd.DataFrame:
    # Execute main review workflow
    # Process each round sequentially
    # Returns updated DataFrame with review results
```

#### `get_total_cost()`

Get total cost of workflow execution.

```python
def get_total_cost(self) -> float:
    # Return sum of all review costs
```

#### Internal Methods

- `_create_content_hash()`: Generate hash for content tracking
- `_format_input_text()`: Format input for reviewers
- `_log()`: Handle logging based on verbose setting

## Usage Examples

### Creating a Basic Review Workflow

```python
from lattereview.workflows import ReviewWorkflow
from lattereview.agents import ScoringReviewer
from lattereview.providers import LiteLLMProvider

# Create reviewers
reviewer1 = ScoringReviewer(
    provider=LiteLLMProvider(model="gpt-4"),
    name="Initial",
    scoring_task="Initial paper screening"
)

reviewer2 = ScoringReviewer(
    provider=LiteLLMProvider(model="gpt-4"),
    name="Expert",
    scoring_task="Detailed technical review"
)

# Define workflow schema
workflow_schema = [
    {
        "round": 'A',
        "reviewers": reviewer1,
        "inputs": ["title", "abstract"]
    },
    {
        "round": 'B',
        "reviewers": reviewer2,
        "inputs": ["title", "abstract", "round-A_Initial_output"],
        "filter": lambda row: row["round-A_Initial_score"] > 3
    }
]

# Create and run workflow
workflow = ReviewWorkflow(workflow_schema=workflow_schema)
results = await workflow(input_data)
```

### Understanding Workflow Construction

A workflow is defined by a list of dictionaries where each dictionary represents a review round. The rounds are executed sequentially in the order they appear in the list. Each round dictionary must contain:

Required Arguments:

- `round`: A string identifier for the round (e.g., 'A', 'B', '1', 'initial')
- `reviewers`: A single ScoringReviewer or list of ScoringReviewers
- `inputs`: A string or list of strings representing DataFrame column names to use

Optional Arguments:

- `filter`: A lambda function that determines which rows to review in this round. This function:

  - Receives each row of the DataFrame as a pandas Series object
  - Is applied to every row at the start of each round
  - Must return a boolean value (True/False)
  - Has access to all columns in the DataFrame, including outputs from previous rounds
  - Determines whether the row should be included in the current round's review

The workflow automatically generates output columns for each reviewer in the format:

- `round-{round_id}_{reviewer.name}_output`: Raw reviewer output
- `round-{round_id}_{reviewer.name}_score`: Numerical score
- `round-{round_id}_{reviewer.name}_reasoning`: Reasoning text

These output columns can be referenced in subsequent rounds as inputs or in filter conditions.

### Running Complex Reviews

Here are examples of increasingly complex workflow patterns:

#### 1. Basic Multi-Reviewer Round

Multiple reviewers examining the same content:

```python
workflow_schema = [
    {
        "round": 'A',
        "reviewers": [reviewer1, reviewer2],
        "inputs": ["title", "abstract"]
    }
]
```

#### 2. Sequential Review with Dependencies

One reviewer examining previous reviews:

```python
workflow_schema = [
    {
        "round": 'A',
        "reviewers": initial_reviewer,
        "inputs": ["title", "abstract"]
    },
    {
        "round": 'B',
        "reviewers": expert_reviewer,
        "inputs": [
            "title",
            "abstract",
            "round-A_initial_reviewer_score",
            "round-A_initial_reviewer_reasoning"
        ]
    }
]
```

#### 3. Disagreement Resolution Pattern

A third reviewer resolving disagreements:

```python
workflow_schema = [
    {
        "round": 'A',
        "reviewers": [reviewer1, reviewer2],
        "inputs": ["title", "abstract"]
    },
    {
        "round": 'B',
        "reviewers": arbitrator,
        "inputs": [
            "title",
            "abstract",
            "round-A_reviewer1_score",
            "round-A_reviewer2_score",
            "round-A_reviewer1_reasoning",
            "round-A_reviewer2_reasoning"
        ],
        "filter": lambda row: abs(
            row["round-A_reviewer1_score"] -
            row["round-A_reviewer2_score"]
        ) > 2
    }
]
```

#### 4. Multi-Stage Review with Filtering

Progressive review stages with filtering:

```python
workflow_schema = [
    # Initial screening
    {
        "round": 'screening',
        "reviewers": screening_reviewer,
        "inputs": ["title", "abstract"]
    },
    # Detailed review of passing papers
    {
        "round": 'detailed',
        "reviewers": [expert1, expert2],
        "inputs": ["title", "abstract", "full_text"],
        "filter": lambda row: row["round-screening_screening_reviewer_score"] >= 4
    },
    # Final decision for contested papers
    {
        "round": 'final',
        "reviewers": senior_reviewer,
        "inputs": [
            "title",
            "abstract",
            "round-detailed_expert1_score",
            "round-detailed_expert2_score",
            "round-detailed_expert1_reasoning",
            "round-detailed_expert2_reasoning"
        ],
        "filter": lambda row:
            row["round-detailed_expert1_score"] != row["round-detailed_expert2_score"]
    }
]
```

#### 5. Hierarchical Review with Validation

Multiple review levels with validation checks:

```python
workflow_schema = [
    # Initial automated screening
    {
        "round": 'auto',
        "reviewers": auto_reviewer,
        "inputs": ["title", "abstract", "metrics"]
    },
    # Human validation of uncertain cases
    {
        "round": 'validation',
        "reviewers": human_validator,
        "inputs": [
            "title",
            "abstract",
            "round-auto_auto_reviewer_score",
            "round-auto_auto_reviewer_reasoning"
        ],
        "filter": lambda row:
            2 <= row["round-auto_auto_reviewer_score"] <= 4
    },
    # Expert review of validated papers
    {
        "round": 'expert',
        "reviewers": domain_expert,
        "inputs": ["title", "abstract", "full_text"],
        "filter": lambda row:
            row["round-validation_human_validator_score"] >= 3 or
            row["round-auto_auto_reviewer_score"] >= 4
    }
]
```

### Handling Results

```python
# Execute workflow
workflow = ReviewWorkflow(workflow_schema=workflow_schema)
try:
    results_df = await workflow(input_df)

    # Access costs
    total_cost = workflow.get_total_cost()
    per_reviewer = workflow.reviewer_costs

    # Access results
    round_a_scores = results_df["round-A_Initial_score"]
    round_b_reasoning = results_df["round-B_Expert_reasoning"]

except ReviewWorkflowError as e:
    print(f"Workflow failed: {e}")
```

## Error Handling

The module uses `ReviewWorkflowError` for all workflow-related errors:

```python
class ReviewWorkflowError(Exception):
    """Base exception for workflow-related errors."""
    pass
```

Common error scenarios:

- Invalid workflow schema
- Missing input columns
- Reviewer initialization failures
- Content validation errors
- Output processing failures

## Best Practices

1. Schema Design

   - Use meaningful round identifiers
   - Design filter functions carefully
   - Consider round dependencies

2. Data Management

   - Validate input data structure
   - Handle missing values appropriately
   - Use appropriate column names

3. Cost Control

   - Monitor per-round costs
   - Set appropriate concurrent request limits
   - Track total workflow costs

4. Error Handling
   - Implement proper exception handling
   - Validate workflow schema
   - Monitor review outputs

## Limitations

- Sequential round execution only
- Memory grows with number of reviews
- No direct reviewer communication
- Limited to DataFrame-based workflows
- Requires async/await syntax
- Filter functions must be serializable
