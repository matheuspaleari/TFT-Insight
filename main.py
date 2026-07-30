from src.config import Config
from src.pipeline import run_pipeline


def main() -> None:

    Config.validate()

    run_pipeline()


if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print(error)