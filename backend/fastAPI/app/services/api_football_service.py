from datetime import datetime, timezone
import json
from typing import Optional, Tuple, Dict, Any
import redis
import aiohttp
from ..core.config import settings
from ..utils.constants import LEAGUE_IDS
import re


class APIFootballService:
    def __init__(self):
        self.headers = settings.API_FOOTBALL_HEADERS
        self.base_url = settings.API_FOOTBALL_URL

        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.cache_ttl = settings.REDIS_TTL

    @staticmethod
    def _get_league_id(tournament: str) -> Optional[int]:
        """Konvertiert Turniernamen zu API-Football League ID."""
        # Entferne Saison-Pattern (z.B. 24/25 oder 2023/2024)
        base_name = re.sub(r'\s+\d{2,4}/\d{2,4}$', '', tournament)

        return LEAGUE_IDS.get(base_name)

    @staticmethod
    def _get_season(date: datetime) -> int:
        """Ermittelt die Saison basierend auf dem Datum."""
        return date.year if date.month > 6 else date.year - 1

    async def _fetch_from_api(self, tournament: str, game_date: datetime) -> Dict[str, Any]:
        """Holt Rohdaten von der API."""
        league_id = self._get_league_id(tournament)
        if not league_id:
            raise ValueError(f"Unbekanntes Turnier: {tournament}")

        season = self._get_season(game_date)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                        f"{self.base_url}/fixtures",
                        headers=self.headers,
                        params={
                            "league": league_id,
                            "season": season,
                        }
                ) as response:
                    if response.status != 200:
                        raise Exception(f"API Error: {response.status}")
                    return await response.json()
        except Exception as e:
            raise Exception(f"API Request fehlgeschlagen: {str(e)}")

    async def get_game_phase(self, tournament: str, game_date: datetime) -> str:
        """
        Ermittelt die Phase eines Spiels.
        Returns: 'GROUP', 'KNOCKOUT', 'SEMI', 'FINAL'
        """
        # Cache-Key für die komplette Saison
        season = self._get_season(game_date)
        cache_key = f"phases:{tournament}:{season}"

        # Versuche Phasen-Map aus Cache zu lesen
        cached_phases = self.redis.get(cache_key)
        if cached_phases:
            phases_map = json.loads(cached_phases)
            date_str = game_date.strftime('%Y-%m-%d')
            return phases_map.get(date_str, "GROUP")

        # Hole ALLE Spiele der Saison
        data = await self._fetch_from_api(tournament, game_date)

        # Erstelle Map von Datum → Phase für alle Spiele
        phases_map = {}
        for match in data["response"]:
            match_date = datetime.fromisoformat(match["fixture"]["date"]).strftime('%Y-%m-%d')
            round_info = match["league"]["round"].upper()

            if "FINAL" in round_info:
                phase = "FINAL"
            elif "SEMI" in round_info:
                phase = "SEMI"
            elif any(x in round_info for x in
                     ["1/4", "1/8", "1/16", "QUARTER", "LAST 16"]):  # TODO: research and rework actual names
                phase = "KNOCKOUT"
            else:
                phase = "GROUP"

            phases_map[match_date] = phase

        # Cache die komplette Map
        self.redis.setex(cache_key, self.cache_ttl, json.dumps(phases_map))

        return phases_map.get(game_date.strftime('%Y-%m-%d'), "GROUP")

    async def get_table_positions(self, tournament: str, team: str, game_date: datetime) -> Tuple[int, int]:
        """
        Ermittelt die Position eines Teams in der Tabelle.
        Returns: (position, total_teams)
        """
        # Stelle sicher, dass game_date timezone-aware ist
        if game_date.tzinfo is None:
            game_date = game_date.replace(tzinfo=timezone.utc)

        try:
            # Cache-Key für die komplette Saison
            season = self._get_season(game_date)
            cache_key = f"tables:{tournament}:{season}"
            print(f"Checking cache for key: {cache_key}")

            # Versuche alle Tabellen der Saison aus Cache zu lesen
            cached_tables = self.redis.get(cache_key)

            print(f"Cache result: {cached_tables is not None}")

            if cached_tables:
                tables_map = json.loads(cached_tables)
                date_str = game_date.strftime('%Y-%m-%d')
                print(f"Looking for date: {date_str}")
                print(f"Available dates: {sorted(tables_map.keys())}")
                # Suche nächstgelegenes Datum in der Vergangenheit
                available_dates = sorted(tables_map.keys())

                # Finde letzte Tabelle vor unserem Datum
                closest_date = None
                for table_date in available_dates:
                    if table_date <= date_str:
                        closest_date = table_date
                    else:
                        break
                # Wenn keine frühere Tabelle gefunden, nimm die erste
                if not closest_date and available_dates:
                    closest_date = available_dates[0]

                if closest_date:
                    table = tables_map[closest_date]
                    if team in table:
                        return table[team]["position"], len(table)

            print("Cache miss, fetching from API...")

            # Wenn nicht im Cache, hole ALLE Spiele der Saison
            data = await self._fetch_from_api(tournament, game_date)

            # Erstelle Map von Datum → Tabelle für alle Spieltage
            tables_map = {}

            # Sortiere Spiele nach Datum
            sorted_matches = sorted(
                data["response"],
                key=lambda x: datetime.fromisoformat(x["fixture"]["date"])
            )

            # Für jedes Spiel aktualisieren wir die Tabelle
            for match in sorted_matches:
                match_date = datetime.fromisoformat(match["fixture"]["date"])
                if match_date > game_date:
                    continue  # Ignoriere Spiele nach unserem Anfragedatum

                date_str = match_date.strftime('%Y-%m-%d')

                # Hole letzte Tabelle als Basis oder starte neu
                last_table = tables_map.get(
                    max(tables_map.keys()) if tables_map else None,
                    {}
                )

                if last_table:
                    current_table = last_table.copy()
                else:
                    current_table = {}

                # Update Tabelle mit neuem Spiel
                home_team = match["teams"]["home"]["name"]
                away_team = match["teams"]["away"]["name"]
                home_goals = match["goals"]["home"]
                away_goals = match["goals"]["away"]

                # Überspringe Spiele ohne Ergebnis
                if home_goals is None or away_goals is None:
                    continue

                # Initialisiere Teams falls nötig
                for team_name in [home_team, away_team]:
                    if team_name not in current_table:
                        current_table[team_name] = {
                            "points": 0,
                            "goals_for": 0,
                            "goals_against": 0,
                            "matches_played": 0
                        }

                # Update Statistiken
                current_table[home_team]["matches_played"] += 1
                current_table[away_team]["matches_played"] += 1

                if home_goals > away_goals:
                    current_table[home_team]["points"] += 3
                elif away_goals > home_goals:
                    current_table[away_team]["points"] += 3
                else:
                    current_table[home_team]["points"] += 1
                    current_table[away_team]["points"] += 1

                current_table[home_team]["goals_for"] += home_goals
                current_table[home_team]["goals_against"] += away_goals
                current_table[away_team]["goals_for"] += away_goals
                current_table[away_team]["goals_against"] += home_goals

                # Berechne Positionen
                sorted_teams = sorted(
                    current_table.items(),
                    key=lambda x: (
                        x[1]["points"],
                        x[1]["goals_for"] - x[1]["goals_against"],
                        x[1]["goals_for"]
                    ),
                    reverse=True
                )

                # Füge Positionen hinzu
                final_table = {}
                for position, (team_name, stats) in enumerate(sorted_teams, 1):
                    final_table[team_name] = {
                        **stats,  # Kopiert alle Werte aus Stats
                        "position": position
                    }
                print(final_table)

                tables_map[date_str] = final_table

            # Cache die komplette Map
            self.redis.setex(cache_key, self.cache_ttl, json.dumps(tables_map))

            # Formatiere Anfragedatum
            search_date = game_date.strftime('%Y-%m-%d')

            # Hole und sortiere alle verfügbaren Daten
            available_dates = sorted(tables_map.keys())

            # Finde das letzte Datum vor unserem Anfragedatum
            closest_date = None
            for date in available_dates:
                if date <= search_date:
                    closest_date = date
                else:
                    break

            # Wenn kein passendes Datum gefunden, nimm das erste verfügbare
            if not closest_date and available_dates:
                closest_date = available_dates[0]

            # Hole Position, wenn möglich
            if closest_date:
                table = tables_map[closest_date]
                if team in table:
                    return table[team]["position"], len(table)
                return len(table), len(table)  # Team nicht in Tabelle = letzter Platz

        except Exception as e:
            print(f"Fehler beim Abrufen der Tabellenposition: {str(e)}")
            return 0, 0  # Fallback bei Fehler
