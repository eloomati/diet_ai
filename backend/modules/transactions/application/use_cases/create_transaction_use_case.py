from backend.modules.transactions.application.dto.transaction_dto import (
    CreateTransactionCommand,
    TransactionResult,
)
from backend.modules.transactions.application.use_cases.exceptions import (
    DietitianNotFoundError,
    EmailNotVerifiedError,
)
from backend.modules.transactions.domain.entities.transaction import Transaction
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.role import Role


class CreateTransactionUseCase:
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        user_repository: UserRepository,
    ) -> None:
        self._transaction_repository = transaction_repository
        self._user_repository = user_repository

    async def execute(self, command: CreateTransactionCommand) -> TransactionResult:
        dietitian = await self._user_repository.get_by_id(command.dietitian_id)
        if dietitian is None or dietitian.role != Role.DIET_USER:
            raise DietitianNotFoundError("No dietitian found for this id.")

        # Account status (banned/inactive) is already enforced upstream by
        # get_current_user's assert_can_authenticate() — every authenticated
        # route gets that for free. Email verification isn't, though: it's
        # tracked but never otherwise enforced, so it's checked here,
        # specifically for buying an offer.
        buyer = await self._user_repository.get_by_id(command.user_id)
        if not buyer.email_verified:
            raise EmailNotVerifiedError("Verify your email before purchasing an offer.")

        # Transaction.create() raises InvalidTransactionError if
        # user_id == dietitian_id — a pure data invariant, not re-checked
        # here.
        transaction = Transaction.create(
            user_id=command.user_id,
            dietitian_id=command.dietitian_id,
            offer_type=command.offer_type,
        )
        await self._transaction_repository.save(transaction)

        return TransactionResult.from_domain(transaction)
