CREATE TABLE IF NOT EXISTS jobs (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identity / dedup keys
    url                   TEXT NOT NULL UNIQUE,
    title                 TEXT NOT NULL,
    company               TEXT NOT NULL,

    -- Job content
    location              TEXT,
    description           TEXT,
    date_posted           TEXT,
    salary_min            REAL,
    salary_max            REAL,
    is_remote             INTEGER DEFAULT 0,
    source                TEXT,

    -- Pre-filter metadata
    visa_signals          TEXT,   -- JSON array of matched signals

    -- Claude scores (NULL until scored)
    skill_match_score     REAL,
    visa_friendly_score   REAL,
    relevance_score       REAL,
    competition_score     REAL,
    overall_score         REAL,
    jd_summary            TEXT,
    recommendation        TEXT,

    -- Lifecycle
    scraped_at            TEXT NOT NULL,
    scored_at             TEXT,
    emailed               INTEGER DEFAULT 0,
    applied               INTEGER DEFAULT 0,

    UNIQUE(title, company)
);

CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at     ON jobs(scraped_at);
CREATE INDEX IF NOT EXISTS idx_jobs_overall_score  ON jobs(overall_score);
CREATE INDEX IF NOT EXISTS idx_jobs_emailed        ON jobs(emailed);

CREATE TABLE IF NOT EXISTS coffee_chat_targets (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    name                  TEXT NOT NULL,
    title                 TEXT,
    company               TEXT,
    linkedin_url          TEXT UNIQUE,
    school                TEXT,
    connection_type       TEXT,
    personalized_message  TEXT,
    generated_at          TEXT NOT NULL,
    sent                  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tailored_resumes (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id                INTEGER REFERENCES jobs(id) ON DELETE SET NULL,
    job_title             TEXT,
    company               TEXT,
    missing_keywords      TEXT,
    tailored_bullets      TEXT,
    papers_to_highlight   TEXT,
    summary_suggestion    TEXT,
    output_file           TEXT,
    generated_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS email_log (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    sent_at               TEXT NOT NULL,
    jobs_included         INTEGER,
    email_to              TEXT,
    github_run_id         TEXT,
    status                TEXT
);
