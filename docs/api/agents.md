# Agents Module Documentation

This module provides the core agent functionality for the LatteReview package, implementing agent-based review workflows. The updated version supports text and image inputs for review tasks.

## Overview

The agents module consists of two main classes:

- `BaseAgent`: An abstract base class that provides core agent functionality
- `ScoringReviewer`: A concrete implementation for reviewing and scoring items

## BaseAgent Class

### Overview

`BaseAgent` serves as the abstract base class for all agents in the system. It provides core functionality for handling prompts, managing agent state, and processing examples.

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
    formatted_prompt: Optional[str] = None
    cost_so_far: float = 0
    memory: List[Dict[str, Any]] = []
    identity: Dict[str, Any] = {}
    additional_context: Optional[Union[Callable, str]] = ""
```

### Key Attributes

- `response_format`: Dictionary defining the expected format of agent responses
- `provider`: LLM provider instance (optional)
- `model_args`: Configuration arguments for the language model (defaults to empty dict using default_factory)
- `max_concurrent_requests`: Maximum number of concurrent requests (default: DEFAULT_CONCURRENT_REQUESTS)
- `name`: Agent's identifier (default: "BaseAgent")
- `backstory`: Agent's background narrative (default: "a generic base agent")
- `input_description`: Description of expected input (default: empty string)
- `examples`: Training examples as string, list of strings, or list of dictionaries (default: None)
- `reasoning`: Type of reasoning using ReasoningType enum (default: ReasoningType.BRIEF)
- `system_prompt`: Optional system prompt for the agent (default: None)
- `formatted_prompt`: Optional formatted prompt for the agent (default: None)
- `cost_so_far`: Tracks the total cost incurred by the agent (default: 0)
- `memory`: List storing agent's interaction history as dictionaries (default: empty list)
- `identity`: Agent's configuration dictionary (default: empty dict)
- `additional_context`: Optional context provider as callable or string (default: empty string). If callable, expects an async function that accepts a single input review item (e.g., to retrieve the relevant context for that unique item in RAG use cases)

### Methods

#### Setup and Initialization

```python
def __init__(self, **data: Any) -> None
```

Initializes the agent with error handling and type validation.

```python
def setup(self) -> None
```

Abstract method that must be implemented by subclasses for initialization.

#### Prompt Building

```python
def _build_system_prompt(self) -> str
```

Constructs the system prompt containing the agent's identity and task description.

```python
def _process_prompt(self, base_prompt: str, item_dict: Dict[str, Any]) -> str
```

Creates an input prompt with variable substitution from the item dictionary.

#### Processing Functions

```python
def _process_reasoning(self, reasoning: Union[str, ReasoningType]) -> str
```

Converts reasoning type into appropriate prompt text.

```python
def _process_examples(self, examples: Union[str, Dict[str, Any], List[Union[str, Dict[str, Any]]]]) -> str
```

Formats examples into a consistent string format.

```python
def _process_additional_context(self, context: str)
```

Processes additional context into a formatted string.

#### Memory Management

```python
def reset_memory(self) -> None
```

Clears the agent's memory and resets cost tracking.

## ScoringReviewer Class

### Overview

`ScoringReviewer` extends `BaseAgent` to implement specialized reviewing capabilities with scoring functionality. The updated version supports image inputs in addition to text inputs.

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

- `response_format`: Defines expected response structure with reasoning, score, and certainty
- `scoring_task`: Description of the scoring criteria
- `scoring_set`: Valid score values
- `scoring_rules`: Rules governing the scoring process
- `generic_prompt`: Template for input prompts
- `max_retries`: Maximum retry attempts for failed reviews

### Methods

#### Review Operations

```python
async def review_items(self, text_input_strings: List[str], image_path_lists: List[List[str]] = None, tqdm_keywords: dict = None) -> List[Dict[str, Any]]
```

Reviews multiple items concurrently with progress tracking and error handling.

Parameters:

- `text_input_strings`: List of text items to review
- `image_path_lists`: List of lists containing image file paths for each review item
- `tqdm_keywords`: Optional keywords for progress bar customization

Returns:

- List of review results and associated costs

```python
async def review_item(self, text_input_string: str, image_path_list: List[str] = []) -> tuple[Dict[str, Any], Dict[str, float]]
```

Reviews a single item with retry logic and additional context handling.

Parameters:

- `text_input_string`: Text input for the review
- `image_path_list`: List of image paths related to the input

Returns:

- Tuple containing review result and associated cost

## Error Handling

The package implements comprehensive error handling through:

- Custom `AgentError` exception class
- Try-except blocks in all critical operations
- Warning generation for retry attempts
- Input validation using Pydantic

## Usage Examples

### Basic Usage

```python
from lattereview.agents import ScoringReviewer
from lattereview.providers import OpenAIProvider

# Create a reviewer
reviewer = ScoringReviewer(
    provider=OpenAIProvider(model="gpt-4"),
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

### Advanced Configuration

```python
# With additional context
reviewer = ScoringReviewer(
    provider=OpenAIProvider(model="gpt-4"),
    additional_context="Consider recent industry standards",
    max_concurrent_requests=5,
    max_retries=5,
    model_args={
        "temperature": 0.7,
        "max_tokens": 500
    }
)

# With dynamic context
async def get_context(item):
    # Fetch or compute context based on item
    return f"Context for {item}"

reviewer.additional_context = get_context
```

## Best Practices

1. Error Handling

   - Implement proper error handling for API calls
   - Use appropriate retry mechanisms
   - Monitor and log errors

2. Performance Optimization

   - Set appropriate concurrency limits
   - Use batch processing for multiple items
   - Implement caching when applicable

3. Resource Management

   - Monitor costs through `cost_so_far`
   - Regularly clear agent memory
   - Set reasonable retry limits

4. Prompt Engineering
   - Provide clear scoring criteria
   - Use appropriate reasoning types
   - Include relevant examples

## Limitations

- Asynchronous operation required
- Provider-dependent capabilities
- Memory growth over time
- No inter-agent communication
- Rate limits based on provider

## Future Enhancements

Potential areas for improvement:

- Enhanced memory management
- Inter-agent communication
- Additional provider support
- Extended scoring capabilities
- Improved error recovery
