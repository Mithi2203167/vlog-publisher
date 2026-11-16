# Vlog & Article Publisher

A small Flask + SQLite backend for publishing vlogs and articles: authors write drafts, an editor reviews
them, readers comment, and subscribers get an email when something new is published.

Built for RUET CSE 3206 (Software Engineering Sessional).

## Modules (one file each)

| Module | File | What it does |
|---|---|---|
| Authors | `app/authors.py` | Register authors |
| Posts | `app/posts.py` | Create article or vlog drafts |
| Review | `app/review.py` | Submit, approve, reject; auto-publish for trusted authors |
| Comments | `app/comments.py` | Readers comment on published posts |
| Subscriptions | `app/subscriptions.py` | Subscribe, unsubscribe; subscribers get emails |

Shared files: `app/db.py` (SQLite schema), `app/observers.py`, `app/notifier.py`, `app/api.py` (Flask routes),
`app/static/index.html` (home page: write, review, read and comment) and `app/static/register.html` (author registration page). Both call the API; open http://127.0.0.1:5000/ and http://127.0.0.1:5000/register after starting the app.

## Design patterns

| Pattern | Category | Where | Problem solved | Alternative rejected |
|---|---|---|---|---|
| Factory | Creational | `PostFactory` | An article needs text, a vlog needs a video link; one place builds and validates each kind | If/else spread through the service |
| Strategy | Behavioral | `ManualReview`, `TrustedAuthorPolicy` | The rule for "what happens when a post is submitted" can change without editing the review service | A flag or if/else inside `submit` |
| Observer | Behavioral | `EventBus`, `EmailNotificationObserver` | Publishing a post must notify subscribers without the review module knowing about email | Calling the notifier directly inside `approve` |

## Run

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
flask --app wsgi run             # API on http://127.0.0.1:5000
```

Data is stored in `publisher.db` (SQLite). Set `DATABASE_PATH` to change the location.

## Test

```bash
pytest
pytest --cov=app --cov-report=term-missing
```

`tests/test_ui_selenium.py` drives a real Chrome browser (Selenium) through the web page: register, write,
submit, approve, comment. It needs Chrome installed; if no browser can start, those tests are skipped.

Tests were written first (TDD). Mocks (`unittest.mock`) replace the repository, the event bus and the SMTP
network call where a test must be isolated; other tests use an in-memory SQLite database.

## API

| Method | Path | Purpose |
|---|---|---|
| POST, GET | `/authors` | Register, list |
| POST, GET | `/posts` | Create draft (`kind`: article or vlog), list (`?status=published`) |
| GET | `/posts/<id>` | One post |
| POST | `/posts/<id>/submit` | Draft -> pending (or published for trusted authors) |
| POST | `/posts/<id>/approve` | Pending -> published, subscribers notified |
| POST | `/posts/<id>/reject` | `{"reason": "..."}` |
| POST, GET | `/posts/<id>/comments` | `{"name": "...", "text": "..."}` |
| POST, DELETE, GET | `/subscriptions` | `{"email": "..."}` |

## Extending

- New post kind (for example podcast): write a builder in `app/posts.py` and add it to `BUILDERS`.
- New review rule: write a class with `decide(published_count)` and pass it as `REVIEW_POLICY` to `create_app`.
- New notification channel: write a class with `send(to, subject, body)` and pass it as `NOTIFIER`.

## Process model

Incremental: each module is built and tested as its own increment on its own feature branch.

## AI use statement

AI (Claude) was used to generate the initial code and tests. See the report for which parts were
reviewed, changed and verified by the author.
