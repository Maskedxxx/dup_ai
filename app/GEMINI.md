# Gemini Code Assistant App Guidelines

This document provides specific instructions for the Gemini code assistant when working within the `app/` directory. It outlines the application's architecture and the purpose of each component.

## Application Architecture

The application follows a modular architecture, with each component having a specific responsibility. When making changes, it's important to respect this separation of concerns and adhere to the existing design patterns.

- **`adapters/`:** This directory contains adapters for interacting with external services, such as the `LlmClient` for language model interactions and `ExcelLoader` for data loading.
- **`api/`:** This directory defines the public API endpoints, including the schemas for requests and responses. When adding new endpoints, follow the existing structure and conventions.
- **`domain/`:** This directory contains the core domain models and business logic of the application. These models should be independent of any specific framework or technology.
- **`pipelines/`:** This directory defines the data processing pipelines, which are responsible for orchestrating the flow of data through the application.
- **`services/`:** This directory contains the business logic for the application, such as classifiers, normalizers, and answer generators. When adding new services, ensure they are properly tested and integrated with the existing components.
- **`tools/`:** This directory contains the tools and utilities used by the application, such as the `ToolExecutor` and `KeywordSearchTool`.
- **`utils/`:** This directory contains utility functions and helper classes used throughout the application.

## Development Guidelines

- **Testing:** All new features and bug fixes should be accompanied by unit tests. The tests should be placed in the corresponding `tests/` directory and follow the existing testing conventions.
- **Dependencies:** When adding new dependencies, ensure they are added to the `requirements.txt` file and that they are compatible with the existing dependencies.
- **Documentation:** All new features and changes to the public API should be properly documented. This includes updating the API documentation and any relevant user guides.
