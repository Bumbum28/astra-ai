def load_all_models() -> None:
    """Import ORM modules so SQLAlchemy can resolve string relationships."""
    from app.domains.auth.model import RefreshSession
    from app.domains.conversations.model import Conversation
    from app.domains.messages.model import Message
    from app.domains.users.model import User

    _ = (RefreshSession, Conversation, Message, User)
