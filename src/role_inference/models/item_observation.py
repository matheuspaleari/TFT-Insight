from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ItemObservation:
    item_id: str

    frontline_uses: int = 0
    backline_uses: int = 0

    damage_carry_uses: int = 0
    tank_uses: int = 0
    support_uses: int = 0

    def __post_init__(self) -> None:
        if not self.item_id.strip():
            raise ValueError(
                "ItemObservation.item_id não pode ser vazio."
            )

        for field_name, value in (
            ("frontline_uses", self.frontline_uses),
            ("backline_uses", self.backline_uses),
            (
                "damage_carry_uses",
                self.damage_carry_uses,
            ),
            ("tank_uses", self.tank_uses),
            ("support_uses", self.support_uses),
        ):
            if value < 0:
                raise ValueError(
                    f"{field_name} não pode ser negativo."
                )

    @property
    def positional_uses(self) -> int:
        """
        Quantidade observada com informação de posição.
        """

        return (
            self.frontline_uses
            + self.backline_uses
        )

    @property
    def role_uses(self) -> int:
        """
        Quantidade observada com papel inferido.
        """

        return (
            self.damage_carry_uses
            + self.tank_uses
            + self.support_uses
        )

    @property
    def total_uses(self) -> int:
        """
        Melhor estimativa disponível da amostra do item.

        Posição e papel podem representar a mesma ocorrência. Por isso,
        usamos o maior total em vez de somá-los e duplicar observações.
        """

        return max(
            self.positional_uses,
            self.role_uses,
        )
