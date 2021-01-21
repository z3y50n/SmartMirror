class Action:
    def __init__(self, gui) -> None:
        self._gui = gui
        self._commands = self._extract_functions([self._gui])

    def get_screen(self, name):
        for screen in self._gui.root.screens:
            if screen.name == name:
                return screen
        return None

    def _extract_functions(self, widgets: list = []):
        """Extract functions of main app and given screen"""
        functions = {widget.name: [method_name for method_name in dir(widget)
                                   if not method_name.startswith("_") and callable(getattr(widget, method_name))]
                     for widget in widgets if hasattr(widget, "name")}
        return functions

    def _extract_widgets(self, screen):
        """Extract widgets of the current screen"""
        if not hasattr(screen, "walk"):
            return
        widgets = [widget for widget in screen.walk()]
        return widgets[1:]

    def perform(self, intents, entities):
        pass
