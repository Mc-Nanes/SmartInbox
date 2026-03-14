class AppBaseException(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InvalidInputError(AppBaseException):
    pass


class FileProcessingError(AppBaseException):
    pass


class OpenAIIntegrationError(AppBaseException):
    pass


class ServiceConfigurationError(AppBaseException):
    pass


class InternalServerError(AppBaseException):
    pass
