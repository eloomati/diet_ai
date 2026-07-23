class MessagingApplicationError(Exception):
    pass


class ThreadNotFoundError(MessagingApplicationError):
    pass


class ThreadAccessDeniedError(MessagingApplicationError):
    pass
