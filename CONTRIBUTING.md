# Contributing to Discord Vector DB

First off, thank you for considering contributing to Discord Vector DB! It's people like you that make this project better for everyone.

## Table of Contents

- [Contributing to Discord Vector DB](#contributing-to-discord-vector-db)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [Development Setup](#development-setup)
  - [Development Environment](#development-environment)
  - [Type Checking](#type-checking)
  - [Coding Standards](#coding-standards)
  - [Pull Request Process](#pull-request-process)
  - [Issue Reporting Guidelines](#issue-reporting-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Development Setup

1. Fork the repository
2. Clone your fork locally:

   ```bash
   git clone https://github.com/yourusername/discord_vector_db.git
   cd discord_vector_db
   ```

3. Set up a virtual environment:

   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

## Development Environment

We recommend using Visual Studio Code with the following extensions:

- Python
- Pylance or Pyright (for type checking)
- Ruff (for linting)

The repository includes configuration files for:

- `.vscode/settings.json` - Editor settings
- `mypy.ini` - MyPy configuration
- `pyproject.toml` - Project configuration including Ruff rules

## Type Checking

This project uses both mypy and Pyright/Pylance for type checking. All code should have proper type annotations.

Type stubs for external libraries are provided in the `typings/` directory. These stubs ensure proper type checking with libraries that may not have their own type definitions.

Important rules:

- All function parameters and return values should be properly typed
- Use `Optional[Type]` for values that could be `None`
- When working with external libraries without type stubs, add appropriate `# type: ignore` comments
- Use the helper functions in `discord_retriever/cli.py` when working with typer to ensure correct typing

## Coding Standards

This project follows PEP 8 style guidelines along with additional rules:

1. **Import Order**:
   - Standard library imports first
   - Related third-party imports
   - Local application/library specific imports

2. **String Formatting**:
   - Use f-strings for string formatting (`f"Hello {name}"`)

3. **Type Annotations**:
   - Follow [PEP 484](https://www.python.org/dev/peps/pep-0484/) for type hints
   - Use type annotations for all function parameters and return values

4. **Documentation**:
   - All modules, classes, and functions should have docstrings
   - Follow [Google's Python Style Guide](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstring format

5. **Error Handling**:
   - Use specific exception types
   - Provide meaningful error messages

6. **Linting**:
   - Code must pass all Ruff checks
   - Run `ruff check .` before submitting a pull request

## Pull Request Process

1. Ensure your code follows the coding standards and passes all type checks
2. Update the documentation if necessary
3. Add tests for any new functionality
4. Submit the pull request with a clear description of the changes

## Issue Reporting Guidelines

When reporting issues, please include:

- Your operating system name and version
- Python version
- Detailed steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any error messages (including stack traces)

For feature requests, clearly describe the proposed functionality and its use cases.

Thank you for contributing to Discord Vector DB!
