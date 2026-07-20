ALTER TABLE pull_requests ADD COLUMN merge_commit_sha TEXT;
CREATE INDEX idx_pull_requests_merge_commit_sha ON pull_requests (repo_id, merge_commit_sha);
