# AGENTS.md

Operational guidelines for AI agents and developers contributing to Anitya.

## Fedora AI-Assisted Contribution Policy

This repository is part of the Fedora Project and subject to the [Fedora AI-Assisted Contributions Policy](https://docs.fedoraproject.org/en-US/council/policy/ai-contribution-policy/). Key requirements:

- **Accountability**: The human contributor is always the author and is fully accountable for the entirety of AI-assisted contributions. All submissions must meet project standards for quality, license compliance, and utility.
- **Transparency**: Use of AI tools MUST be disclosed when the significant part of the contribution is taken from a tool without changes. For git contributions, use an `Assisted-by:` commit message trailer (e.g., `Assisted-by: ChatGPTv5` or `Assisted-by: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`).
- **No AI-only judgments**: AI MUST NOT be used as the sole or final arbiter for substantive or subjective judgments on contributions, nor for evaluating a person's standing in the community. Automated objective validation (CI/CD, testing, linting) is permitted.

## Git Conventions

### Commit Messages & Sign-off
- **Subject line:** Capitalized imperative sentence or Conventional Commit under 80 characters (up to 100 is acceptable). Example: `Handle connection timeouts in PyPI backend`.
- **Body:** Leave a blank line after the subject. Explain the problem context, why the change is necessary, and technical implementation details. Do not add conversational fluff or AI narration.
- **DCO Sign-off (Mandatory):** Every commit MUST be signed off using `git commit -s` to append:
  ```gitcommit
  Signed-off-by: Full Name <email@example.com>
  ```

## Development & Tooling: When to Use Poetry vs Make

### When to Use `make` (Containerized Dev Environment)
Use `make` commands when running inside or managing Podman/Docker containers. The project mounts the repo at `/app`:
- `make up`: Start dev containers (web at `localhost:5000`, PostgreSQL, RabbitMQ).
- `make halt`: Stop dev containers.
- `make restart`: Restart containers (required after updating `pyproject.toml` or `package.json`).
- `make build`: Rebuild images (required after modifying `Containerfile.dev`).
- `make tests PARAM="anitya/tests/test_api_v2.py"`: Run pytest in container.
- `make lint`: Run flake8 in container.
- `make format`: Run black check in container.
- `make mypy`: Run mypy in container.
- `make diff-cover`: Run coverage check on changed lines against `origin/master`.

### When to Use `poetry` (Host-Native Development)
Use `poetry` when working directly on your host in a Python 3.11+ virtual environment:
- `poetry install`: Install Python dependencies.
- `poetry run pytest anitya/tests/test_<name>.py -k <test_method>`: Run fast targeted tests directly.
- `poetry run flake8 anitya/`: Lint code.
- `poetry run black anitya/`: Format code automatically.
- `poetry run mypy --config-file mypy.cfg anitya`: Run type checker.

### Documentation
- Documentation uses Sphinx with Google-style docstrings.
- **When to document:** Add Google-style docstrings to all new public classes and functions (picked up by `autodoc`); update `docs/api.rst` when modifying or adding REST API endpoints.
- Generate schema image and build docs:
  ```bash
  (cd docs && ./generate_db_schema) && poetry run sphinx-build -W -b html docs docs/_build/html
  ```
  Or run via tox: `poetry run tox -e docs`.

### News Fragments (Towncrier)
Every user-facing change, bugfix, API adjustment, or developer change requires a news fragment in `news/`:
- Format: `news/<number>.<type>` (e.g., `1234.bug`, `2345.feature`, `3456.dev`). Use the issue number or the PR number without any prefix.
- Valid types: `.feature`, `.bug`, `.api`, `.dev`, `.other`, `.author`.
- Preview draft notes: `poetry run towncrier --draft`.

## System Architecture

Anitya monitors upstream software releases across distributions and broadcasts new release events over `fedora-messaging` (RabbitMQ).

### Core Components & Directory Map
- `anitya/check_service.py`: Background worker that periodically polls upstream sources on a schedule and publishes release notifications.
- `anitya/lib/backends/`: Upstream provider plugins extending `BaseBackend` (GitHub, PyPI, Crates, GitLab, etc.). Responsible for upstream API calls, URL normalization, and tag/release extraction.
- `anitya/lib/ecosystems/`: Package ecosystem definitions (Python, Rust, Go, etc.) providing package boundaries and default version schemes.
- `anitya/lib/versions/`: Version parsing and comparison algorithms (RPM, SemVer, PEP 440, CalVer).
- `anitya/db/models.py`: Database persistence models (`Project`, `Package`, `Version`, `Distro`, `Ecosystem`).
- `anitya/api_v2.py` & `anitya/ui.py`: REST API v2 and Flask web frontend.
- `anitya/templates/`: Jinja2 HTML templates extending `master.html`.
- `anitya/static/css/`: Frontend stylesheets (`main.css` for application-level overrides and tables, `navbar.css`, `footer.css`, `avatars.css`, `text.css`).

### Design Principles & Boundaries
- **Plugin Extensibility:** Upstream-specific behavior (URL parsing, custom API formats, version extraction) belongs inside the respective backend subclass, never in centralized procedural switches or utility functions.
- **Lean Route Handlers:** Keep `api_v2.py` and `ui.py` focused on HTTP routing, request parsing, and response formatting; delegate business logic, validation, and queries to models or backend plugins.
- **Frontend & Theming:** Custom site styles belong in `anitya/static/css/main.css` or scoped stylesheets, never inline. Anitya supports both light and dark modes via Bootstrap 5.3's `data-bs-theme`; all custom colors must meet WCAG AA contrast standards in both themes.
- **Asynchronous Decoupling:** Upstream checks and network scraping run in the background via `check_service`, keeping web and API responses fast and non-blocking.

## Legacy Code Guardrail

- Anitya contains legacy code written against older Python and SQLAlchemy 1.x versions.
- **Do not cargo-cult outdated idioms** simply because they exist in adjacent files (e.g., legacy `session.query(...)` chaining, untyped helpers, manual transaction manipulation, or monolithic procedural scripts).
- Follow modern standards: SQLAlchemy 2.0+ patterns, explicit type hints, and modular class methods.

## DRY & Commenting Standards

- Do not repeat logic across backends, routes, or test suites. Extract common logic into `BaseBackend` or shared modules.
- Comments must explain non-obvious reasoning (the "why"): upstream API rate limits, special regex behaviors, third-party quirk workarounds, or business constraints.
- Never write comments that narrate syntax (`# loop through projects`, `# return True`). Let readable code explain the "how".

## Testing & Quality Assurance

- **100% Diff Coverage:** CI strictly enforces 100% diff coverage (`diff-cover coverage.xml --compare-branch=origin/master --fail-under=100`). Every new line, branch, and exception handler must have a test.
- **Database & Migrations:** Use `DatabaseTestCase` (`anitya.tests.base`) for tests requiring database persistence. If altering models in `anitya/db/models.py`, generate a new Alembic migration in `anitya/db/migrations/versions/` and refresh the schema diagram (`cd docs && ./generate_db_schema`).
- **Test Isolation:** Tests run against an isolated SQLite test database with transaction rollbacks. Never call `db.manager.sync()`, drop tables, or reconfigure engines inside individual test methods.
- **Network & VCR:** External HTTP requests made by backends during tests are recorded and replayed via VCR cassettes in `anitya/tests/request-data/`.
- **Targeted Testing:** Always run targeted tests for modified modules during development rather than the full multi-minute test suite.
