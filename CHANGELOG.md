# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- [Placeholder for changes that will be added in the next release]

## [0.1.2] - 2024-12-16

### Added

- NA

### Changed

- Renamed `score_review_test.md` to `scoring_review_test.md`
- Updated the `README.md` file.

### Deprecated

- NA

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
