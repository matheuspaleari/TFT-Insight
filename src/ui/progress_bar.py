"""
Componente reutilizável de barra de progresso para o terminal.
"""


class ProgressBar:
    """
    Renderiza barras de progresso em texto.
    """

    FILLED_CHAR = "█"
    EMPTY_CHAR = "░"

    @classmethod
    def render(
        cls,
        value: float,
        maximum: float = 100,
        width: int = 10,
        show_value: bool = True,
        value_suffix: str = "%"
    ) -> str:
        """
        Retorna uma barra de progresso em texto.

        Args:
            value: Valor atual.
            maximum: Valor máximo da escala.
            width: Quantidade de caracteres da barra.
            show_value: Define se o valor será exibido.
            value_suffix: Sufixo exibido depois do valor.

        Returns:
            Barra formatada.

        Exemplo:
            ███████░░░ 70%
        """

        if maximum <= 0:
            raise ValueError(
                "O valor máximo deve ser maior que zero."
            )

        if width <= 0:
            raise ValueError(
                "A largura da barra deve ser maior que zero."
            )

        normalized_value = max(
            0,
            min(float(value), float(maximum))
        )

        percentage = (
            normalized_value
            / maximum
        ) * 100

        filled_slots = round(
            (normalized_value / maximum) * width
        )

        empty_slots = width - filled_slots

        bar = (
            cls.FILLED_CHAR * filled_slots
            + cls.EMPTY_CHAR * empty_slots
        )

        if not show_value:
            return bar

        formatted_value = round(percentage)

        return (
            f"{bar} "
            f"{formatted_value}{value_suffix}"
        )