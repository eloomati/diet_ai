from uuid import UUID, uuid4

import pytest

from backend.modules.ai.tests.fakes import FakeLLMProvider
from backend.modules.nutrition.application import (
    CreateNutritionProfileCommand,
    CreateNutritionProfileUseCase,
    DietPlanExportNotFoundError,
    DietPlanNotFoundError,
    DownloadDietPlanExportQuery,
    DownloadDietPlanExportUseCase,
    ExportDietPlanCommand,
    ExportDietPlanUseCase,
    GenerateDietPlanCommand,
    GenerateDietPlanUseCase,
    ListDietPlanExportsQuery,
    ListDietPlanExportsUseCase,
)
from backend.modules.nutrition.tests.fakes import (
    FakeSftpClient,
    InMemoryDietPlanExportRepository,
    InMemoryDietPlanRepository,
    InMemoryNutritionProfileRepository,
)


def _plan_dict(duration_days: int = 1) -> dict:
    return {
        "days": [
            {
                "day_number": day,
                "meals": [
                    {"name": "Oatmeal", "calories": 400, "protein": 20, "carbohydrates": 60, "fat": 10}
                ],
            }
            for day in range(1, duration_days + 1)
        ]
    }


async def _generate_plan(plan_repo, profile_repo, user_id):
    await CreateNutritionProfileUseCase(profile_repo).execute(
        CreateNutritionProfileCommand(
            user_id=user_id,
            age=29,
            height_cm=187,
            weight_kg=80,
            activity_level="HIGH",
            goal="MUSCLE_GAIN",
            diet_type="VEGETARIAN",
        )
    )
    llm = FakeLLMProvider(canned_structured_response=_plan_dict())
    return await GenerateDietPlanUseCase(plan_repo, profile_repo, llm).execute(
        GenerateDietPlanCommand(user_id=user_id, duration_days=1)
    )


@pytest.mark.asyncio
async def test_export_diet_plan_uploads_and_records_metadata() -> None:
    plan_repo = InMemoryDietPlanRepository()
    export_repo = InMemoryDietPlanExportRepository()
    sftp = FakeSftpClient()
    user_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_id)

    result = await ExportDietPlanUseCase(plan_repo, export_repo, sftp).execute(
        ExportDietPlanCommand(user_id=user_id, plan_id=UUID(created.plan_id))
    )

    assert result.diet_plan_id == created.plan_id
    assert result.filename in sftp.files
    assert b"Oatmeal" in sftp.files[result.filename]


@pytest.mark.asyncio
async def test_export_diet_plan_raises_for_unknown_plan() -> None:
    plan_repo = InMemoryDietPlanRepository()
    export_repo = InMemoryDietPlanExportRepository()
    sftp = FakeSftpClient()

    with pytest.raises(DietPlanNotFoundError):
        await ExportDietPlanUseCase(plan_repo, export_repo, sftp).execute(
            ExportDietPlanCommand(user_id=uuid4(), plan_id=uuid4())
        )


@pytest.mark.asyncio
async def test_export_diet_plan_raises_for_non_owner() -> None:
    plan_repo = InMemoryDietPlanRepository()
    export_repo = InMemoryDietPlanExportRepository()
    sftp = FakeSftpClient()
    owner_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), owner_id)

    with pytest.raises(DietPlanNotFoundError):
        await ExportDietPlanUseCase(plan_repo, export_repo, sftp).execute(
            ExportDietPlanCommand(user_id=uuid4(), plan_id=UUID(created.plan_id))
        )


@pytest.mark.asyncio
async def test_exporting_twice_creates_two_distinct_archived_files() -> None:
    plan_repo = InMemoryDietPlanRepository()
    export_repo = InMemoryDietPlanExportRepository()
    sftp = FakeSftpClient()
    user_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_id)
    use_case = ExportDietPlanUseCase(plan_repo, export_repo, sftp)

    first = await use_case.execute(ExportDietPlanCommand(user_id=user_id, plan_id=UUID(created.plan_id)))
    second = await use_case.execute(ExportDietPlanCommand(user_id=user_id, plan_id=UUID(created.plan_id)))

    assert first.export_id != second.export_id
    assert first.filename != second.filename
    assert len(sftp.files) == 2


@pytest.mark.asyncio
async def test_list_diet_plan_exports_returns_newest_first() -> None:
    plan_repo = InMemoryDietPlanRepository()
    export_repo = InMemoryDietPlanExportRepository()
    sftp = FakeSftpClient()
    user_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_id)
    export_use_case = ExportDietPlanUseCase(plan_repo, export_repo, sftp)
    first = await export_use_case.execute(
        ExportDietPlanCommand(user_id=user_id, plan_id=UUID(created.plan_id))
    )
    second = await export_use_case.execute(
        ExportDietPlanCommand(user_id=user_id, plan_id=UUID(created.plan_id))
    )

    results = await ListDietPlanExportsUseCase(plan_repo, export_repo).execute(
        ListDietPlanExportsQuery(user_id=user_id, plan_id=UUID(created.plan_id))
    )

    assert [r.export_id for r in results] == [second.export_id, first.export_id]


@pytest.mark.asyncio
async def test_list_diet_plan_exports_raises_for_non_owner() -> None:
    plan_repo = InMemoryDietPlanRepository()
    export_repo = InMemoryDietPlanExportRepository()
    owner_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), owner_id)

    with pytest.raises(DietPlanNotFoundError):
        await ListDietPlanExportsUseCase(plan_repo, export_repo).execute(
            ListDietPlanExportsQuery(user_id=uuid4(), plan_id=UUID(created.plan_id))
        )


@pytest.mark.asyncio
async def test_download_diet_plan_export_returns_the_uploaded_content() -> None:
    plan_repo = InMemoryDietPlanRepository()
    export_repo = InMemoryDietPlanExportRepository()
    sftp = FakeSftpClient()
    user_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), user_id)
    exported = await ExportDietPlanUseCase(plan_repo, export_repo, sftp).execute(
        ExportDietPlanCommand(user_id=user_id, plan_id=UUID(created.plan_id))
    )

    downloaded = await DownloadDietPlanExportUseCase(export_repo, sftp).execute(
        DownloadDietPlanExportQuery(
            user_id=user_id, plan_id=UUID(created.plan_id), export_id=UUID(exported.export_id)
        )
    )

    assert downloaded.filename == exported.filename
    assert b"Oatmeal" in downloaded.content


@pytest.mark.asyncio
async def test_download_diet_plan_export_raises_for_unknown_export() -> None:
    export_repo = InMemoryDietPlanExportRepository()
    sftp = FakeSftpClient()

    with pytest.raises(DietPlanExportNotFoundError):
        await DownloadDietPlanExportUseCase(export_repo, sftp).execute(
            DownloadDietPlanExportQuery(user_id=uuid4(), plan_id=uuid4(), export_id=uuid4())
        )


@pytest.mark.asyncio
async def test_download_diet_plan_export_raises_for_non_owner() -> None:
    plan_repo = InMemoryDietPlanRepository()
    export_repo = InMemoryDietPlanExportRepository()
    sftp = FakeSftpClient()
    owner_id = uuid4()
    created = await _generate_plan(plan_repo, InMemoryNutritionProfileRepository(), owner_id)
    exported = await ExportDietPlanUseCase(plan_repo, export_repo, sftp).execute(
        ExportDietPlanCommand(user_id=owner_id, plan_id=UUID(created.plan_id))
    )

    with pytest.raises(DietPlanExportNotFoundError):
        await DownloadDietPlanExportUseCase(export_repo, sftp).execute(
            DownloadDietPlanExportQuery(
                user_id=uuid4(), plan_id=UUID(created.plan_id), export_id=UUID(exported.export_id)
            )
        )
