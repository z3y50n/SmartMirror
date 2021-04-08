from modules import speech

class Action:
    _commands = {}
    _current_screen = None
    
    def __init__(self, gui) -> None:
        self._gui = gui
        self._update_commands()
        self._s = speech.Speech()

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
                if res is not None:
                    if "config" in res:
                        self._config_change(res[1:])
                    elif "update" in res:
                        print(res)
                        self._update_commands()
                    elif "speech" in res:
                        self._s.speak_back(res[1])
            else:
                print("Not available command")
        except Exception as e:
            print(e)
            print("Something went wrong while trying to perform action")

    def _config_change(self, conf):
        self._gui.config.set(*conf)
        self._gui.config.write()
        self._gui.on_config_change(self._gui.config, *conf)

    