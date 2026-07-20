from fastapi import APIRouter, Depends, status

from backend.modules.identity.api.dependencies import get_current_user, require_role
from backend.modules.identity.domain import Role, User
from backend.modules.transactions.api.dependencies import (
    get_create_transaction_use_case,
    get_my_transactions_as_dietitian_use_case,
)
from backend.modules.transactions.api.schemas import CreateTransactionRequest, TransactionResponse
from backend.modules.transactions.application.dto.transaction_dto import CreateTransactionCommand
from backend.modules.transactions.application.use_cases.create_transaction_use_case import (
    CreateTransactionUseCase,
)
from backend.modules.transactions.application.use_cases.exceptions import (
    DietitianNotFoundError,
)
from backend.modules.transactions.application.use_cases.get_my_transactions_as_dietitian_use_case import (
    GetMyTransactionsAsDietitianUseCase,
)
from backend.modules.transactions.domain.exceptions.transaction_domain_errors import (
    InvalidTransactionError,
)
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    request: CreateTransactionRequest,
    current_user: User = Depends(get_current_user),
    use_case: CreateTransactionUseCase = Depends(get_create_transaction_use_case),
) -> TransactionResponse:
    try:
        result = await use_case.execute(
            CreateTransactionCommand(
                user_id=current_user.id,
                dietitian_id=request.dietitian_id,
                offer_type=request.offer_type,
            )
        )
    except DietitianNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc
    except InvalidTransactionError as exc:
        raise AppException(
            code=ErrorCode.BAD_REQUEST, message=str(exc), status_code=status.HTTP_400_BAD_REQUEST
        ) from exc

    return TransactionResponse.from_result(result)


@router.get("/me", response_model=list[TransactionResponse], status_code=status.HTTP_200_OK)
async def get_my_transactions_as_dietitian(
    current_user: User = Depends(require_role(Role.DIET_USER)),
    use_case: GetMyTransactionsAsDietitianUseCase = Depends(
        get_my_transactions_as_dietitian_use_case
    ),
) -> list[TransactionResponse]:
    results = await use_case.execute(current_user.id)
    return [TransactionResponse.from_result(result) for result in results]
