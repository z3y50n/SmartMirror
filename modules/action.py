class Action:
    _commands = {}
    _current_screen = None
    
    def __init__(self, gui) -> None:
        self._gui = gui
        self._update_commands()
        print(self._commands)

    def _update_commands(self):
        """update available commands and current screen"""
        self._commands = self._extract_functions([self._gui])
        self._current_screen = self._get_screen(self._gui.root.current)
        widgets = self._extract_widgets(self._current_screen)
        functions = self._extract_functions(widgets)
        self._commands.update(functions)

    def _get_screen(self, name):
        """Get actuall screen object from a given name"""
        for screen in self._gui.root.screens:
            if screen.name == name:
                return screen
        return None

    def _extract_widgets(self, screen):
        """Extract widgets of the current screen"""
        if not hasattr(screen, "walk"):
            return
        widgets = [widget for widget in screen.walk()]
        return widgets[1:]

    def _extract_functions(self, widgets: list = []):
        """Extract functions of main app and given screen"""
        functions = {widget.name: [method_name for method_name in dir(widget)
                                   if not method_name.startswith("_") and callable(getattr(widget, method_name))]
                     for widget in widgets if hasattr(widget, "name")}
        return functions

    def _get_widget(self, screen, name):
        """Get actual widget object from a given name"""
        for widget in screen.walk():
            if hasattr(widget, "name"):
                if widget.name == name:
                    return widget
        return

    def perform(self, resp):
        """Perform action as specified by wit bot"""
        if (resp['widget'] == 'smartmirror'):
            getattr(self._gui, resp['function'])(**resp['args'])
        
        elif resp['widget'] in self._commands and resp['function'] in self._commands[resp['widget']]:
            widget = self._get_widget(self._current_screen, resp['widget'])
            # call function
            getattr(widget, resp['function'])(**resp['args'])
