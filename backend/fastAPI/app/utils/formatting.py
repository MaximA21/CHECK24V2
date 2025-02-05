from datetime import datetime


def format_date_iso(date: datetime) -> str:
    """Formatiert datetime"""
    return date.isoformat() + "Z"


def format_game_for_response(game):
    """Formatiert ein Spiel für die API Response."""
    return {
        "homeTeam": game.team_home,
        "awayTeam": game.team_away,
        "tournament": game.tournament,
        "date": format_date_iso(game.starts_at),
        "importance": float(game.total_weight)
    }


def format_package_for_response(package):
    """Formatiert ein Package für die API Response."""
    return {
        "name": package["package"]["name"],
        "activeMonths": list(package["active_months"]) if package["active_months"] else [],
        "costInEuro": package["cost"] / 100,
        "subscriptionType": package["subscription_type"],
        "gamesCovered": [format_game_for_response(g) for g in package["covered_games"]]
    }
