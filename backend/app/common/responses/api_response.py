from pydantic import BaseModel, ConfigDict


class ApiError(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    details: object | None = None


class ApiResponse[DataT](BaseModel):
    model_config = ConfigDict(frozen=True)

    success: bool
    data: DataT | None = None
    error: ApiError | None = None

    @classmethod
    def ok(cls, data: DataT) -> "ApiResponse[DataT]":
        return cls(success=True, data=data)

    @classmethod
    def fail(
        cls,
        code: str,
        message: str,
        details: object | None = None,
    ) -> "ApiResponse[DataT]":
        return cls(
            success=False,
            error=ApiError(code=code, message=message, details=details),
        )
