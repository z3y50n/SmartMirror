from modules import speech


class Interface:
    def start(self):
        s = speech.Speech("mirror mirror on the wall", "thank you mirror")
        while True:
            while not s.check_launch_phrase():
                s.speak()
            print("You gained access")
            while not s.check_close_phrase():
                s.speak()
                print("decide action")


if __name__ == "__main__":
    interface = Interface()
    interface.start()
