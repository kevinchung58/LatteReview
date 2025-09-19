# Project Overview: LatteReview 🤖☕

## Functionality

LatteReview is a powerful Python package designed to automate academic literature review processes through AI-powered agents. It aims to make reviewing numerous research articles an efficient and pleasant experience.

Key features of LatteReview include:

*   **Multi-agent review system:** Allows for customizable roles and expertise levels for each AI reviewer.
*   **Multiple review rounds:** Supports hierarchical decision-making workflows with several stages of review.
*   **Diverse content type review:** Capable of reviewing article titles, abstracts, custom texts, and even images using LLM-powered agents.
*   **Specialized reviewer agents:** Users can define agents with specific backgrounds and evaluation capabilities (e.g., scoring, concept abstraction, or custom-defined reviewers).
    *   : Focuses on reviewing titles and abstracts.
    *   : Assigns scores based on defined criteria.
    *   : Summarizes and abstracts key information from papers.
*   **Flexible review workflows:** Enables the creation of workflows where multiple agents operate in parallel or sequentially.
*   **Peer feedback analysis:** Reviewer agents can analyze feedback from other agents, cast votes, and suggest corrections (conceptual, depending on workflow design).
*   **Context integration:** Enhances reviews with item-specific context, supporting use cases like Retrieval Augmented Generation (RAG).
*   **Broad LLM provider compatibility:** Integrates with various LLM providers through LiteLLM, including OpenAI and Ollama. This allows for model-agnostic integration with models like OpenAI, Gemini, Claude, Groq, and local models via Ollama.
*   **High-performance processing:** Utilizes asynchronous processing for efficient batch reviews.
*   **Standardized output:** Provides results in a standardized format with detailed scoring metrics and reasoning for transparency.
*   **Resource management:** Includes robust cost tracking and memory management systems (features of the underlying LatteReview package).
*   **Extensible architecture:** Allows for the implementation of custom review workflows.
*   **RIS file support:** Supports RIS (Research Information Systems) file format for academic literature review.

## Architecture

LatteReview is structured around three main components: Agents, Providers, and Workflows.

*   **Agents:** These are the AI-powered reviewers responsible for evaluating the literature. LatteReview provides different types of agents, each configurable with a specific LLM, a "backstory" or persona, and task-specific criteria (like inclusion/exclusion criteria).
    *   : For initial screening based on titles and abstracts.
    *   : For quantitative evaluation against defined rubrics.
    *   : For extracting key information or concepts.
    *   Custom agents can also be developed by users.

*   **Providers:** These components handle the communication with the Large Language Models (LLMs). LatteReview's flexible provider system (primarily via ) allows use of models from OpenAI, Anthropic (Claude), Google (Gemini), Cohere, local models via Ollama, and many others. This enables users to choose the most suitable LLM for each agent and task based on capability, cost, or privacy requirements.

*   **Workflows ():** Workflows define the structure and sequence of the review process.
    *   They are defined by a schema that specifies multiple rounds of review.
    *   Each round can have one or more agents operating in parallel or sequentially.
    *   Workflows manage the flow of data (e.g., articles), direct agents to perform reviews, and can incorporate logic to filter articles between rounds (e.g., only "Included" articles proceed, or articles where previous agents disagreed go to an expert review).
    *   The system uses asynchronous operations for efficient processing of large batches of articles.

These components interact to create a versatile system for automating literature reviews. Data (e.g., a list of articles from a RIS file) is loaded and passed to a . The workflow then orchestrates the review process according to its defined schema, with  performing their tasks by leveraging  to communicate with LLMs. The results, including decisions, scores, extracted data, and reasoning, are collected and returned by the workflow, typically as a structured dataset (e.g., a pandas DataFrame).
