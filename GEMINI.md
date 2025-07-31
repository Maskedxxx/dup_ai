# Gemini Code Assistant Project Guidelines

This document provides instructions for the Gemini code assistant to ensure its interactions and contributions are aligned with the project's standards and practices.

## General Principles

- **Be Proactive:** Your primary goal is to assist in software engineering tasks. Anticipate the user's needs and offer suggestions to improve the codebase.
- **Clarity and Conciseness:** Communicate clearly and concisely. Avoid jargon and unnecessary verbiage.
- **Respect Existing Code:** Adhere to the existing coding style, conventions, and architecture.
- **Verify Before Committing:** Always run tests and linting checks before committing any changes.

## Workflow

1.  **Understand the Goal:** Before making any changes, ensure you understand the user's request. Ask for clarification if needed.
2.  **Explore the Codebase:** Use the available tools to explore the codebase and understand the context of the changes.
3.  **Implement the Changes:** Make the necessary changes to the code, following the project's conventions.
4.  **Test and Verify:** Run the test suite and any relevant linting checks to ensure the changes are correct and don't introduce any regressions.
5.  **Commit the Changes:** Once the changes are verified, commit them with a clear and descriptive commit message.

## Commit Messages

- **Format:** Use the following format for commit messages:

    ```
    <type>: <subject>

    <body>
    ```

- **Type:** The type of the commit, such as `feat` (new feature), `fix` (bug fix), `docs` (documentation), `style` (code style), `refactor` (refactoring), `test` (tests), or `chore` (maintenance).
- **Subject:** A concise and descriptive summary of the changes.
- **Body:** A more detailed explanation of the changes, including the motivation and context.
