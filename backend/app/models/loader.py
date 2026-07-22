def load_all_models() -> None:
    """Import ORM modules so SQLAlchemy can resolve string relationships."""
    from app.domains.auth.model import RefreshSession
    from app.domains.characters.model import Character, CharacterVersion
    from app.domains.conversations.model import Conversation
    from app.domains.messages.model import Message
    from app.domains.personas.model import Persona, PersonaVersion
    from app.domains.relationships.model import Relationship, RelationshipEvent
    from app.domains.users.model import User

    _ = (
        RefreshSession,
        Character,
        CharacterVersion,
        Conversation,
        Message,
        Persona,
        PersonaVersion,
        Relationship,
        RelationshipEvent,
        User,
    )
