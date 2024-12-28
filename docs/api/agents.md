# Agents Module Documentation

This module provides the core agent functionality for the LatteReview package, implementing agent-based review workflows. The updated version supports text and image inputs for review tasks, with a newly introduced `AbstractionReviewer` agent in addition to the existing `ScoringReviewer` agent.

## Overview

The agents module consists of three main classes:

- `BaseAgent`: An abstract base class that provides core agent functionality.
- `ScoringReviewer`: A concrete implementation for reviewing and scoring items.
- `AbstractionReviewer`: A new agent designed for structured extraction tasks from input content.

## BaseAgent Class

### Overview

`BaseAgent` serves as the abstract base class for all agents in the system. It provides core functionality for handling prompts, managing agent state, and processing examples.

### Class Definition

```python
class BaseAgent(BaseModel):
    generic_prompt: Optional[str] = None
    response_format: Dict[str, Any] = None
    provider: Optional[Any] = None
    model_args: Dict[str, Any] = Field(default_factory=dict)
    max_concurrent_requests: int = DEFAULT_CONCURRENT_REQUESTS
    name: str = "BaseAgent"
    backstory: str = "a generic base agent"
    input_description: str = ""
    examples: Union[str, List[Union[str, Dict[str, Any]]]] = None
    reasoning: ReasoningType = ReasoningType.BRIEF
    system_prompt: Optional[str] = None
    formatted_prompt: Optional[str] = None
    cost_so_far: float = 0
    memory: List[Dict[str, Any]] = []
    identity: Dict[str, Any] = {}
    additional_context: Optional[Union[Callable, str]] = ""
```

### Key Attributes

- **`generic_prompt`**: A template for constructing prompts.
- **`response_format`**: Dictionary defining the expected format of agent responses.
- **`provider`**: LLM provider instance (optional).
- **`model_args`**: Configuration arguments for the language model.
- **`max_concurrent_requests`**: Maximum number of concurrent requests.
- **`name`**: Agent's identifier.
- **`backstory`**: Agent's background narrative.
- **`input_description`**: Description of expected input.
- **`examples`**: Training examples as string, list of strings, or dictionaries.
- **`reasoning`**: Type of reasoning using the `ReasoningType` enum.
- **`system_prompt`**: Optional system prompt for the agent.
- **`formatted_prompt`**: Optional formatted prompt for the agent.
- **`cost_so_far`**: Tracks the total cost incurred by the agent.
- **`memory`**: List storing the agent's interaction history.
- **`identity`**: Agent's configuration dictionary.
- **`additional_context`**: Optional context provider as callable or string.

### Key Methods

- **Setup and Initialization**

  - `setup(self)`: Abstract method for initialization.
  - `reset_memory(self)`: Clears the agent's memory and resets cost tracking.

- **Prompt Building**

  - `_build_system_prompt(self)`: Constructs the system prompt containing the agent's identity and task description.
  - `_process_prompt(self, base_prompt: str, item_dict: Dict[str, Any])`: Creates an input prompt with variable substitution.

- **Processing Functions**
  - `_process_reasoning(self, reasoning: Union[str, ReasoningType])`: Converts reasoning type into appropriate prompt text.
  - `_process_examples(self, examples: Union[str, Dict[str, Any], List[Union[str, Dict[str, Any]]]])`: Formats examples into a consistent string format.

---

## ScoringReviewer Class

### Overview

`ScoringReviewer` extends `BaseAgent` to implement specialized reviewing capabilities with scoring functionality. This class supports both text and image inputs.

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
    generic_prompt: Optional[str] = Field(default=None)
    input_description: str = "article title/abstract"
    reasoning: ReasoningType = ReasoningType.BRIEF
    max_retries: int = DEFAULT_MAX_RETRIES
```

### Key Attributes

- **`response_format`**: Defines expected response structure with reasoning, score, and certainty.
- **`scoring_task`**: Description of the scoring criteria.
- **`scoring_set`**: Valid score values.
- **`scoring_rules`**: Rules governing the scoring process.
- **`generic_prompt`**: Template for input prompts.
- **`input_description`**: Description of the input being reviewed.
- **`reasoning`**: Type of reasoning required for the review.
- **`max_retries`**: Maximum retry attempts for failed reviews.

### Key Methods

- **Review Operations**
  - `review_items(self, text_input_strings: List[str], image_path_lists: List[List[str]] = None)`: Reviews multiple items concurrently with error handling.
  - `review_item(self, text_input_string: str, image_path_list: List[str] = [])`: Reviews a single item with retry logic and additional context handling.

---

## AbstractionReviewer Class

### Overview

`AbstractionReviewer` is a new agent introduced for extracting structured information from input content. It specializes in tasks such as key-value extraction based on predefined instructions and response formats.

### Class Definition

```python
class AbstractionReviewer(BaseAgent):
    response_format: Dict[str, Any]
    instructions: Dict[str, Any]
    input_description: str = "article title/abstract"
    max_retries: int = DEFAULT_MAX_RETRIES
```

### Key Attributes

- **`response_format`**: Defines the structure of the extracted response. Should be a dictionary with {key: expected format} structure.
- **`instructions`**: Detailed guidelines for extraction tasks. Should be a dictionary with {key: instructions_for_key} structure.
- **`input_description`**: Description of the input being reviewed.
- **`max_retries`**: Maximum retry attempts for failed reviews.

### Key Methods

- **Review Operations**
  - `review_items(self, text_input_strings: List[str], image_path_lists: List[List[str]] = None)`: Reviews multiple items concurrently, extracting specified keys.
  - `review_item(self, text_input_string: str, image_path_list: List[str] = [])`: Extracts structured information from a single input item.

---

## Error Handling

The package implements comprehensive error handling through:

- Custom `AgentError` exception class.
- Retry mechanisms for failed operations.
- Input validation using Pydantic.
- Warning generation during retries.

---

## Usage Examples

### ScoringReviewer Example

```python
from lattereview.agents import ScoringReviewer
from lattereview.providers import OpenAIProvider

# Create a ScoringReviewer
reviewer = ScoringReviewer(
    provider=OpenAIProvider(model="gpt-4o"),
    name="QualityReviewer",
    backstory="an expert in quality assessment",
    scoring_task="Evaluate content quality",
    scoring_set=[1, 2, 3, 4, 5],
    reasoning=ReasoningType.COT
)

# Review items
text_items = ["Content A", "Content B"]
image_paths = [["path/to/image1.png"], []]
results, costs = await reviewer.review_items(text_items, image_paths)
```

### AbstractionReviewer Example

```python
from lattereview.agents import AbstractionReviewer
from lattereview.providers import OpenAIProvider

# Create an AbstractionReviewer
abstraction_reviewer = AbstractionReviewer(
    provider=OpenAIProvider(model="gpt-4o"),
    response_format={"title": str, "abstract": str},
    instructions={"title": "Extract the article title", "abstract": "Extract the abstract text"},
    input_description="Article title and abstract for structured extraction"
)

# Extract structured information
text_items = ["Title: AI Advances\nAbstract: Recent AI breakthroughs..."]
results, costs = await abstraction_reviewer.review_items(text_items)
```

---

## Best Practices

1. **Error Handling**:
   - Implement retry mechanisms.
   - Monitor and log errors.
2. **Performance Optimization**:
   - Set appropriate concurrency limits.
   - Use batch processing.
3. **Prompt Engineering**:
   - Define clear and concise prompts.
   - Include examples for better understanding.

---

## Future Enhancements

- Improved memory management.
- Enhanced support for multi-agent collaboration.
- Additional functionalities for extraction and scoring tasks.
