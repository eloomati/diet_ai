from backend.modules.dietitian.domain.entities.dietitian_profile import DietitianProfile
from backend.modules.identity.domain.entities.user import User


def resolve_dietitian_name(profile: DietitianProfile, user: User) -> str:
    """A dietitian's public-facing name, in priority order: their real
    first + last name (only when *both* are set — filling them in is
    itself the dietitian's choice to show a real name instead of a
    generic one), then the same two-step fallback every user gets
    (`display_name`, then `email`)."""
    if profile.first_name and profile.last_name:
        return f"{profile.first_name} {profile.last_name}"
    return user.resolved_display_name
