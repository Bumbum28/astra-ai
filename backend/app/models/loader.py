def load_all_models() -> None:
    """Import ORM modules so SQLAlchemy can resolve string relationships."""
    from app.agents.model import AgentRun, AgentStep
    from app.domains.auth.model import RefreshSession
    from app.domains.characters.model import Character
    from app.domains.conversations.model import Conversation
    from app.domains.knowledge.model import KnowledgeChunk, KnowledgeSource
    from app.domains.memories.model import Memory
    from app.domains.messages.model import Message
    from app.domains.personas.model import Persona
    from app.domains.users.model import User

    _ = (
        AgentRun,
        AgentStep,
        RefreshSession,
        Character,
        Conversation,
        KnowledgeChunk,
        KnowledgeSource,
        Memory,
        Message,
        Persona,
        User,
    )
