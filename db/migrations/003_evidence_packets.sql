CREATE TABLE IF NOT EXISTS evidence_packets (
  evidence_packet_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  timestamp_logical_ns BIGINT NOT NULL,
  features JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_packets_session_ts
ON evidence_packets(session_id, timestamp_logical_ns);
