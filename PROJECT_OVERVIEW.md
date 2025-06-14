# Project Overview: LatteReview 🤖☕

## Functionality

LatteReview is a powerful Python package designed to automate academic literature review processes through AI-powered agents. It aims to make reviewing numerous research articles an efficient and pleasant experience.

Key features of LatteReview include:

*   **Multi-agent review system:** Allows for customizable roles and expertise levels for each AI reviewer.
*   **Multiple review rounds:** Supports hierarchical decision-making workflows with several stages of review.
*   **Diverse content type review:** Capable of reviewing article titles, abstracts, custom texts, and even images using LLM-powered agents.
*   **Specialized reviewer agents:** Users can define agents with specific backgrounds and evaluation capabilities (e.g., scoring, concept abstraction, or custom-defined reviewers).
*   **Flexible review workflows:** Enables the creation of workflows where multiple agents operate in parallel or sequentially.
*   **Peer feedback analysis:** Reviewer agents can analyze feedback from other agents, cast votes, and suggest corrections.
*   **Context integration:** Enhances reviews with item-specific context, supporting use cases like Retrieval Augmented Generation (RAG).
*   **Broad LLM provider compatibility:** Integrates with various LLM providers through LiteLLM, including OpenAI and Ollama. This allows for model-agnostic integration with models like OpenAI, Gemini, Claude, Groq, and local models via Ollama.
*   **High-performance processing:** Utilizes asynchronous processing for efficient batch reviews.
*   **Standardized output:** Provides results in a standardized format with detailed scoring metrics and reasoning for transparency.
*   **Resource management:** Includes robust cost tracking and memory management systems.
*   **Extensible architecture:** Allows for the implementation of custom review workflows.
*   **RIS file support:** Supports RIS (Research Information Systems) file format for academic literature review.

## Architecture

LatteReview is structured around three main components: Agents, Providers, and Workflows.

*   **Agents:** These are the AI-powered reviewers responsible for evaluating the literature. LatteReview provides different types of agents:
    *   `TitleAbstractReviewer`: Focuses on reviewing titles and abstracts.
    *   `ScoringReviewer`: Assigns scores based on defined criteria.
    *   `AbstractionReviewer`: Summarizes and abstracts key information from papers.
    *   Users can also create custom reviewer agents to suit specific needs.
    Each agent can be configured with a specific LLM, a "backstory" or persona, inclusion/exclusion criteria, and other parameters.

*   **Providers:** These components handle the communication with the Large Language Models (LLMs). LatteReview supports various providers:
    *   `LiteLLMProvider`: A versatile provider that supports a wide range of LLMs including OpenAI, Anthropic (Claude), Gemini, Groq, and more. This is the recommended provider.
    *   `OpenAIProvider`: For direct integration with OpenAI and Gemini APIs.
    *   `OllamaProvider`: Optimized for running local models via Ollama.
    This flexible provider system allows users to choose the most suitable LLM for each agent and task.

*   **Workflows:** Workflows define the structure and sequence of the review process.
    *   `ReviewWorkflow`: This class allows users to define multi-stage review processes.
    *   A workflow is defined by a schema that specifies rounds of review, the agents involved in each round, the text inputs for the agents, and filters to determine which items proceed to subsequent rounds.
    *   For example, a workflow can have an initial round with multiple junior agents reviewing titles and abstracts, followed by a second round where a senior agent reviews items where the junior agents disagreed.
    *   Workflows handle the flow of data, manage the execution of agent reviews (asynchronously for efficiency), and aggregate the results.

These components interact to create a flexible and powerful system for automated literature reviews. Data (e.g., a list of articles) is fed into a Workflow. The Workflow then directs specified Agents to review the data according to the defined stages. Agents, in turn, utilize Providers to interact with LLMs to perform their review tasks. The results, including decisions, scores, and reasoning, are then collected and returned by the Workflow.
