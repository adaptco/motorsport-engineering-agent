# Data Persistence and Storage Analysis

## Overview
This document analyzes the data persistence and storage components of the Motorsport Engineering Agent (MEA) system, focusing on database models, migration scripts, forensic ledger, session receipts, and data validation mechanisms.

## Database Models (shared/models.py)

The system uses Pydantic models for data validation and serialization:

### Core Data Models
- **TelemetryFrame**: Represents individual telemetry data points with session_id, driver_id, track_id, car_id, timestamp_ns, tick, and channels (numeric values)
- **EvidencePacket**: Contains evidence data with severity levels (CRITICAL, WARNING, ADVISORY, INFO, NONE) and features like brake_delta, turn_in_delta, etc.
- **Recommendation**: AI-generated recommendations linked to evidence packets with priority levels
- **Job Models**: FixCIRequest, JobStatusResponse for CI/CD integration

### Validation Features
- Strict type checking with Pydantic Field validators
- Channel validation ensures numeric values only
- Timestamp and tick monotonicity requirements
- JSON schema validation for complex nested structures

## Migration Scripts (db/migrations/)

### 001_init.sql - Initial Schema
- **github_installations**: GitHub App installation tracking
- **jobs**: CI/CD job management with status, phases, and GitHub integration
- **job_events**: Event logging for job lifecycle
- **traces/spans**: Distributed tracing support
- **receipts**: Session receipts for forensic auditing
- **artifacts**: Job artifact storage
- **webhook_events**: GitHub webhook event persistence

### 002_session_runtime.sql - Session Evidence
- **session_evidence**: Runtime evidence packet storage with logical timestamps
- **recommendations_runtime**: AI recommendations linked to evidence
- Indexed by session_id and timestamp for efficient querying

### 003_evidence_packets.sql - Evidence Storage
- **evidence_packets**: Dedicated evidence packet table
- Optimized indexing for session-based queries

## Forensic Ledger (shared/forensic_ledger.py)

### Purpose
The forensic ledger provides immutable, cryptographically verifiable audit trails for system decisions and state changes.

### Key Features
- **SQLite-based**: Uses SQLite with WAL mode for concurrent access
- **Hash Chaining**: Each receipt contains prev_hash and state_hash for tamper detection
- **Logical Clock**: Per-session monotonic counter for ordering
- **Decision Basis Hashing**: Canonical JSON hashing of decision parameters
- **Session Heads**: Tracks latest state per session

### Schema
- **receipts**: Immutable audit records with full context
- **session_heads**: Current state tracking per session

### Functions
- `append_receipt()`: Adds new audit entry with hash verification
- `get_session_head()`: Retrieves current session state
- `verify_chain()`: Validates entire audit chain integrity

## Session Receipts (control_plane/services/session_receipts.py)

### Functionality
- `build_state_surface()`: Creates standardized state representation from evidence packets and recommendations
- Integrates with forensic ledger for persistent audit trails

## Data Validation Mechanisms

### JSONL Validation (shared/jsonl_validator.py)
- **JSONLValidationResult**: Comprehensive validation report with line-by-line analysis
- **Validation Checks**:
  - JSON parsing errors
  - Required field presence
  - Schema validation against TelemetryFrame model
  - Timestamp monotonicity
  - Tick strict monotonicity
  - Empty line detection

### Key Validation Rules
- Required fields: session_id, driver_id, track_id, car_id, timestamp_ns, tick, channels
- Numeric channel values only
- Non-regressing timestamps
- Strictly increasing ticks

## Storage Architecture

### Multi-Layer Persistence
1. **PostgreSQL**: Primary relational database for structured data
2. **SQLite Forensic Ledger**: Immutable audit trails
3. **JSONL Files**: Telemetry data storage
4. **JSONB Fields**: Flexible metadata storage

### Data Flow
1. Telemetry ingested as JSONL
2. Validated and processed into evidence packets
3. AI analysis generates recommendations
4. All decisions logged to forensic ledger
5. Session state persisted with receipts

### Integrity Mechanisms
- Cryptographic hashing for audit trails
- Schema validation at ingestion
- Logical clock ordering
- Referential integrity in PostgreSQL

## Recommendations

### Potential Improvements
1. **Migration Versioning**: Consider adding version metadata to migration files
2. **Backup Strategy**: Document backup procedures for forensic ledger
3. **Performance Monitoring**: Add metrics for validation performance
4. **Schema Evolution**: Plan for evidence packet schema changes

### Security Considerations
- Forensic ledger provides non-repudiation
- Access controls via authz_scope in receipts
- Principal identification in all audit entries

This analysis confirms the system has robust data persistence with strong integrity guarantees and comprehensive validation mechanisms.</content>
<parameter name="filePath">c:\Users\eqhsp\Agent Projects\MotorsportEngineerAgent\motorsport-engineering-agent\docs\data_persistence_analysis.md