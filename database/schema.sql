DROP TABLE IF EXISTS matches;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS traits;
DROP TABLE IF EXISTS units;

CREATE TABLE matches (
    match_id TEXT PRIMARY KEY,
    game_creation INTEGER,
    game_datetime INTEGER,
    game_length REAL,
    game_version TEXT,
    queue_id INTEGER,
    tft_game_type TEXT,
    tft_set_core_name TEXT,
    tft_set_number INTEGER
);

CREATE TABLE players (
    match_id TEXT,
    puuid TEXT,
    riot_id_game_name TEXT,
    riot_id_tagline TEXT,
    placement INTEGER,
    level INTEGER,
    gold_left INTEGER,
    last_round INTEGER,
    players_eliminated INTEGER,
    time_eliminated REAL,
    total_damage_to_players INTEGER,
    win INTEGER
);

CREATE TABLE traits (
    match_id TEXT,
    puuid TEXT,
    trait_name TEXT,
    num_units INTEGER,
    style INTEGER,
    tier_current INTEGER,
    tier_total INTEGER
);

CREATE TABLE units (
    match_id TEXT,
    puuid TEXT,
    unit_position INTEGER,
    character_id TEXT,
    unit_name TEXT,
    rarity INTEGER,
    tier INTEGER,
    item_1 TEXT,
    item_2 TEXT,
    item_3 TEXT
);