"""PostgreSQL implementation of the asynchronous execution repository port.

The adapter persists the existing Gate 3 domain model. It deliberately does not
start work, publish queue messages, or alter worker behavior. An async
application service can adopt this adapter in a later, separately reviewed
increment.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from services.orchestrator.domain.models import (
    CommandType,
    ExecutionCommand,
    ExecutionLease,
    ExecutionReceipt,
    ExecutionRun,
    ExecutionState,
    RuntimeEvent,
    event_global_hash,
    event_payload_hash,
    new_event_id,
)
from services.orchestrator.infrastructure.in_memory_execution_repository import (
    StaleAggregateVersionError,
)
from services.orchestrator.ports.async_execution_repository import AsyncExecutionRepository
from shared.db import DATABASE_URL, DB_CONNECT_TIMEOUT_SECONDS

ConnectionFactory = Callable[[], Awaitable[AsyncConnection[Any]]]
Row = Mapping[str, Any]


class PostgresExecutionRepository(AsyncExecutionRepository):
    """Durable async adapter for the orchestrator execution persistence schema."""

    def __init__(
        self,
        *,
        database_url: str = DATABASE_URL,
        connect_timeout_seconds: int = DB_CONNECT_TIMEOUT_SECONDS,
        connection_factory: ConnectionFactory | None = None,
    ) -> None:
        self._database_url = database_url
        self._connect_timeout_seconds = connect_timeout_seconds
        self._connection_factory = connection_factory or self._connect

    async def _connect(self) -> AsyncConnection[Any]:
        return await AsyncConnection.connect(
            self._database_url,
            connect_timeout=self._connect_timeout_seconds,
            row_factory=dict_row,
        )

    @asynccontextmanager
    async def _transaction(self) -> AsyncIterator[AsyncConnection[Any]]:
        connection = await self._connection_factory()
        async with connection:
            async with connection.transaction():
                yield connection

    async def find_command_by_idempotency(
        self, idempotency_key: str
    ) -> tuple[ExecutionCommand, str] | None:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT command_id, command_type, idempotency_key, workflow_type, priority,
                       input, request_id, trace_id, principal_id, issued_at, run_id
                FROM orchestrator_commands
                WHERE idempotency_key = %s
                """,
                (idempotency_key,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        command = self._command_from_row(row)
        return command, str(row["run_id"])

    async def save_command(self, command: ExecutionCommand, run_id: str) -> None:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO orchestrator_commands (
                  idempotency_key, command_id, run_id, command_type, workflow_type, priority,
                  input, request_id, trace_id, principal_id, issued_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING command_id
                """,
                (
                    command.idempotency_key,
                    command.command_id,
                    run_id,
                    command.command_type.value,
                    command.workflow_type,
                    command.priority,
                    json.dumps(command.input),
                    command.request_id,
                    command.trace_id,
                    command.principal_id,
                    command.issued_at,
                ),
            )
            inserted = await cursor.fetchone()
            if inserted is not None:
                return
            await cursor.execute(
                "SELECT command_id FROM orchestrator_commands WHERE idempotency_key = %s",
                (command.idempotency_key,),
            )
            existing = await cursor.fetchone()
        if existing is None or str(existing["command_id"]) != command.command_id:
            raise ValueError("IDEMPOTENCY_CONFLICT")

    async def create_run(self, run: ExecutionRun) -> None:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await cursor.execute(
                """
                INSERT INTO orchestrator_runs (
                  run_id, workflow_type, priority, state, aggregate_version, trace_id, request_id,
                  principal_id, current_attempt_id, current_lease_id, last_event_id, last_receipt_id,
                  created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (run_id) DO NOTHING
                RETURNING run_id
                """,
                self._run_values(run),
            )
            inserted = await cursor.fetchone()
        if inserted is None:
            raise ValueError("RUN_ALREADY_EXISTS")

    async def get_run(self, run_id: str) -> ExecutionRun | None:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await cursor.execute("SELECT * FROM orchestrator_runs WHERE run_id = %s", (run_id,))
            row = await cursor.fetchone()
        return self._run_from_row(row) if row is not None else None

    async def list_runs(self, *, status: str | None = None) -> list[ExecutionRun]:
        async with self._transaction() as connection, connection.cursor() as cursor:
            if status:
                await cursor.execute(
                    """
                    SELECT * FROM orchestrator_runs
                    WHERE state = %s
                    ORDER BY created_at ASC, run_id ASC
                    """,
                    (status,),
                )
            else:
                await cursor.execute(
                    "SELECT * FROM orchestrator_runs ORDER BY created_at ASC, run_id ASC"
                )
            rows = await cursor.fetchall()
        return [self._run_from_row(row) for row in rows]

    async def active_lease_for_run(self, run_id: str) -> ExecutionLease | None:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await cursor.execute(
                """
                SELECT lease_id, run_id, attempt_id, executor_id, acquired_at, expires_at
                FROM orchestrator_leases
                WHERE run_id = %s AND expires_at > NOW()
                ORDER BY acquired_at DESC, lease_id DESC
                LIMIT 1
                """,
                (run_id,),
            )
            row = await cursor.fetchone()
        return self._lease_from_row(row) if row is not None else None

    async def save_lease(self, lease: ExecutionLease) -> None:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await cursor.execute(
                "SELECT run_id FROM orchestrator_runs WHERE run_id = %s FOR UPDATE",
                (lease.run_id,),
            )
            if await cursor.fetchone() is None:
                raise KeyError("RUN_NOT_FOUND")
            await cursor.execute(
                """
                SELECT lease_id FROM orchestrator_leases
                WHERE run_id = %s AND expires_at > NOW()
                ORDER BY acquired_at DESC, lease_id DESC
                LIMIT 1
                """,
                (lease.run_id,),
            )
            active = await cursor.fetchone()
            if active is not None and str(active["lease_id"]) != lease.lease_id:
                raise ValueError("LEASE_CONFLICT")
            await cursor.execute(
                """
                INSERT INTO orchestrator_leases (
                  lease_id, run_id, attempt_id, executor_id, acquired_at, expires_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (lease_id) DO NOTHING
                """,
                (
                    lease.lease_id,
                    lease.run_id,
                    lease.attempt_id,
                    lease.executor_id,
                    lease.acquired_at,
                    lease.expires_at,
                ),
            )

    async def append_event(
        self,
        *,
        run_id: str,
        expected_aggregate_version: int,
        event_type: str,
        payload: dict[str, Any],
        new_run: ExecutionRun,
    ) -> RuntimeEvent:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await cursor.execute(
                "SELECT * FROM orchestrator_runs WHERE run_id = %s FOR UPDATE", (run_id,)
            )
            current_row = await cursor.fetchone()
            if current_row is None:
                raise KeyError("RUN_NOT_FOUND")
            current = self._run_from_row(current_row)
            if current.aggregate_version != expected_aggregate_version:
                raise StaleAggregateVersionError(
                    "STALE_AGGREGATE_VERSION: "
                    f"expected={expected_aggregate_version}, actual={current.aggregate_version}"
                )
            if new_run.aggregate_version != current.aggregate_version + 1:
                raise ValueError("INVALID_AGGREGATE_VERSION")

            await cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext('orchestrator_events_global_chain'))"
            )
            await cursor.execute(
                "SELECT global_hash FROM orchestrator_events "
                "ORDER BY global_event_index DESC LIMIT 1"
            )
            previous = await cursor.fetchone()
            previous_global_hash = str(previous["global_hash"]) if previous is not None else None
            await cursor.execute(
                """
                SELECT nextval(
                  pg_get_serial_sequence('orchestrator_events', 'global_event_index')
                ) AS global_event_index
                """
            )
            sequence_row = await cursor.fetchone()
            if sequence_row is None:
                raise RuntimeError("EVENT_SEQUENCE_UNAVAILABLE")
            global_event_index = int(sequence_row["global_event_index"])
            event_id = new_event_id()
            payload_hash = event_payload_hash(payload)
            event = RuntimeEvent(
                event_id=event_id,
                event_type=event_type,
                run_id=run_id,
                aggregate_version=new_run.aggregate_version,
                global_event_index=global_event_index,
                occurred_at=new_run.updated_at,
                payload=dict(payload),
                payload_hash=payload_hash,
                previous_global_hash=previous_global_hash,
                global_hash=event_global_hash(
                    event_id=event_id,
                    event_type=event_type,
                    run_id=run_id,
                    aggregate_version=new_run.aggregate_version,
                    global_event_index=global_event_index,
                    occurred_at=new_run.updated_at,
                    payload_hash=payload_hash,
                    previous_global_hash=previous_global_hash,
                ),
            )
            await cursor.execute(
                """
                INSERT INTO orchestrator_events (
                  event_id, run_id, event_type, aggregate_version, global_event_index, occurred_at,
                  payload, payload_hash, previous_global_hash, global_hash
                ) VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                """,
                (
                    event.event_id,
                    event.run_id,
                    event.event_type,
                    event.aggregate_version,
                    event.global_event_index,
                    event.occurred_at,
                    json.dumps(event.payload),
                    event.payload_hash,
                    event.previous_global_hash,
                    event.global_hash,
                ),
            )
            await cursor.execute(
                """
                UPDATE orchestrator_runs
                SET state = %s, aggregate_version = %s, current_attempt_id = %s,
                    current_lease_id = %s, last_event_id = %s, updated_at = %s
                WHERE run_id = %s
                """,
                (
                    new_run.state.value,
                    new_run.aggregate_version,
                    new_run.current_attempt_id,
                    new_run.current_lease_id,
                    event.event_id,
                    new_run.updated_at,
                    run_id,
                ),
            )
        return event

    async def append_receipt(self, receipt: ExecutionReceipt) -> None:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await cursor.execute(
                "SELECT run_id FROM orchestrator_runs WHERE run_id = %s FOR UPDATE",
                (receipt.run_id,),
            )
            if await cursor.fetchone() is None:
                raise KeyError("RUN_NOT_FOUND")
            await cursor.execute(
                """
                SELECT logical_clock, state_hash
                FROM orchestrator_receipts
                WHERE run_id = %s
                ORDER BY logical_clock DESC
                LIMIT 1
                """,
                (receipt.run_id,),
            )
            previous = await cursor.fetchone()
            expected_clock = int(previous["logical_clock"]) + 1 if previous is not None else 1
            expected_hash = str(previous["state_hash"]) if previous is not None else None
            if receipt.logical_clock != expected_clock or receipt.previous_hash != expected_hash:
                raise ValueError("RECEIPT_INTEGRITY_FAILURE")
            await cursor.execute(
                """
                INSERT INTO orchestrator_receipts (
                  receipt_id, run_id, event_id, logical_clock, receipt_type, previous_hash,
                  state_hash, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    receipt.receipt_id,
                    receipt.run_id,
                    receipt.event_id,
                    receipt.logical_clock,
                    receipt.receipt_type,
                    receipt.previous_hash,
                    receipt.state_hash,
                    receipt.created_at,
                ),
            )
            await cursor.execute(
                "UPDATE orchestrator_runs SET last_receipt_id = %s WHERE run_id = %s",
                (receipt.receipt_id, receipt.run_id),
            )

    async def events_for_run(self, run_id: str) -> list[RuntimeEvent]:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await self._require_run(cursor, run_id)
            await cursor.execute(
                "SELECT * FROM orchestrator_events WHERE run_id = %s ORDER BY aggregate_version ASC",
                (run_id,),
            )
            rows = await cursor.fetchall()
        return [self._event_from_row(row) for row in rows]

    async def receipts_for_run(self, run_id: str) -> list[ExecutionReceipt]:
        async with self._transaction() as connection, connection.cursor() as cursor:
            await self._require_run(cursor, run_id)
            await cursor.execute(
                "SELECT * FROM orchestrator_receipts WHERE run_id = %s ORDER BY logical_clock ASC",
                (run_id,),
            )
            rows = await cursor.fetchall()
        return [self._receipt_from_row(row) for row in rows]

    async def _require_run(self, cursor: Any, run_id: str) -> None:
        await cursor.execute("SELECT run_id FROM orchestrator_runs WHERE run_id = %s", (run_id,))
        if await cursor.fetchone() is None:
            raise KeyError("RUN_NOT_FOUND")

    @staticmethod
    def _command_from_row(row: Row) -> ExecutionCommand:
        return ExecutionCommand(
            command_id=str(row["command_id"]),
            command_type=CommandType(str(row["command_type"])),
            idempotency_key=str(row["idempotency_key"]),
            workflow_type=str(row["workflow_type"]),
            priority=str(row["priority"]),
            input=dict(row["input"]),
            request_id=str(row["request_id"]),
            trace_id=str(row["trace_id"]),
            principal_id=str(row["principal_id"]),
            issued_at=PostgresExecutionRepository._utc(row["issued_at"]),
        )

    @staticmethod
    def _run_from_row(row: Row) -> ExecutionRun:
        return ExecutionRun(
            run_id=str(row["run_id"]),
            workflow_type=str(row["workflow_type"]),
            priority=str(row["priority"]),
            state=ExecutionState(str(row["state"])),
            aggregate_version=int(row["aggregate_version"]),
            trace_id=str(row["trace_id"]),
            request_id=str(row["request_id"]),
            principal_id=str(row["principal_id"]),
            created_at=PostgresExecutionRepository._utc(row["created_at"]),
            updated_at=PostgresExecutionRepository._utc(row["updated_at"]),
            current_attempt_id=row.get("current_attempt_id"),
            current_lease_id=row.get("current_lease_id"),
            last_event_id=row.get("last_event_id"),
            last_receipt_id=row.get("last_receipt_id"),
        )

    @staticmethod
    def _lease_from_row(row: Row) -> ExecutionLease:
        return ExecutionLease(
            lease_id=str(row["lease_id"]),
            run_id=str(row["run_id"]),
            attempt_id=str(row["attempt_id"]),
            executor_id=str(row["executor_id"]),
            acquired_at=PostgresExecutionRepository._utc(row["acquired_at"]),
            expires_at=PostgresExecutionRepository._utc(row["expires_at"]),
        )

    @staticmethod
    def _event_from_row(row: Row) -> RuntimeEvent:
        return RuntimeEvent(
            event_id=str(row["event_id"]),
            event_type=str(row["event_type"]),
            run_id=str(row["run_id"]),
            aggregate_version=int(row["aggregate_version"]),
            global_event_index=int(row["global_event_index"]),
            occurred_at=PostgresExecutionRepository._utc(row["occurred_at"]),
            payload=dict(row["payload"]),
            payload_hash=str(row["payload_hash"]),
            previous_global_hash=row.get("previous_global_hash"),
            global_hash=str(row["global_hash"]),
        )

    @staticmethod
    def _receipt_from_row(row: Row) -> ExecutionReceipt:
        return ExecutionReceipt(
            receipt_id=str(row["receipt_id"]),
            run_id=str(row["run_id"]),
            event_id=str(row["event_id"]),
            logical_clock=int(row["logical_clock"]),
            receipt_type=str(row["receipt_type"]),
            previous_hash=row.get("previous_hash"),
            state_hash=str(row["state_hash"]),
            created_at=PostgresExecutionRepository._utc(row["created_at"]),
        )

    @staticmethod
    def _run_values(run: ExecutionRun) -> tuple[Any, ...]:
        return (
            run.run_id,
            run.workflow_type,
            run.priority,
            run.state.value,
            run.aggregate_version,
            run.trace_id,
            run.request_id,
            run.principal_id,
            run.current_attempt_id,
            run.current_lease_id,
            run.last_event_id,
            run.last_receipt_id,
            run.created_at,
            run.updated_at,
        )

    @staticmethod
    def _utc(value: Any) -> datetime:
        if not isinstance(value, datetime):
            raise TypeError("DATABASE_DATETIME_INVALID")
        return value.astimezone(UTC)
