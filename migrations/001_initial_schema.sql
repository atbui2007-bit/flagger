CREATE TABLE pull_requests (
  id SERIAL PRIMARY KEY,
  repo_name TEXT NOT NULL,
  pr_number INT NOT NULL,
  author TEXT NOT NULL,
  title TEXT,
  opened_at TIMESTAMP DEFAULT NOW(),
  status TEXT DEFAULT 'pending'
);
CREATE TABLE risk_scores (
  id SERIAL PRIMARY KEY,
  pr_id INT REFERENCES pull_requests(id),
  overall_score FLOAT NOT NULL,
  ai_confidence FLOAT,
  security_risk FLOAT,
  debt_risk FLOAT,
  findings JSONB,
  scored_at TIMESTAMP DEFAULT NOW()
);