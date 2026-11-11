# CyberJobHunter

**CyberJobHunter** is a personal, non-commercial Python project created by a Computer Engineering student to practice Python programming, API integration, data processing, databases, and process automation.

The project helps organize the search for cybersecurity internships by retrieving job listings, estimating their relevance, and storing them for later review. It was built as a learning exercise rather than a commercial recruitment product.

## Features

- Search for internship and entry-level opportunities using the Tavily Search API.
- Normalize search results and avoid saving duplicate URLs.
- Rank listings using configurable keywords, locations, and relevance rules.
- Assign a priority level to each result.
- Store offers in a local SQLite database.
- Review offers and update their status (`nueva`, `revisada`, `descartada`, `solicitada`).
- View saved offers, submitted applications, and basic statistics through a command-line menu.

> **Development status:** The current version uses SQLite and runs locally. Scheduled execution with GitHub Actions and a cloud-hosted PostgreSQL database are planned improvements, not requirements for running the current version.

## Technologies

- Python 3
- [Tavily Search API](https://tavily.com/)
- `tavily-python` for search requests
- `python-dotenv` for local environment variables
- `requests` for HTTP requests where used
- `sqlite3` (Python standard library) for local persistence
- `re` (Python standard library) for keyword matching

## Getting started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/CyberJobHunter.git
cd CyberJobHunter
```

Replace `YOUR_USERNAME` with the repository owner's GitHub username.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install tavily-python python-dotenv requests
```

If the repository includes a `requirements.txt`, you can instead use:

```bash
pip install -r requirements.txt
```

### 4. Configure your Tavily API key

Create a file named `.env` in the project root:

```dotenv
TAVILY_API_KEY=your_tavily_api_key_here
```

Create your own API key from the [Tavily dashboard](https://app.tavily.com/). The key must be read by the Python program using `python-dotenv` (or another environment-variable mechanism).

**Never publish your real API key or commit your `.env` file.**

### 5. Configure `.gitignore`

Create a file named `.gitignore` in the project root and include:

```gitignore
.env
.venv/
__pycache__/
*.pyc
ofertas.db
```

`ofertas.db` is excluded here because it contains local search data; remove that rule only if you deliberately want to version a sample database without private information. If a secret was previously committed, adding it to `.gitignore` does not erase it from Git history: revoke or rotate the exposed key.

### 6. Run the application

From the project root, run the main Python file, for example:

```bash
python main.py
```

> Check the actual entry-point filename in your copy of the project and replace `main.py` if necessary. The application presents a command-line menu for searching and managing job offers.

## Customizing the job search

CyberJobHunter's scoring rules are intended to be adapted. To search for different types of roles or in other locations, review the configuration values in the Python source code:

| Configuration | What to change | Example |
| --- | --- | --- |
| Search queries (`busquedas`) | Keywords passed to Tavily | `"cloud security internship Madrid"` |
| Test queries (`busquedas_pruebas`) | Smaller set of searches for development | One or two searches to reduce API usage |
| Locations (`ubicaciones`) | Cities or regions and their score weights | Madrid, Valencia, remote |
| Specialization keywords | Relevant technical skills and job titles | SOC, pentesting, cloud, Python |
| Internship indicators | Words that identify internships or junior roles | intern, trainee, prácticas |
| Scoring thresholds | How results receive high/medium/low priority | Adjust according to your needs |

Some identifiers may differ between versions. Locate the corresponding dictionaries, lists, and scoring functions in your source code before editing them. Keep the search queries and scoring criteria aligned so that relevant opportunities are not filtered out or ranked too low.

For example, someone searching for **data analyst internships** could replace cybersecurity-related keywords with `SQL`, `Power BI`, `data analysis`, and `Python`, then update the preferred locations and test the results.

## Project workflow

1. The user starts a search from the CLI.
2. Tavily returns potential job listings.
3. The program normalizes the results and calculates relevance and priority.
4. New URLs are stored in SQLite; previously saved URLs are skipped.
5. The user reviews offers, updates their status, and consults summary statistics.

The scoring is heuristic and depends on the search results and configured keywords. It does not guarantee that an offer is current, suitable, or still accepting applications. Always verify the original job posting before applying.

## Planned improvements

- Run searches automatically on a schedule using GitHub Actions.
- Move persistent storage to a cloud-hosted PostgreSQL database.
- Improve logging, error handling, and automated tests.

These features are part of the roadmap and may change as the project evolves.

## Educational purpose and disclaimer

This project was developed independently for **learning and experimentation**. It is **not affiliated with Tavily, job boards, employers, or recruitment agencies**, and it has **no commercial purpose**.

Users are responsible for complying with the terms of the APIs and websites they use, respecting request quotas, and protecting their own credentials. Search results may be incomplete or inaccurate.

## Contributing

Suggestions, feedback, and educational improvements are welcome. If you adapt the project, document your changes and avoid committing API keys or personal data.

## License

No license has been selected yet. If you want others to be legally permitted to reuse, modify, and redistribute the code, add an appropriate `LICENSE` file (for example, MIT) after reviewing its terms. A public GitHub repository does not automatically grant permission to reuse its code.
