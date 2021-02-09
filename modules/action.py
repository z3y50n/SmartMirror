class Action:
    _commands = {}
    _current_screen = None
    
    def __init__(self, gui) -> None:
        self._gui = gui
        self._update_commands()

    def _update_commands(self):
        """update available commands and current screen"""
        self._commands = {}
        self._current_screen = self._get_screen(self._gui.root.current)

        widgets = self._extract_widgets(self._current_screen)
        widgets.append(self._gui)
        
        self._commands = self._extract_functions(widgets)

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
        widgets = [widget for widget in screen.walk() if hasattr(widget, "subscribe")]
        return widgets

    def _extract_functions(self, widgets: list = []):
        """Extract subscribed functions from a list of widgets"""
        functions = {}
        for widget in widgets:
            if hasattr(widget, "subscribe"):
                functions.update(widget.subscribe())
        return functions

    def perform(self, resp):
        """Perform action as specified by wit bot"""
        try:
            if resp['intent'] in self._commands:
                res = self._commands[resp['intent']](**resp['args'])
                if "config" in res:
                    self._config_change(res)
            else:
                print("Not available command")
        except:
            print("Something went wrong while trying to perform action")

    def _config_change(self, conf):
        self._gui.config.set(*conf[1:])
        self._gui.config.write()
        self._gui.on_config_change(self._gui.config, *conf[1:])

    # def _extract_functions(self, widgets: list = []):
    #     """Extract functions of main app and given screen"""
    #     functions = {widget.name: [method_name for method_name in dir(widget)
    #                                if not method_name.startswith("_") and callable(getattr(widget, method_name))]
    #                  for widget in widgets if hasattr(widget, "name")}
    #     return functions

    # def _get_widget(self, screen, name):
    #     """Get actual widget object from a given name"""
    #     for widget in screen.walk():
    #         if hasattr(widget, "name"):
    #             if widget.name == name:
    #                 return widget
    #     return

    # def perform(self, resp):
    #     """Perform action as specified by wit bot"""
    #     widget = self._gui
    #     if resp['widget'] in self._commands and resp['function'] in self._commands[resp['widget']]:
    #         widget = self._get_widget(self._current_screen, resp['widget'])
    #     try:
    #         # call function
    #         resp = getattr(widget, resp['function'])(**resp['args'])
    #         if "config" in resp:
    #             self._config_change(resp)
    #     except:
    #         print("Something went wrong when calling the function")
    








