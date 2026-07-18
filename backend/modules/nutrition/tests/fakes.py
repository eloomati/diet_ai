from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from backend.modules.nutrition.domain import DietPlan, DietPlanExport, NutritionProfile


class InMemoryNutritionProfileRepository:
    def __init__(self) -> None:
        self._by_user_id: dict[UUID, NutritionProfile] = {}

    async def get_by_user_id(self, user_id: UUID) -> NutritionProfile | None:
        return self._by_user_id.get(user_id)

    async def save(self, profile: NutritionProfile) -> None:
        self._by_user_id[profile.user_id] = profile


class InMemoryDietPlanRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, DietPlan] = {}

    async def get_by_id(self, plan_id: UUID) -> DietPlan | None:
        return self._by_id.get(plan_id)

    async def list_by_user_id(
        self,
        user_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[DietPlan]:
        plans = [plan for plan in self._by_id.values() if plan.user_id == user_id]
        if start_date is not None:
            lower = datetime.combine(start_date, time.min, tzinfo=UTC)
            plans = [plan for plan in plans if plan.created_at >= lower]
        if end_date is not None:
            upper = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
            plans = [plan for plan in plans if plan.created_at < upper]
        return sorted(plans, key=lambda plan: plan.created_at, reverse=True)

    async def save(self, plan: DietPlan) -> None:
        self._by_id[plan.id] = plan


class InMemoryDietPlanExportRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUID, DietPlanExport] = {}

    async def save(self, export: DietPlanExport) -> None:
        self._by_id[export.id] = export

    async def get_by_id(self, export_id: UUID) -> DietPlanExport | None:
        return self._by_id.get(export_id)

    async def list_by_diet_plan_id(self, diet_plan_id: UUID) -> list[DietPlanExport]:
        exports = [e for e in self._by_id.values() if e.diet_plan_id == diet_plan_id]
        return sorted(exports, key=lambda e: e.created_at, reverse=True)


class FakeSftpClient:
    """Shared in-memory store, unlike infrastructure/sftp/MockSftpClient (which is
    constructed fresh per request and so can't back the "download it later" flow) —
    use a single instance across an export and a later download within a test."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}

    async def upload(self, remote_filename: str, content: bytes) -> None:
        self.files[remote_filename] = content

    async def download(self, remote_filename: str) -> bytes:
        if remote_filename not in self.files:
            raise FileNotFoundError(remote_filename)
        return self.files[remote_filename]
