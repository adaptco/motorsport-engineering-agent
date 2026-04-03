
CREATE TABLE IF NOT EXISTS session_evidence (
  evidence_packet_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  timestamp_logical_ns BIGINT NOT NULL,
  timestamp_wall TIMESTAMPTZ,
  severity TEXT NOT NULL,
  features JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recommendations_runtime (
  recommendation_id TEXT PRIMARY KEY,
  evidence_packet_id TEXT NOT NULL REFERENCES session_evidence(evidence_packet_id) ON DELETE CASCADE,
  priority TEXT NOT NULL,
  trigger TEXT,
  action TEXT,
  expected_effect TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_evidence_session_timestamp
ON session_evidence(session_id, timestamp_logical_ns);
