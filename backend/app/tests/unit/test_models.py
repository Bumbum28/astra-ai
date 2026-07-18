from app.domains.users.model import User


def test_entities_eagerly_load_database_generated_timestamps() -> None:
    assert User.__mapper__.eager_defaults is True
