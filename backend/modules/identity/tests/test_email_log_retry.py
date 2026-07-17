from datetime import UTC, datetime, timedelta

from backend.modules.identity.domain.entities.email_log import EmailDeliveryStatus, EmailLog


def test_record_failed_schedules_next_retry() -> None:
    before = datetime.now(UTC)
    log = EmailLog.record_failed(
        to="user@example.com",
        subject="Subject",
        purpose="PASSWORD_RESET",
        error_message="boom",
        max_attempts=10,
        retry_interval_seconds=180,
    )

    assert log.status == EmailDeliveryStatus.FAILED
    assert log.attempts == 1
    assert log.next_retry_at is not None
    assert log.next_retry_at >= before + timedelta(seconds=180)


def test_record_failed_with_max_attempts_one_does_not_schedule_retry() -> None:
    log = EmailLog.record_failed(
        to="user@example.com",
        subject="Subject",
        purpose="PASSWORD_RESET",
        error_message="boom",
        max_attempts=1,
    )

    assert log.next_retry_at is None


def test_is_due_for_retry_true_once_next_retry_at_has_passed() -> None:
    log = EmailLog.record_failed(
        to="user@example.com", subject="Subject", purpose="PASSWORD_RESET", error_message="boom"
    )
    log.next_retry_at = datetime.now(UTC) - timedelta(seconds=1)

    assert log.is_due_for_retry() is True


def test_is_due_for_retry_false_before_next_retry_at() -> None:
    log = EmailLog.record_failed(
        to="user@example.com", subject="Subject", purpose="PASSWORD_RESET", error_message="boom"
    )

    assert log.is_due_for_retry() is False


def test_is_due_for_retry_false_when_sent() -> None:
    log = EmailLog.record_sent(to="user@example.com", subject="Subject", purpose="PASSWORD_RESET")

    assert log.is_due_for_retry() is False


def test_mark_retry_succeeded_clears_error_and_schedule() -> None:
    log = EmailLog.record_failed(
        to="user@example.com", subject="Subject", purpose="PASSWORD_RESET", error_message="boom"
    )

    log.mark_retry_succeeded()

    assert log.status == EmailDeliveryStatus.SENT
    assert log.error_message is None
    assert log.next_retry_at is None


def test_mark_retry_failed_increments_attempts_and_reschedules() -> None:
    log = EmailLog.record_failed(
        to="user@example.com", subject="Subject", purpose="PASSWORD_RESET", error_message="boom"
    )

    log.mark_retry_failed("still broken", max_attempts=10, retry_interval_seconds=180)

    assert log.attempts == 2
    assert log.status == EmailDeliveryStatus.FAILED
    assert log.error_message == "still broken"
    assert log.next_retry_at is not None


def test_mark_retry_failed_stops_scheduling_once_max_attempts_reached() -> None:
    log = EmailLog.record_failed(
        to="user@example.com", subject="Subject", purpose="PASSWORD_RESET", error_message="boom"
    )
    log.attempts = 9

    log.mark_retry_failed("still broken", max_attempts=10, retry_interval_seconds=180)

    assert log.attempts == 10
    assert log.status == EmailDeliveryStatus.FAILED
    assert log.next_retry_at is None
    assert log.is_due_for_retry() is False
