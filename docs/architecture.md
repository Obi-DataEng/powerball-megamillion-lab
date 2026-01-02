```mermaid
flowchart TD
    A[GitHub Actions<br/>Cron / Manual Dispatch]
    --> B[Runner: Setup Python + Dependencies]

    B --> C[Ingest Draw Data]

    C --> C1[Powerball API<br/>data/raw/powerball_draws.json]
    C --> C2[NY Open Data (Socrata)<br/>data/raw/megamillions_draws.json]

    C --> D{Is there a draw today?}

    D -- Yes --> E[Generate Tonight's Picks]
    E --> E1[data/generated/daily_picks_YYYY-MM-DD.json]

    D -- No --> E0[Skip Picks]

    E1 --> F{Was there a draw yesterday?}

    F -- Yes --> G[Evaluate Yesterday's Picks]
    G --> G1[reports/daily/evaluation_YYYY-MM-DD.json]

    F -- No --> G0[No Evaluation]

    E1 --> H[Compose HTML Report]
    G1 --> H
    G0 --> H

    H --> I[Send Email via SMTP]
    H --> J[Upload Outputs as GitHub Artifact]
