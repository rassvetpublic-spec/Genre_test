from __future__ import annotations


def main() -> None:
    from . import check_gui
    from .build_check_gui import BuildAwareCheckTab
    from .build_history import install_validation_build_awareness
    from .validation_display import install_validation_display_labels

    check_gui.CheckTab = BuildAwareCheckTab
    install_validation_build_awareness()
    install_validation_display_labels()

    from .themed_gui import main as themed_main

    themed_main()


if __name__ == "__main__":
    main()
