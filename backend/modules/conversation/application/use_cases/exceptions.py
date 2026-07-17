class ConversationApplicationError(Exception):
    pass


class ConversationNotFoundError(ConversationApplicationError):
    pass
