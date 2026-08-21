# CheapFlightFinder

CheapFlightFinder searches flexible travel dates with the SerpApi Google Travel Explore API, ranks the best flight options, and emails one grouped report on your preferred schedule. Everything a typical fork needs to customize lives in `config.json`.

## What it does

- Searches from one or many origin airports.
- Tracks multiple independent destinations in the same run.
- Supports weekend, one-week, and two-week flexible trips.
- Filters by price, cabin, and maximum stops.
- Combines every configured search into one email.
- Shows best-fare price trends from the saved history for each trip length.
- Runs automatically through GitHub Actions without a dedicated server.
- Saves `data/price_history.json` after successful reports.
- Controls report frequency through `schedule.every_hours` in `config.json`.

Each configured trip length uses one SerpApi search. The included configuration splits nine origin airports into four regional profiles. With two trip lengths per profile, it uses eight API searches per report and typically returns a broader set of deals than sending all nine origins in one request.

## Fork and set up your own tracker

### 1. Fork the repository

Use GitHub's **Fork** button to create a copy under your own account. GitHub maintains [instructions for creating and working with forks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo).

### 2. Customize `config.json`

Edit the file directly on GitHub or clone your fork and edit it locally. The included configuration contains one Cape Town search. Add another object to the `searches` list for every additional route set you want to monitor.

```json
{
  "schedule": {
    "every_hours": 12
  },
  "results_per_search": 5,
  "searches": [
    {
      "name": "Cape Town from East Coast airports",
      "origins": ["BOS", "JFK", "EWR"],
      "destination": "CPT",
      "currency": "USD",
      "travel_class": "economy",
      "max_stops": 2,
      "max_price": 1500,
      "trip_lengths": ["one_week", "two_weeks"]
    },
    {
      "name": "Long weekends in Miami",
      "origins": ["BOS", "JFK"],
      "destination": "MIA",
      "currency": "USD",
      "travel_class": "economy",
      "max_stops": 1,
      "max_price": 500,
      "trip_lengths": ["weekend"]
    }
  ]
}
```

The example above sends one email containing separate Cape Town and Miami sections. For a large origin list, divide airports into a few regional profiles. Each profile receives its own result pool and email section, which can surface more options without making a separate API request for every airport.

### 3. Create the credentials

You need:

1. A [SerpApi account and API key](https://serpapi.com/google-travel-explore-api).
2. A Gmail account with 2-Step Verification enabled.
3. A Google App Password for that Gmail account. Google explains the eligibility requirements and creation process in its [App Password guide](https://support.google.com/accounts/answer/185833).

Use the App Password—not your normal Google password—as `EMAIL_APP_PASSWORD`. Some work, school, security-key-only, or Advanced Protection accounts do not offer App Passwords.

### 4. Add GitHub Actions secrets

In your fork, open **Settings → Secrets and variables → Actions → New repository secret**. Create all four secrets with these exact names:

| Secret | Value |
| --- | --- |
| `SERPAPI_KEY` | Your private SerpApi API key |
| `EMAIL_ADDRESS` | The Gmail address that sends the report |
| `EMAIL_APP_PASSWORD` | The Google App Password for that Gmail account |
| `EMAIL_RECIPIENT` | The address that receives reports |

GitHub's [Actions secrets guide](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets) has screenshots and additional options. Never put credentials directly in `config.json`, the workflow file, or a commit.
The workflow also accepts the legacy misspelling `SERPAI_KEY` for existing forks, although new forks should use `SERPAPI_KEY`.

### 5. Enable and test the workflow

GitHub disables workflows in new forks by default. Open the **Actions** tab, select **Configurable Flight Search**, and enable it. Then select **Run workflow** to send an immediate test report. A manual run ignores `every_hours` and resets the interval from the time it succeeds.

The workflow checks once per hour, but it installs dependencies, calls SerpApi, and sends email only when the configured interval is due. Scheduled workflows in public forks are disabled by default and can also be disabled after 60 days without repository activity; see GitHub's [workflow enablement documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows).

## Configuration reference

### Top-level settings

| Setting | Required | Meaning |
| --- | --- | --- |
| `schedule.every_hours` | No | Hours between successful reports. Defaults to `24`. Minimum is `1`. |
| `results_per_search` | No | Maximum flights shown for each named search. It does not force SerpApi to return that many. Defaults to `10`. |
| `searches` | Yes | Non-empty list of independent search profiles. |

Common schedule values:

| Value | Frequency |
| ---: | --- |
| `1` | Hourly |
| `6` | Four times per day |
| `12` | Twice per day |
| `24` | Daily |
| `168` | Weekly |

GitHub schedules can start a little late during busy periods, so treat these as approximate intervals rather than exact delivery times.
To choose the approximate starting time for a daily or weekly interval, trigger one manual workflow run at that time; later scheduled reports count forward from the last successful run.

### Search profile settings

| Setting | Required | Allowed values or example |
| --- | --- | --- |
| `name` | Yes | A unique label shown as the email section heading |
| `origins` | Yes | One or more airport codes, such as `["BOS", "JFK"]` |
| `destination` | Yes | Destination airport code, such as `"CPT"` |
| `currency` | No | Three-letter currency code; defaults to `"USD"` |
| `travel_class` | No | `economy`, `premium_economy`, `business`, or `first` |
| `max_stops` | No | `0`, `1`, or `2`; defaults to `2` |
| `max_price` | No | Maximum total ticket price; defaults to `1500` |
| `trip_lengths` | Yes | Any combination of `weekend`, `one_week`, and `two_weeks` |

To search another destination or a different group of origins, add another object to `searches`. To monitor the same route with different constraints—economy under $1,000 and business under $3,000, for example—create two profiles with unique names.

### Price trends in the email

Each search section shows the cheapest current fare for every trip length, its change from the previous successful run, and the range of cheapest fares observed across saved runs. Trends use `data/price_history.json`, so they persist in GitHub Actions and improve as the tracker collects more reports.

When you rename or split a profile, its first trend can fall back to comparable history with the same origin, destination, and currency. After the first successful run under the new name, later comparisons use that profile's own history. Deleting `data/price_history.json` resets all trends.

## Run locally

Python 3.11 or newer is recommended.

```bash
git clone https://github.com/YOUR_USERNAME/CheapFlightFinder.git
cd CheapFlightFinder
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`, customize `config.json`, and run:

```bash
python main.py
```

Local runs always execute immediately; `schedule.every_hours` only gates scheduled GitHub Actions checks. The included `.gitignore` excludes `.env` so credentials are not committed.

## How ranking works

Lower scores are better. A flight starts with its ticket price, then receives:

- A 100-point penalty for each stop.
- A 0.2-point penalty for each minute beyond 20 hours.

Change the constants near the top of `src/flight_ranker.py` to adjust those preferences.

## Saved data

- `data/price_history.json` stores every flight returned in successful reports, including the search profile name.
- `data/run_state.json` stores the last successful report time used by `schedule.every_hours`.

The workflow commits both files back to the branch using `github-actions[bot]`. If that push is rejected, check repository branch rules and ensure Actions has permission to write repository contents. The workflow requests only `contents: write` through its `GITHUB_TOKEN` permissions.

## Project layout

```text
.
├── config.json                 # Routes, filters, and report frequency
├── data/
│   ├── price_history.json      # Persisted flight observations
│   └── run_state.json          # Time of the last successful report
├── main.py                     # Application orchestration
├── src/
│   ├── config.py               # Configuration and secret loading
│   ├── emailer.py              # Grouped email formatting and Gmail SMTP
│   ├── flight_parser.py        # SerpApi response normalization
│   ├── flight_ranker.py        # Deal scoring and sorting
│   ├── flight_search.py        # SerpApi requests
│   ├── history.py              # Price-history persistence
│   ├── models.py               # Shared data models
│   └── scheduler.py            # Configurable interval gating
└── .github/workflows/
    └── daily-flight-search.yml # Hourly check and persistent automation
```

## Troubleshooting

### The workflow does not run

- Enable it from the **Actions** tab after forking.
- Make sure the workflow exists on your fork's default branch.
- Use **Run workflow** to bypass the configured interval.

### The tracker reports missing environment variables

Confirm that all four repository secrets exist and their names exactly match the table above. Secrets created in the upstream repository are not copied into a fork.

### Gmail rejects the login

Use a Google App Password, verify that `EMAIL_ADDRESS` belongs to the account that created it, and generate a replacement if the Google Account password was changed. Google revokes App Passwords after an account-password change.

### History does not update

Open the failed workflow run and inspect **Persist tracker data**. Branch protection or an organization policy may prevent `github-actions[bot]` from pushing directly to the selected branch.

### No flights are returned

Increase `max_price`, allow more stops, try additional origin airports, or use another trip length. You can also reproduce the query using the [SerpApi Google Travel Explore playground](https://serpapi.com/google-travel-explore-api).
