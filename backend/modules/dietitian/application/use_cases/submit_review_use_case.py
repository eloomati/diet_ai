from backend.modules.dietitian.application.dto.review_dto import ReviewResult, SubmitReviewCommand
from backend.modules.dietitian.application.use_cases.exceptions import DietitianNotFoundError
from backend.modules.dietitian.domain.entities.review import Review
from backend.modules.dietitian.domain.repositories.review_repository import ReviewRepository
from backend.modules.identity.domain.repositories.user_repository import UserRepository
from backend.modules.identity.domain.value_objects.role import Role


class SubmitReviewUseCase:
    def __init__(
        self,
        review_repository: ReviewRepository,
        user_repository: UserRepository,
    ) -> None:
        self._review_repository = review_repository
        self._user_repository = user_repository

    async def execute(self, command: SubmitReviewCommand) -> ReviewResult:
        dietitian = await self._user_repository.get_by_id(command.dietitian_id)
        if dietitian is None or dietitian.role != Role.DIET_USER:
            raise DietitianNotFoundError("No dietitian found for this id.")

        existing = await self._review_repository.get_by_reviewer_and_dietitian(
            command.reviewer_id, command.dietitian_id
        )
        if existing is not None:
            existing.update_content(command.rating, command.comment)
            review = existing
        else:
            # Review.create() raises SelfReviewError if reviewer_id ==
            # dietitian_id — a pure data invariant, not re-checked here.
            review = Review.create(
                reviewer_id=command.reviewer_id,
                dietitian_id=command.dietitian_id,
                rating=command.rating,
                comment=command.comment,
            )

        await self._review_repository.save(review)
        return ReviewResult.from_domain(review)
