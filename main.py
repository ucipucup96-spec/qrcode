from app.seed import ensure_seed_data
from app.ui import launch_app


def main() -> None:
    ensure_seed_data()
    launch_app()


if __name__ == "__main__":
    main()
