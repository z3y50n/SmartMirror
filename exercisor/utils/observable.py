from utils.log import logger

class Observable(object):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._observers = []

    def attach(self, observer) -> None:
        self._observers.append(observer)

    def detach(self, observer) -> None:
        self._observers.remove(observer)

    def notify(self, *args, **kwargs) -> None:
        for observer in self._observers:
            try:
                observer.update(self, *args, **kwargs)
            except Exception as e:
                logger.debug(f'Error: {e}')