# Comprehensive Project Development Plan: LatteReview 🤖☕

**Slogan: A week's literature review in the time it takes to drink a latte.**

## I. Project Vision

In an era of information overload, academic researchers, students, and knowledge workers face a deluge of literature, reports, and data. Traditional literature review processes are time-consuming, tedious, and prone to error. LatteReview's vision is to revolutionize the way knowledge is sifted and synthesized, delegating repetitive, laborious tasks to AI, allowing human intellect to focus on high-value innovation, critical thinking, and insight generation.

We are not just creating a tool, but building a trusted team of AI research assistants. This team can work tirelessly 24/7, efficiently and transparently completing literature screening, scoring, summarization, and analysis tasks according to your defined professional backgrounds and criteria.

## II. Core Concepts Explained

LatteReview's power lies in the modularity and synergy of its three core components:

### 1. Intelligent Agents: Your Digital Expert Review Team

Agents are the soul of LatteReview. They are not mere API wrappers but AI entities endowed with roles and tasks.

*   **Persona Definition (Backstory):** You can assign unique "personas" to each agent, for example:
    *   "A clinical immunologist with 10 years of experience, particularly interested in Randomized Controlled Trials (RCTs)."
    *   "A postdoctoral researcher specializing in eXplainable AI (XAI), critically evaluating model assessment methodologies."
    *   "A junior research assistant responsible for rapidly screening out irrelevant literature."
*   **Professional Capabilities:**
    *   **:** Handles rapid initial screening, determining if titles and abstracts meet inclusion criteria.
    *   **:** Performs quantitative scoring based on multi-dimensional criteria you define (e.g., innovativeness, methodological rigor, relevance).
    *   **:** Conducts in-depth reading and information extraction, summarizing key findings, methods, sample sizes, etc., from qualified literature into structured data.
    *   **:** Offers ultimate flexibility. Through simple prompt engineering or by inheriting base classes, you can create any agent you need, such as a "Bias Detection Agent" or a "Technical Feasibility Assessment Agent."

### 2. Model Providers: Bridging to the World's Leading AI Brains

LatteReview is designed to be "Model-Agnostic," ensuring you can always use the most suitable and cost-effective model for the task.

*   ** (Recommended):** Our Swiss Army knife. Through a single interface, seamlessly switch between:
    *   Top-tier commercial models: OpenAI (GPT-4o, GPT-3.5), Anthropic (Claude 3 Opus/Sonnet/Haiku), Google (Gemini 1.5 Pro, and the default  for the GUI).
    *   High-performance open-source models: Groq (Llama3, Mixtral).
    *   Localized models: Run Llama3, Phi-3, etc., on your own machine via Ollama, ensuring data privacy and zero API costs.
*   **Flexible Configuration:** Assign different models to different agents or even different review rounds. For example, use fast, inexpensive models (Groq, local models) for initial screening, and the most powerful ones (GPT-4o, Claude 3 Opus) for in-depth analysis and decision-making.

### 3. Workflows (): Designing Your Automated Review Pipeline

Workflows are the conductors of this orchestra, stringing together agents, data, and review rules into an automated, repeatable scientific process.

*   **Schema-based:** Define the entire review process using a clear YAML or JSON file, like writing a script. This blueprint details:
    *   **Review Rounds:** Defines the stages of the review.
    *   **Agent Assignment:** Specifies which agents participate in each round.
    *   **Data Flow (Filters):** Determines which literature proceeds to the next round (e.g., "Only articles rated 'Include' by at least two junior agents proceed to senior agent review").
*   **Parallel & Sequential Processing:** Configure multiple agents to review the same batch of articles in parallel (simulating peer review) or have the review process occur serially (initial screen -> full review -> data extraction).
*   **Asynchronous Execution Engine:** The underlying asynchronous processing maximizes resource utilization and API concurrency, significantly reducing wait times, even with thousands of articles.

## III. Typical Workflow Example: Systematic Literature Review

Imagine a medical researcher needing to conduct a systematic review on "AI applications in early lung cancer diagnosis."

**Scenario:** 2000 relevant articles exported from PubMed as a RIS file.

**LatteReview Workflow Design:**

*   **Round 0: Data Import**
    *   Action:  loads .
*   **Round 1: Large-Scale Rapid Initial Screening (Triage)**
    *   Agents: 3  agents (persona: "Junior Radiology Intern"), using high-speed models (e.g., Groq, local Llama3; GUI defaults to ).
    *   Task: Based only on title and abstract, determine if articles are directly relevant to "AI" and "lung cancer diagnosis." Output: "Include," "Exclude," or "Unsure."
    *   Filter Rule: Articles proceed if at least 2 agents vote "Include," or if there's disagreement (e.g., 1 include, 1 exclude).
    *   Expected Outcome: Reduction from 2000 to ~400 articles.
*   **Round 2: Senior Expert Review & Conflict Resolution**
    *   Agent: 1  agent (persona: "Senior Oncologist"), using a high-quality model (e.g., GPT-4o; GUI defaults to ).
    *   Task: Review the ~400 articles from Round 1.
        *   For articles with disagreement, the agent receives votes and reasoning from Round 1 agents as additional context.
        *   Scores articles on dimensions like "Study Design," "Sample Size," "Innovativeness" (1-5 points), providing a final "Include/Exclude" decision and detailed reasoning.
    *   Filter Rule: Only articles with a total score > 3.5 and a final decision of "Include" proceed.
    *   Expected Outcome: Reduction from 400 to ~80 core articles.
*   **Round 3: Structured Data Extraction**
    *   Agent: 1  agent, using a model capable of long-context processing (e.g., Claude 3 Sonnet; GUI defaults to ).
    *   Task: For the final 80 articles, extract structured information:
        *   AI Model Type (e.g., CNN, Transformer)
        *   Dataset Source & Size
        *   Reported Accuracy/Sensitivity
        *   Key Conclusions
    *   Context Enhancement (RAG): Optionally provide a document with core research questions as context to make data extraction more targeted.

**Final Output:**

A structured JSON or CSV file containing the complete review history for the 80 articles, including per-round agent decisions, scores, reasoning, and the final extracted structured data. Researchers can directly use this for statistical analysis and manuscript writing.

## IV. Technical Architecture & Advantages

*   **Async Core:** Built on Python's  for true non-blocking I/O, ensuring efficient concurrency for remote LLM API calls and local file operations.
*   **Standardized Data Models:** All inputs, outputs, and intermediate results use Pydantic for strict type definition and validation, ensuring data consistency and reliability throughout the workflow. Outputs include detailed metadata for full traceability.
*   **Resource Management:**
    *   **Cost Tracking:** Deep integration with LiteLLM allows precise tracking of LLM API call costs, providing users with clear expense visibility.
    *   **Memory Management:** Optimized for large-scale data processing, avoiding loading all data into memory at once.
*   **Extreme Extensibility:** Each core component (Agent, Provider, Workflow) is designed around abstract base classes. Advanced users can easily inherit these classes to implement custom logic without modifying the core codebase.

## V. Target Users & Application Scenarios

*   **Academic Researchers/PhD Students:** Systematic literature reviews, meta-analyses, tracking latest field advancements.
*   **Corporate R&D Teams:** Patent analysis, competitive technology intelligence, new tech trend monitoring.
*   **Market Analysts/Consultants:** Extracting key insights and data from numerous industry reports, news, and financial statements.
*   **Legal Professionals:** Case law research, contract review.
*   **Content Curators:** Automating screening, tagging, and summarization of vast content for knowledge bases or newsletters.

## VI. Future Vision & Roadmap

*   **Q3 2024: Graphical User Interface (GUI)**
    *   Develop a web-based, drag-and-drop interface allowing non-developers to easily design and run review workflows. (This is what we've been building!)
*   **Q4 2024: Enhanced Agents & Full-Text Document Support**
    *   **Proactive Agents:** Agents that can auto-generate initial inclusion/exclusion criteria based on a high-level research question.
    *   **Native PDF/DOCX Parsing:** Directly process full-text documents, not just titles/abstracts.
*   **2025 H1: Interactive Dashboard & Collaboration Platform**
    *   Develop an interactive dashboard to visualize review progress, agent decision distributions, and allow users to manually override/correct AI decisions.
    *   Introduce multi-user collaboration features for team-based review project management.
*   **Long-Term Vision: Open Source Ecosystem**
    *   Foster an open community encouraging users to contribute and share domain-specific agents and workflow templates (e.g., "Clinical Trial Review Template," "Social Science Qualitative Research Template").

## VII. Conclusion

LatteReview is more than a code package; it's a powerful cognitive augmentation framework. It combines the capabilities of large language models with rigorous academic review processes, aiming to free researchers from tedious labor, allowing them more time—perhaps precisely the time for a latte—for genuinely creative work. This project is born for efficiency, transparency, and deep insight.
