from typing import Optional
from ..utils.constants import TOP_LEAGUES, LEAGUE_TIERS
from ..core.database import Database
import re

async def get_team_tournaments(db: Database, teams: list[str]) -> set[str]:
    """Hole alle Turniere für die ausgewählten Teams."""
    query = """
    SELECT ARRAY_AGG(DISTINCT tournament_name) as tournaments
    FROM game 
    WHERE team_home = ANY(:teams) OR team_away = ANY(:teams)
    """
    result = await db.execute(query, {"teams": teams})
    return set(result[0]["tournaments"]) if result and result[0]["tournaments"] else set()


async def get_main_league(db: Database, teams: list[str]) -> Optional[str]:
    """Bestimme die Main Liga"""
    if not teams:
        return None

    tournaments = await get_team_tournaments(db, teams)

    tournament_groups = {}
    for tournament in tournaments:
        base_name = re.sub(r'\s+\d{2,4}/\d{2,4}$', '', tournament)
        if base_name not in tournament_groups:
            tournament_groups[base_name] = []
        tournament_groups[base_name].append(tournament)

    # Erst Top-5 Ligen prüfen
    for base_name in TOP_LEAGUES:
        if base_name in tournament_groups:
            # Nimm neueste Saison dieses Turniers
            return max(tournament_groups[base_name])

    # Sonst Liga mit höchstem Tier
    max_base_name = max(
        tournament_groups.keys(),
        key=lambda t: LEAGUE_TIERS.get(t, 1),
        default=None
    )

    if max_base_name:
        return max(tournament_groups[max_base_name])