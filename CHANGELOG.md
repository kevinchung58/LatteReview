# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Adding support for `AbstractionReviewer` class.

## [0.3.0] - xxxx-xx-xx

### Added

-

### Changed

-

### Deprecated

- NA

### Removed

- NA

### Fixed

- Addressed a bug in the `scoring_review_prompt.txt` that caused the reasoning and examples not to be read by the agents.

### Security

- NA

## [0.2.1] - 2024-12-23

### Added

- The agents can now accept an `additional_context` argument of type string or Callable. If callable, expects an async function that accepts a single input review item (e.g., to retrieve the relevant context for that unique item in RAG use cases)
- Added the `scoring_review_rag` use case to the example folders.

### Changed

- Moved `examples/scoring_review_test.ipynb` to `examples/scoring_review_simple/scoring_review_simple.ipynb`.
- Updated all provider classes so that they can now directly accept classes inheriting from pydantic.BaseModel as `response_format_class`.
- Updated the naming convention of prompts in the agent methods for further clarity.
- Added `_` to all internal methods of `BaseAgent` class.
- All example data spreadsheets are now named as `data.csv`.
- Updated all the docs to reflect all the above changes.
- Updated the `README.md` file to reflect all the above changes.

### Deprecated

- NA

### Removed

- NA

### Fixed

- Addressed a bug in the `scoring_review_prompt.txt` that caused the reasoning and examples not to be read by the agents.

### Security

- NA

## [0.2.0] - 2024-12-21

### Added

- All agents now return a `certainty` score which is an integer between 0 to 100.
- It is now possible to pass `0` to `scoring_set` of the ScoringReviewer agents as 0 is not used for denoting uncertainty anymore.

### Changed

- Updated the `review_workflow` to dynamically add any output keys from reviewers to the workflow dataframe.

- Updated the `scoring_review_prompt` for clarity and to reflect the above changes.
- Renamed the `score_set` parameter of the `scooring_reviewer `to `scoring_set`.
- Renamed `score_review_test.md` to `scoring_review_test.md`.
- Updated the `scoring_review_test.ipynb` to reflect all the above changes.
- Updated the `README.md` file to reflect all the above changes.

### Deprecated

- `ScoringReviewer` agent now only accepts `brief` and `cot` for reasoning. the `long` reasoning is now deprecated.

### Removed

- NA

### Fixed

- NA

### Security

- NA

## [0.1.1] - 2024-12-16

### Added

- Added the package documentation to the `docs` folder.
- Added a `data` folder within the `examples` folder.

### Changed

- Updated the `README.md` file.
- Moved `README.md` to the `docs` folder.
- Changed `notebooks` folder to `examples`.
- Changed `data.xlsx` to `test_article_data.csv` which now has cleaner Column names and only contains 20 rows.
- Moved the `review_workflow.py` to the `workflows` folder.
- Passing the `inputs_description` to agents are now optional. The default value is "article title/abstract."

### Deprecated

- NA

### Removed

- NA

### Fixed

- Bug in `OpenAIProvider.py` making it unable to read the environmental variable for OPENAI_API_KEY.

### Security

- NA
