from unittest import TestCase
from unittest.mock import Mock, patch

from botocore.exceptions import ClientError

from app.services.vector_db import pgvector_schema


def _resuming_error() -> ClientError:
    return ClientError(
        {
            "Error": {
                "Code": "DatabaseResumingException",
                "Message": "Database is resuming",
            }
        },
        "ExecuteStatement",
    )


class TestPgVectorWarmup(TestCase):
    def test_warmup_retry_waits_longer_than_normal_search_retry(self):
        operation = Mock(
            side_effect=[_resuming_error(), _resuming_error(), "ok"]
        )
        sleeps: list[float] = []

        with (
            patch.object(pgvector_schema.time, "sleep", sleeps.append),
            patch.object(
                pgvector_schema.time,
                "monotonic",
                Mock(side_effect=[0, 1, 3]),
            ),
        ):
            result = pgvector_schema.call_with_warmup_retry(
                operation,
                max_wait_seconds=90,
            )

        self.assertEqual(result, "ok")
        self.assertEqual(sleeps, [2.0, 4.0])
        self.assertEqual(operation.call_count, 3)

    def test_warmup_retry_does_not_hide_other_database_errors(self):
        operation = Mock(
            side_effect=ClientError(
                {"Error": {"Code": "AccessDeniedException"}},
                "ExecuteStatement",
            )
        )

        with self.assertRaises(ClientError):
            pgvector_schema.call_with_warmup_retry(operation)
