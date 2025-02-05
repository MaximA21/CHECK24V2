# Turnier-Basisgewichte
TOURNAMENT_WEIGHTS = {
    # Top Tier (1.5)
    "UEFA Champions League": 5,
    "Bundesliga": 1.5,
    "Premier League": 1.5,
    "LaLiga": 1.5,
    "Serie A": 1.5,
    "Ligue 1": 1.5,
    "Europameisterschaft 2024": 1.5,

    # Mid Tier (1.0)
    "UEFA Europa League": 1.0,
    "DFB Pokal": 1.0,
    "FA Cup": 1.0,
    "Copa del Rey": 1.0,
    "UEFA Super Cup": 1.0,

    # Lower Tier (0.7)
    "UEFA Conference League": 0.7,
    "2. Bundesliga": 0.7,
    "Liga Portugal": 0.7,
    "Eredivisie": 0.7,
    "Süper Lig": 0.7,

    # Base Tier (0.4)
    "3. Liga": 0.4,
    "Major League Soccer": 0.4,
    "Saudi Prof. League": 0.4,
    # TODO: add more
}

# Phasen-Multiplikatoren
PHASE_MULTIPLIERS = {
    "GROUP": 1.0,  # Gruppenphase/Normal
    "KNOCKOUT": 1.3,  # K.O.-Phase
    "SEMI": 1.5,  # Halbfinale
    "FINAL": 1.5,  # Finale
}

# Wichtigkeits-Multiplikatoren
IMPORTANCE_MULTIPLIERS = {
    "NORMAL": 1.0,  # Normales Spiel
    "DERBY": 1.3,  # Traditionelles Derby
    "TITLE": 1.4,  # Titel-relevantes Spiel
    "RELEGATION": 1.2,  # Abstiegskampf
}