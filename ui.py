import os
import threading
APP_NAME = "hero_ui"

def ui_kill(): os.system("killall " + APP_NAME)

command = str()
def ui_start(state = ""):
    ui_kill()
    command = "\"" + os.path.dirname(__file__) + "/" + APP_NAME + "\" " + state
    print(command)
    os.system(command)

def ui_start_async(state = ""):
    thread = threading.Thread(target=ui_start, args=(state,))
    thread.start()
