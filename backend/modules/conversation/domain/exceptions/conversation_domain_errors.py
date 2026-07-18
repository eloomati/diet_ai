class ConversationDomainError(Exception):
    pass


class ArchivedConversationError(ConversationDomainError):
    pass


class InvalidConversationError(ConversationDomainError):
    pass
