from utils.console import use_utf8_console


def main() -> None:
    # Console phai doi sang UTF-8 TRUOC khi lap dat logging, neu khong
    # thong diep tieng Viet se hong tren Terminal Windows.
    use_utf8_console()

    from ui.main_qt import run

    run()


if __name__ == "__main__":
    main()
