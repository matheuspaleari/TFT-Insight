-- Quantidade de partidas
SELECT COUNT(*) AS total_matches
FROM matches;


-- Quantidade de participantes
SELECT COUNT(*) AS total_players
FROM players;


-- Colocação média por jogador
SELECT
    riot_id_game_name,
    riot_id_tagline,
    ROUND(AVG(placement), 2) AS average_placement,
    COUNT(*) AS matches_played
FROM players
GROUP BY
    riot_id_game_name,
    riot_id_tagline
ORDER BY average_placement;


-- Unidades mais utilizadas
SELECT
    character_id,
    COUNT(*) AS times_used
FROM units
GROUP BY character_id
ORDER BY times_used DESC
LIMIT 20;


-- Traits mais utilizadas
SELECT
    trait_name,
    COUNT(*) AS times_used
FROM traits
WHERE style > 0
GROUP BY trait_name
ORDER BY times_used DESC
LIMIT 20;