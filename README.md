## Project Motivation & Origin

This project began with a simple but compelling question:

- __Is it possible to “beat” the lottery using data?__

Specifically, I wanted to explore whether Powerball and Mega Millions drawing outcomes exhibit any detectable patterns, biases, or statistical tendencies that could influence number selection, even in systems designed to be random.

While lottery systems are theoretically random, real-world randomness often invites deeper questions:

- __Are certain numbers drawn more frequently over long periods?__

- __Do number combinations cluster in observable ways?__

- __Are there psychological or structural biases (e.g., number ranges, human selection habits) that influence outcomes or perceived randomness?__

This curiosity led to the analytical phase of the project.

## Phase 1: Exploratory Data Analysis & Understanding Randomness

Before building any automation, the project focused on understanding the data itself:

Historical Powerball and Mega Millions draw data was collected

Frequency distributions were analyzed for:

- White balls

- Bonus balls (Powerball / Mega Ball)

- Long-term trends and draw counts were explored

Randomness was evaluated not to “prove predictability,” but to validate or challenge assumptions about true randomness

This phase reinforced an important conclusion:

__While lottery systems remain fundamentally random, analyzing randomness itself is a valuable data problem.__

That insight reframed the project.

## Phase 2: From Analysis to Automation

After understanding the statistical landscape, the project evolved into something more dynamic and practical:

Instead of a one-time analysis, I asked:

- __What if this analysis powered a system that runs every day, reacts to the calendar, and delivers results automatically?__

That shift led to the automation phase.

## Phase 3: Automated Data Pipeline & Daily Intelligence

The workflow executes the following stages:

## 1. Orchestration

- GitHub Actions acts as the workflow orchestrator

- A GitHub-hosted runner initializes the environment and installs dependencies

## 2. Data Ingestion

- Powerball draw data is fetched from a Powerball API

- Mega Millions data is fetched from New York Open Data (Socrata)

- Raw draw data is stored as versioned JSON in data/raw/

## 3. Business Logic

- The system determines which lottery has a drawing today based on the day of the week

- If a drawing is scheduled:

    - Five number combinations are generated using the bounded randomness model

    - Picks are written to data/generated/daily_picks_YYYY-MM-DD.json

- The system checks whether a drawing occurred yesterday

    - If so, yesterday’s picks are evaluated against official results

    - Evaluation output is saved to reports/daily/evaluation_YYYY-MM-DD.json

## 4. Reporting & Notification

- A formatted HTML report is composed containing:

    - Tonight’s picks

    - Yesterday’s evaluation results (if applicable)

- The report is sent via email using SMTP credentials stored securely in GitHub Secrets

## 5. Artifact Storage

- Generated picks and evaluation reports are uploaded as GitHub Actions artifacts

- This provides traceability, auditing, and reproducibility

