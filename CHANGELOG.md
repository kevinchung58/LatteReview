# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- [Placeholder for changes that will be added in the next release]

## [0.1.1] - 2024-12-16

### Added

- NA

### Changed

- Changed `data.xlsx` to `test_article_data.csv` which now has cleaner Column names and only contains 20 rows.
- Passing the inputs_description to agents are now optional. The default value is "article title/abstract."
- Expanded the "Quick Start" section in the README.md file.

### Deprecated

- NA

### Removed

- NA

### Fixed

- Bug in `OpenAIProvider.py` making it unable to read the environmental variable for OPENAI_API_KEY.

### Security

- NA
