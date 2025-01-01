# LatteReview 🤖☕

[![PyPI version](https://badge.fury.io/py/lattereview.svg)](https://badge.fury.io/py/lattereview)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Maintained: yes](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/prouzrokh/lattereview)

<p><img src="images/robot.png" width="400"></p>

A framework for multi-agent review workflows using large language models.

## Overview

LatteReview is a Python framework that enables you to create and manage multi-agent review workflows using various large language models. It provides a flexible and extensible architecture for implementing different types of review processes, from simple single-agent reviews to complex multi-stage workflows with multiple agents.

## Features

- Multi-agent review system with customizable roles and expertise levels for each reviewer
- Support for multiple review rounds with hierarchical decision-making workflows
- Review diverse content types including article titles, abstracts, custom texts, and images using LLM-powered reviewer agents
- Define reviewer agents with specialized backgrounds and distinct evaluation capabilities
- Create flexible review workflows where multiple agents operate in parallel or sequential arrangements
- Enable reviewer agents to analyze peer feedback, cast votes, and propose corrections to other reviewers' assessments
- Enhance reviews with item-specific context integration, supporting use cases like Retrieval Augmented Generation (RAG)
- Broad compatibility with LLM providers through LiteLLM, including OpenAI and Ollama
- Model-agnostic integration supporting OpenAI, Gemini, Claude, Groq, and local models via Ollama
- High-performance asynchronous processing for efficient batch reviews
- Standardized output format featuring detailed scoring metrics and reasoning transparency
- Robust cost tracking and memory management systems
- Extensible architecture supporting custom review workflow implementation

## Quick Links

- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Tutorial notebooks](https://github.com/prouzrokh/lattereview/tutorials)
- [API Reference](api/workflows.md)
- [GitHub Repository](https://github.com/PouriaRouzrokh/LatteReview)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/PouriaRouzrokh/LatteReview/blob/main/LICENSE) file for details.

## Author

**Pouria Rouzrokh, MD, MPH, MHPE**  
Medical Practitioner and Machine Learning Engineer  
Incoming Radiology Resident @Yale University  
Former Data Scientist @Mayo Clinic AI Lab

Find my work:
[![Twitter Follow](https://img.shields.io/twitter/follow/prouzrokh?style=social)](https://twitter.com/prouzrokh)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/pouria-rouzrokh)
[![Google Scholar](https://img.shields.io/badge/Google%20Scholar-Profile-green)](https://scholar.google.com/citations?user=Ksv9I0sAAAAJ&hl=en)
[![Email](https://img.shields.io/badge/Email-Contact-red)](mailto:po.rouzrokh@gmail.com)

## Support LatteReview

If you find LatteReview helpful in your research or work, consider supporting its continued development. Since we're already sharing a virtual coffee break while reviewing papers, maybe you'd like to treat me to a real one? ☕ 😊

### Ways to Support:

- [Treat me to a coffee](http://ko-fi.com/pouriarouzrokh) on Ko-fi ☕
- [Star the repository](https://github.com/PouriaRouzrokh/LatteReview) to help others discover the project
- Submit bug reports, feature requests, or contribute code
- Share your experience using LatteReview in your research
