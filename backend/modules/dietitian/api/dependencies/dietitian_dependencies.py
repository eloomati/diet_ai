from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.dietitian.application.use_cases.get_my_dietitian_application_use_case import (
    GetMyDietitianApplicationUseCase,
)
from backend.modules.dietitian.application.use_cases.submit_dietitian_application_use_case import (
    SubmitDietitianApplicationUseCase,
)
from backend.modules.dietitian.domain.repositories.dietitian_application_repository import (
    DietitianApplicationRepository,
)
from backend.modules.dietitian.infrastructure.persistence.repository.sqlalchemy_dietitian_application_repository import (
    SqlAlchemyDietitianApplicationRepository,
)
from backend.shared.database import get_db_session


def get_dietitian_application_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DietitianApplicationRepository:
    return SqlAlchemyDietitianApplicationRepository(session)


def get_submit_dietitian_application_use_case(
    repository: DietitianApplicationRepository = Depends(get_dietitian_application_repository),
) -> SubmitDietitianApplicationUseCase:
    return SubmitDietitianApplicationUseCase(repository)


def get_my_dietitian_application_use_case(
    repository: DietitianApplicationRepository = Depends(get_dietitian_application_repository),
) -> GetMyDietitianApplicationUseCase:
    return GetMyDietitianApplicationUseCase(repository)
