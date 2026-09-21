from pydantic import BaseModel, ConfigDict


class APIResponse[T](BaseModel):
    code: int
    message: str
    data: T | None = None

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def success(
        cls,
        *,
        code: int = 0,
        message: str = "success",
        data: T | None = None,
    ) -> APIResponse[T]:
        return cls(code=code, message=message, data=data)

    @classmethod
    def fail(
        cls,
        *,
        code: int = 1,
        message: str = "fail",
        data: T | None = None,
    ) -> APIResponse[T]:
        return cls(code=code, message=message, data=data)
