class LengthTooLong(Exception):
    pass


class NoMessageError(Exception):
    pass


class NoVoiceChannelError(Exception):
    pass


class APIReturnError(Exception):
    pass


class APINotUsingError(Exception):
    pass


class QueueMaxLengthError(Exception):
    pass
