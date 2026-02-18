class SettingsController:
    def __init__(self, view):
        self.view = view
    
    def quit(self):
        print("quit")

    def go(self):
        print("go")

    def home(self):
        print("home")

    def stop(self):
        print("stop")
    
    def z_move_up(self):
        print("Move Z up")

    def z_move_down(self):
        print("Move Z down")
    
    def take_picture(self):
        print("take picture")