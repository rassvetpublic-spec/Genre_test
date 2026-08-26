from __future__ import annotations


def main() -> None:
    from . import check_gui
    from .build_check_gui import BuildAwareCheckTab
    from .build_history import install_validation_build_awareness
    from .resource_monitor_install import install_resource_monitor_button
    from .validation_display import install_validation_display_labels

    check_gui.CheckTab = BuildAwareCheckTab
    install_validation_build_awareness()
    install_validation_display_labels()

    from . import themed_gui

    original_install_switch = themed_gui.ThemeController._install_switch

    def install_switch_with_resource_monitor(controller) -> None:
        original_install_switch(controller)
        install_resource_monitor_button(controller.root)

    themed_gui.ThemeController._install_switch = install_switch_with_resource_monitor
    try:
        themed_gui.main()
    finally:
        themed_gui.ThemeController._install_switch = original_install_switch


if __name__ == "__main__":
    main()
