from tft_insight import (
    AuthenticationError,
    PlayerNotFoundError,
    RateLimitError,
    TFTInsightAPIError,
    TFTInsightClient,
    TransportError,
)


def main() -> None:
    try:
        with TFTInsightClient(
            api_key="partner-key",
        ) as client:
            client.analyze_player(
                game_name="Jogador",
                tag_line="TAG",
            )

    except AuthenticationError:
        print("Chave inválida.")

    except PlayerNotFoundError:
        print("Jogador não encontrado.")

    except RateLimitError:
        print("Limite atingido.")

    except TransportError:
        print("API indisponível.")

    except TFTInsightAPIError as error:
        print(
            f"Erro {error.status_code}: {error}"
        )


if __name__ == "__main__":
    main()
