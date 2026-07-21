from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.admin.application.use_cases.activate_user_use_case import ActivateUserUseCase
from backend.modules.admin.application.use_cases.approve_dietitian_application_use_case import (
    ApproveDietitianApplicationUseCase,
)
from backend.modules.admin.application.use_cases.ban_user_use_case import BanUserUseCase
from backend.modules.admin.application.use_cases.delete_user_use_case import DeleteUserUseCase
from backend.modules.admin.application.use_cases.list_dietitian_applications_use_case import (
    ListDietitianApplicationsUseCase,
)
from backend.modules.admin.application.use_cases.list_transactions_use_case import (
    ListTransactionsUseCase,
)
from backend.modules.admin.application.use_cases.list_users_use_case import ListUsersUseCase
from backend.modules.admin.application.use_cases.mark_transaction_paid_use_case import (
    MarkTransactionPaidUseCase,
)
from backend.modules.admin.application.use_cases.mark_transaction_unpaid_use_case import (
    MarkTransactionUnpaidUseCase,
)
from backend.modules.admin.application.use_cases.reject_dietitian_application_use_case import (
    RejectDietitianApplicationUseCase,
)
from backend.modules.conversation.api.dependencies import get_conversation_repository
from backend.modules.conversation.domain.repositories.conversation_repository import (
    ConversationRepository,
)
from backend.modules.dietitian.api.dependencies import (
    get_dietitian_application_repository,
    get_dietitian_profile_repository,
)
from backend.modules.dietitian.domain.repositories.dietitian_application_repository import (
    DietitianApplicationRepository,
)
from backend.modules.dietitian.domain.repositories.dietitian_profile_repository import (
    DietitianProfileRepository,
)
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.infrastructure.persistence.repository.sqlalchemy_user_repository import (
    SqlAlchemyUserRepository,
)
from backend.modules.nutrition.api.dependencies import (
    get_diet_plan_export_repository,
    get_diet_plan_repository,
    get_nutrition_profile_repository,
)
from backend.modules.nutrition.domain.repositories.diet_plan_export_repository import (
    DietPlanExportRepository,
)
from backend.modules.nutrition.domain.repositories.diet_plan_repository import DietPlanRepository
from backend.modules.nutrition.domain.repositories.nutrition_profile_repository import (
    NutritionProfileRepository,
)
from backend.modules.transactions.api.dependencies import (
    get_transaction_event_publisher,
    get_transaction_repository,
)
from backend.modules.transactions.application.ports.transaction_event_publisher import (
    TransactionEventPublisher,
)
from backend.modules.transactions.domain.repositories.transaction_repository import (
    TransactionRepository,
)
from backend.shared.database import get_db_session


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return SqlAlchemyUserRepository(session)


def get_list_users_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> ListUsersUseCase:
    return ListUsersUseCase(user_repository)


def get_activate_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> ActivateUserUseCase:
    return ActivateUserUseCase(user_repository)


def get_ban_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
) -> BanUserUseCase:
    return BanUserUseCase(user_repository)


def get_delete_user_use_case(
    user_repository: UserRepository = Depends(get_user_repository),
    conversation_repository: ConversationRepository = Depends(get_conversation_repository),
    nutrition_profile_repository: NutritionProfileRepository = Depends(
        get_nutrition_profile_repository
    ),
    diet_plan_repository: DietPlanRepository = Depends(get_diet_plan_repository),
    diet_plan_export_repository: DietPlanExportRepository = Depends(
        get_diet_plan_export_repository
    ),
) -> DeleteUserUseCase:
    return DeleteUserUseCase(
        user_repository,
        conversation_repository,
        nutrition_profile_repository,
        diet_plan_repository,
        diet_plan_export_repository,
    )


def get_list_dietitian_applications_use_case(
    application_repository: DietitianApplicationRepository = Depends(
        get_dietitian_application_repository
    ),
) -> ListDietitianApplicationsUseCase:
    return ListDietitianApplicationsUseCase(application_repository)


def get_approve_dietitian_application_use_case(
    application_repository: DietitianApplicationRepository = Depends(
        get_dietitian_application_repository
    ),
    profile_repository: DietitianProfileRepository = Depends(get_dietitian_profile_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> ApproveDietitianApplicationUseCase:
    return ApproveDietitianApplicationUseCase(
        application_repository, profile_repository, user_repository
    )


def get_reject_dietitian_application_use_case(
    application_repository: DietitianApplicationRepository = Depends(
        get_dietitian_application_repository
    ),
) -> RejectDietitianApplicationUseCase:
    return RejectDietitianApplicationUseCase(application_repository)


def get_mark_transaction_paid_use_case(
    transaction_repository: TransactionRepository = Depends(get_transaction_repository),
    event_publisher: TransactionEventPublisher = Depends(get_transaction_event_publisher),
) -> MarkTransactionPaidUseCase:
    return MarkTransactionPaidUseCase(transaction_repository, event_publisher)


def get_mark_transaction_unpaid_use_case(
    transaction_repository: TransactionRepository = Depends(get_transaction_repository),
) -> MarkTransactionUnpaidUseCase:
    return MarkTransactionUnpaidUseCase(transaction_repository)


def get_list_transactions_use_case(
    transaction_repository: TransactionRepository = Depends(get_transaction_repository),
) -> ListTransactionsUseCase:
    return ListTransactionsUseCase(transaction_repository)
