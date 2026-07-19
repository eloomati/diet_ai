from uuid import UUID

from fastapi import APIRouter, Depends, status

from backend.modules.admin.api.dependencies import (
    get_mark_transaction_paid_use_case,
    get_mark_transaction_unpaid_use_case,
)
from backend.modules.admin.application.use_cases.mark_transaction_paid_use_case import (
    MarkTransactionPaidUseCase,
)
from backend.modules.admin.application.use_cases.mark_transaction_unpaid_use_case import (
    MarkTransactionUnpaidUseCase,
)
from backend.modules.identity.api.dependencies import require_role
from backend.modules.identity.domain import Role, User
from backend.modules.transactions.api.schemas.transaction_schemas import TransactionResponse
from backend.modules.transactions.application.use_cases.exceptions import (
    TransactionNotFoundError,
)
from backend.shared.exceptions import AppException, ErrorCode

router = APIRouter(prefix="/admin/transactions", tags=["admin"])


@router.post(
    "/{transaction_id}/mark-paid",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_transaction_paid(
    transaction_id: UUID,
    _caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: MarkTransactionPaidUseCase = Depends(get_mark_transaction_paid_use_case),
) -> TransactionResponse:
    try:
        result = await use_case.execute(transaction_id)
    except TransactionNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc

    return TransactionResponse.from_result(result)


@router.post(
    "/{transaction_id}/mark-unpaid",
    response_model=TransactionResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_transaction_unpaid(
    transaction_id: UUID,
    _caller: User = Depends(require_role(Role.ADMIN, Role.SUPER_ADMIN)),
    use_case: MarkTransactionUnpaidUseCase = Depends(get_mark_transaction_unpaid_use_case),
) -> TransactionResponse:
    try:
        result = await use_case.execute(transaction_id)
    except TransactionNotFoundError as exc:
        raise AppException(
            code=ErrorCode.NOT_FOUND, message=str(exc), status_code=status.HTTP_404_NOT_FOUND
        ) from exc

    return TransactionResponse.from_result(result)
