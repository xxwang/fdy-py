class APIException(Exception):
    def __init__(
        self,
        code: int = 1,
        message: str = "业务处理失败",
        status_code: int = 400,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
