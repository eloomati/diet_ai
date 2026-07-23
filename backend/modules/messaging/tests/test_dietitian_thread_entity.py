import uuid

from backend.modules.messaging.domain.entities.dietitian_thread import DietitianThread


def test_create_sets_fields() -> None:
    user_id = uuid.uuid4()
    dietitian_id = uuid.uuid4()

    thread = DietitianThread.create(user_id=user_id, dietitian_id=dietitian_id)

    assert thread.user_id == user_id
    assert thread.dietitian_id == dietitian_id


def test_has_participant_true_for_either_side() -> None:
    user_id = uuid.uuid4()
    dietitian_id = uuid.uuid4()
    thread = DietitianThread.create(user_id=user_id, dietitian_id=dietitian_id)

    assert thread.has_participant(user_id)
    assert thread.has_participant(dietitian_id)
    assert not thread.has_participant(uuid.uuid4())


def test_other_participant_returns_the_opposite_side() -> None:
    user_id = uuid.uuid4()
    dietitian_id = uuid.uuid4()
    thread = DietitianThread.create(user_id=user_id, dietitian_id=dietitian_id)

    assert thread.other_participant(user_id) == dietitian_id
    assert thread.other_participant(dietitian_id) == user_id
