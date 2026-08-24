from enum import Enum


class RecommendationCategory(str, Enum):
    CONTEST = "Contestação"
    ITEMIZATION = "Itemização"
    ECONOMY = "Economia"
    TEMPO = "Tempo"
    FLEX = "Flexibilidade"
    COMPOSITION = "Composição"
    PLAYSTYLE = "Estilo de jogo"
