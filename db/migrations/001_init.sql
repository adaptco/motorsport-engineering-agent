CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS github_installations (
  installation_id BIGINT PRIMARY KEY,
  account_login TEXT,
  account_type TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
  job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_type TEXT NOT NULL,
  repo_slug TEXT NOT NULL,
  base_branch TEXT NOT NULL,
  fix_branch TEXT,
  github_run_id TEXT,
  github_pr_number INTEGER,
  github_pr_url TEXT,
  status TEXT NOT NULL,
  phase TEXT NOT NULL,
  patch_hash TEXT,
  trace_id UUID,
  receipt_id UUID,
  request_payload JSONB NOT NULL,
  result_payload JSONB,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_repo_status ON jobs(repo_slug, status);

CREATE TABLE IF NOT EXISTS job_events (
  event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  level TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS traces (
  trace_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL UNIQUE REFERENCES jobs(job_id) ON DELETE CASCADE,
  trace_name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS spans (
  span_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trace_id UUID NOT NULL REFERENCES traces(trace_id) ON DELETE CASCADE,
  parent_span_id UUID REFERENCES spans(span_id) ON DELETE SET NULL,
  span_name TEXT NOT NULL,
  status TEXT NOT NULL,
  attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS receipts (
  receipt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL UNIQUE REFERENCES jobs(job_id) ON DELETE CASCADE,
  outcome TEXT NOT NULL,
  epoch INTEGER NOT NULL DEFAULT 1,
  lineage JSONB NOT NULL DEFAULT '{}'::jsonb,
  state_delta JSONB NOT NULL DEFAULT '{}'::jsonb,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
  artifact_type TEXT NOT NULL,
  content JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS webhook_events (
  delivery_id TEXT PRIMARY KEY,
  event_name TEXT NOT NULL,
  repo_slug TEXT,
  payload JSONB NOT NULL,
  received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
