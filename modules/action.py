class Action:
    def __init__(self, gui) -> None:
        self._gui = gui
        self._commands = {"main": self._extract_functions()}

        print(dir(self._gui))
        screen = self._screen_widgets()
        self._commands.update(self._extract_functions(screen))

    def _get_screen(self):
        return self._gui.root.current

    def _extract_functions(self, screen=[]):
        """Extract functions of main app and given screen"""
        if screen:
            functions = {widget.name: [method_name for method_name in dir(widget)
                                       if not method_name.startswith("_") and callable(getattr(widget, method_name))]
                         for widget in screen if hasattr(widget, "name")}
        else:
            functions = [method_name for method_name in dir(self._gui)
                         if not method_name.startswith("_") and callable(getattr(self._gui, method_name))]
        return functions

    def _screen_widgets(self):
        widgets = [widget for widget in self._gui.root.walk()]
        return widgets

    def perform(self, intents, entities):
        pass
