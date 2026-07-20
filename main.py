from utils.console import use_utf8_console


def main() -> None:
    use_utf8_console()

    from ui.main_qt import run

    run()


if __name__ == "__main__":
    main()
