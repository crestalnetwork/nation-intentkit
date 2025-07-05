# LLM Integration Guide for Nation IntentKit Project

This guide provides comprehensive information for Large Language Models working with this project.

## Project Overview

This project uses IntentKit (https://github.com/crestalnetwork/intentkit) as the core and extends it with some nation-specific business logic.

It includes an API server, a task scheduler, and several scripts.

## Technology Stack

Package manager: uv, please use native `uv` command, do not use the `uv pip` command.

Lint: ruff, run `uv run ruff format & uv run ruff check --fix` after your final edit.

API framework: fastapi, Doc in https://fastapi.tiangolo.com/

DB ORM: SQLAlchemy 2.0, please check the 2.0 api for use, do not use the legacy way.
Doc in https://docs.sqlalchemy.org/en/20/

Model: Pydantic V2, Also be careful not to use the obsolete V1 interface.
Doc in https://docs.pydantic.dev/latest/

## Rules

1. Always use the latest version of the new package.
2. Always use English for code comments.
3. Always use English to search.

## Guide

### Git Commit
When you generate git commit message, always start with one of feat/fix/chore/docs/test/refactor/improve. Title Format: `<type>: <subject>`, subject should start with lowercase. Only one-line needed, do not generate commit message body.

### Github Release
1. Please use gh command to do it.
2. Make a `git pull` first.
3. Find the last release/pre-release, diff the origin/main with it, summarize the release note to changelog.md for later use. Add a diff link to release note too, the from and to should be the version number.
4. And also insert the release note to the beginning of RELEASE_NOTES.md (This file contains all history release notes, don't use it in gh command)
5. Construct `gh release create` command, calculate the next version number, use RELEASE_NOTES.md as notes file in gh command.
6. Use gh to do release only, don't create branch, tag, or pull request.
