DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'check_jobs_status'
  ) THEN
    ALTER TABLE jobs
      ADD CONSTRAINT check_jobs_status
      CHECK (status IN ('queued', 'running', 'succeeded', 'failed'));
  END IF;
END $$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'check_jobs_phase'
  ) THEN
    ALTER TABLE jobs
      ADD CONSTRAINT check_jobs_phase
      CHECK (
        phase IN (
          'accepted',
          'running',
          'complete',
          'error',
          'policy_check',
          'token_issued',
          'cloned',
          'patched',
          'validated',
          'pushed',
          'validation_failed'
        )
      );
  END IF;
END $$;
