# Agents Module Documentation

This module provides the core agent functionality for the LatteReview package, implementing agent-based review workflows.

## Overview

The agents module consists of two main classes:

- `BaseAgent`: An abstract base class that provides core agent functionality
- `ScoringReviewer`: A concrete implementation for reviewing and scoring items

## BaseAgent

### Description

The `BaseAgent` class serves as an abstract base class for all agents in the system. It provides core functionality for handling prompts, managing agent state, and processing examples.

### Class Definition

```python
class BaseAgent(BaseModel):
    response_format: Dict[str, Any]
    provider: Optional[Any] = None
    model_args: Dict[str, Any] = Field(default_factory=dict)
    max_concurrent_requests: int = DEFAULT_CONCURRENT_REQUESTS
    name: str = "BaseAgent"
    backstory: str = "a generic base agent"
    input_description: str = ""
    examples: Union[str, List[Union[str, Dict[str, Any]]]] = None
    reasoning: ReasoningType = ReasoningType.BRIEF
    system_prompt: Optional[str] = None
    item_prompt: Optional[str] = None
    cost_so_far: float = 0
    memory: List[Dict[str, Any]] = []
    identity: Dict[str, Any] = {}
```

### Key Attributes

- `response_format`: Defines the expected format of agent responses, which now includes a mandatory `certainty` field.
- `provider`: The LLM provider instance used by the agent
- `model_args`: Arguments passed to the language model
- `max_concurrent_requests`: Maximum number of concurrent requests (default: 20)
- `name`: Agent's name
- `backstory`: Agent's background story
- `reasoning`: Type of reasoning (NONE, BRIEF, COT)
- `memory`: List storing agent's interactions
- `identity`: Dictionary containing agent's configuration

### Methods

#### `setup()`

Abstract method that must be implemented by subclasses to initialize the agent.

#### `build_system_prompt()`

Constructs the system prompt based on agent's configuration.

```python
def build_system_prompt(self) -> str:
    # Returns formatted system prompt containing agent's name, backstory,
    # task description, and expected output format
```

#### `build_item_prompt()`

Builds a prompt for a specific item with variable substitution.

```python
def build_item_prompt(self, base_prompt: str, item_dict: Dict[str, Any]) -> str:
    # Substitutes variables in base_prompt with values from item_dict
```

#### `process_reasoning()`

Processes the reasoning type into a prompt string.

```python
def process_reasoning(self, reasoning: Union[str, ReasoningType]) -> str:
    # Converts reasoning type to corresponding prompt text
```

#### `process_examples()`

Formats examples into a string suitable for prompting.

```python
def process_examples(self, examples: Union[str, Dict[str, Any],
                    List[Union[str, Dict[str, Any]]]]) -> str:
    # Formats examples into a consistent string format
```

## ScoringReviewer

### Description

The `ScoringReviewer` class implements a reviewer agent that can score items based on defined criteria. It extends `BaseAgent` with scoring-specific functionality.

### Class Definition

```python
class ScoringReviewer(BaseAgent):
    response_format: Dict[str, Any] = {
        "reasoning": str,
        "score": int,
        "certainty": int
    }
    scoring_task: Optional[str] = None
    scoring_set: List[int] = [1, 2]
    scoring_rules: str = "Your scores should follow the defined schema."
    generic_item_prompt: Optional[str] = Field(default=None)
    input_description: str = "article title/abstract"
    reasoning: ReasoningType = ReasoningType.BRIEF
    max_retries: int = DEFAULT_MAX_RETRIES
```

### Key Attributes

- `generic_item_prompt`: The path to the template but dynamic prompt used for the `ScoringReviewer`.
- `response_format`: The expected response format from the ScoringReviewer agent with three necessary keys: `reasoning`, `score`, and `certainty`.
- `scoring_task`: Description of the scoring task.
- `scoring_set`: List of valid scores (now supports 0 as a valid score)
- `scoring_rules`: Rules for scoring items
- `max_retries`: Maximum number of retry attempts for failed reviews

### Methods

#### `review_items()`

Reviews multiple items concurrently with progress tracking.

```python
async def review_items(self, items: List[str],
                      tqdm_keywords: dict = None) -> List[Dict[str, Any]]:
    # Reviews multiple items concurrently
    # Returns list of review results and associated costs
```

#### `review_item()`

Reviews a single item with retry logic.

```python
async def review_item(self, item: str) -> tuple[Dict[str, Any], Dict[str, float]]:
    # Reviews single item with retry mechanism
    # Returns review result and associated cost
```

## Usage Examples

### Creating a Basic Scoring Reviewer

```python
from lattereview.agents import ScoringReviewer
from lattereview.providers import OpenAIProvider

reviewer = ScoringReviewer(
    provider=OpenAIProvider(model="gpt-4"),
    name="ReviewerOne",
    backstory="an expert reviewer in scientific literature",
    scoring_task="Evaluate papers for methodology quality",
    scoring_set=[1, 2, 3, 4, 5],
    scoring_rules="Score 1-5 where 1 is poor and 5 is excellent",
    reasoning=ReasoningType.COT
)
```

### Running Reviews

```python
# Single item review
result, cost = await reviewer.review_item("Paper abstract text...")

# Multiple items review
items = ["Abstract 1...", "Abstract 2...", "Abstract 3..."]
results, total_cost = await reviewer.review_items(items)
```

### Customizing Review Behavior

```python
reviewer = ScoringReviewer(
    provider=OpenAIProvider(model="gpt-4"),
    max_concurrent_requests=10,  # Limit concurrent requests
    max_retries=5,              # Increase retry attempts
    model_args={                # Customize model behavior
        "temperature": 0.7,
        "max_tokens": 500
    }
)
```

## Error Handling

Common error scenarios:

- Provider initialization failures
- Prompt building errors
- Review process failures
- Response format validation errors

All operations are wrapped in try-except blocks with detailed error messages.

## Best Practices

1. Always initialize agents with appropriate providers
2. Set reasonable concurrency limits based on API constraints
3. Use appropriate reasoning types for your use case
4. Monitor costs through the `cost_so_far` attribute
5. Implement retry logic for robust production systems
6. Keep prompts and scoring rules clear and specific
7. Regularly clear agent memory for long-running processes

## Limitations

- Requires async/await syntax for operation
- Depends on external LLM providers
- Memory grows with usage (clear regularly)
- Rate limits depend on provider capabilities
- For now, agents cannot converse with each other.
