# LLM Integration Guide for Nation IntentKit Project

This guide provides comprehensive information for Large Language Models working with this project.

## Project Overview

This project uses IntentKit (https://github.com/crestalnetwork/intentkit) as the core and extends it with some nation-specific business logic.

It includes an API server, a task scheduler, and several scripts.

## Technology Stack

Package manager: uv, please use native uv command, not use the uv pip command.

Lint: ruff, run `uv run ruff format & uv run ruff check --fix` after your every edit.

API framework: fastapi

DB ORM: SQLAlchemy 2.0, please check the 2.0 api for use, do not use the legacy way.

Model: Pydantic V2, Also be careful not to use the obsolete V1 interface.

## Rules

1. Always use the latest version of the new package.
2. Always use English for code comments.
3. Always use English to search.
4. If you want to generate git commit message, always start with feat/fix/chore/docs/test/refactor/improve. Format: `<type>: <subject>`, subject should start with lowercase. Only one-line title needed, do not generate message body.
