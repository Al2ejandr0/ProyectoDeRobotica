import sys
import threading
from ctypes import *
from sdl3 import *
from OpenGL.GL import *
from PIL import Image
import os
import cv2
from VISION import DetectorRostro

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600

class HeroUI:
    def __init__(self):
        self.running = True
        self.window = None
        self.gl_context = None
        self.font = None
        self.robot_data = {
            "x": 0.0, "y": 0.0, "theta": 0.0,
            "battery": 100, "status": "Iniciando..."
        }
        self.data_lock = threading.Lock()
        self.active_buttons = {}
        self.current_page = "HOME"

        self.cap = cv2.VideoCapture(0)
        self.detector = DetectorRostro()
        self.faces_detected = None
        self.gesture_detected = None
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1024)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        self.rendercam = False
        self.camframe_x = 200
        self.camframe_y = 64
        self.cam_texture = None

        self.bot_texture = None
        self.bot_w = 0
        self.bot_h = 0

        self.backbtn_texture = None
        self.backbtn_w = 0
        self.backbtn_h = 0

    def load_texture(self, path = str()):
        try:
            img = Image.open(path).convert("RGBA")
            img_data = img.tobytes("raw", "RGBA", 0, -1)
            texture_id = GLuint()
            glGenTextures(1, byref(texture_id))
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
            return texture_id, img.width, img.height
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return None, 0, 0

    def render_texture(self, texture_id, x, y, w, h):
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        x_start = (x / SCREEN_WIDTH) * 2.0 - 1.0
        y_start = 1.0 - (y / SCREEN_HEIGHT) * 2.0
        x_end = ((x + w) / SCREEN_WIDTH) * 2.0 - 1.0
        y_end = 1.0 - ((y + h) / SCREEN_HEIGHT) * 2.0
        glTexCoord2f(0.0, 1.0); glVertex2f(x_start, y_start)
        glTexCoord2f(1.0, 1.0); glVertex2f(x_end, y_start)
        glTexCoord2f(1.0, 0.0); glVertex2f(x_end, y_end)
        glTexCoord2f(0.0, 0.0); glVertex2f(x_start, y_end)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def render_text_to_opengl(self, text, x, y, color):
        if not self.font:
            return

        text_bytes = text.encode('utf-8')
        text_surface = TTF_RenderText_Blended(self.font, text_bytes, len(text_bytes), color)
        if not text_surface:
            return

        surf = text_surface.contents
        
        texture_id = GLuint()
        glGenTextures(1, byref(texture_id))
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, surf.pitch // 4) 
        
        pixels_pointer = cast(surf.pixels, c_void_p)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surf.w, surf.h, 0, GL_BGRA, GL_UNSIGNED_BYTE, pixels_pointer)

        glPixelStorei(GL_UNPACK_ROW_LENGTH, 0)

        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        
        x_start = (x / SCREEN_WIDTH) * 2.0 - 1.0
        y_start = 1.0 - (y / SCREEN_HEIGHT) * 2.0
        x_end = ((x + surf.w) / SCREEN_WIDTH) * 2.0 - 1.0
        y_end = 1.0 - ((y + surf.h) / SCREEN_HEIGHT) * 2.0

        glTexCoord2f(0.0, 0.0); glVertex2f(x_start, y_start)
        glTexCoord2f(1.0, 0.0); glVertex2f(x_end, y_start)
        glTexCoord2f(1.0, 1.0); glVertex2f(x_end, y_end)
        glTexCoord2f(0.0, 1.0); glVertex2f(x_start, y_end)
        
        glEnd()
        glDisable(GL_TEXTURE_2D)

        glDeleteTextures(1, byref(texture_id))
        SDL_DestroySurface(text_surface)

    def render_button(self, button_id, text, x, y, w, h, bg_color, text_color):
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)
        
        is_pressed = self.active_buttons.get(button_id, False)
        
        if is_pressed:
            r = max(0.0, (bg_color.r * 0.6) / 255.0)
            g = max(0.0, (bg_color.g * 0.6) / 255.0)
            b = max(0.0, (bg_color.b * 0.6) / 255.0)
            a = bg_color.a / 255.0
        else:
            r = bg_color.r / 255.0
            g = bg_color.g / 255.0
            b = bg_color.b / 255.0
            a = bg_color.a / 255.0

        glColor4f(r, g, b, a)
        
        x_start = (x / SCREEN_WIDTH) * 2.0 - 1.0
        y_start = 1.0 - (y / SCREEN_HEIGHT) * 2.0
        x_end = ((x + w) / SCREEN_WIDTH) * 2.0 - 1.0
        y_end = 1.0 - ((y + h) / SCREEN_HEIGHT) * 2.0

        glBegin(GL_QUADS)
        glVertex2f(x_start, y_start)
        glVertex2f(x_end, y_start)
        glVertex2f(x_end, y_end)
        glVertex2f(x_start, y_end)
        glEnd()

        glColor4f(1.0, 1.0, 1.0, 1.0)

        if not self.font:
            glEnable(GL_DEPTH_TEST)
            return

        text_bytes = text.encode('utf-8')
        text_surface = TTF_RenderText_Blended(self.font, text_bytes, len(text_bytes), text_color)
        if not text_surface:
            glEnable(GL_DEPTH_TEST)
            return

        surf = text_surface.contents
        
        texture_id = GLuint()
        glGenTextures(1, byref(texture_id))
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, surf.pitch // 4) 
        
        pixels_pointer = cast(surf.pixels, c_void_p)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surf.w, surf.h, 0, GL_BGRA, GL_UNSIGNED_BYTE, pixels_pointer)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, 0)

        glEnable(GL_TEXTURE_2D)
        glBegin(GL_QUADS)
        
        text_x = x + (w - surf.w) / 2
        text_y = y + (h - surf.h) / 2

        t_x_start = (text_x / SCREEN_WIDTH) * 2.0 - 1.0
        t_y_start = 1.0 - (text_y / SCREEN_HEIGHT) * 2.0
        t_x_end = ((text_x + surf.w) / SCREEN_WIDTH) * 2.0 - 1.0
        t_y_end = 1.0 - ((text_y + surf.h) / SCREEN_HEIGHT) * 2.0

        glTexCoord2f(0.0, 0.0); glVertex2f(t_x_start, t_y_start)
        glTexCoord2f(1.0, 0.0); glVertex2f(t_x_end, t_y_start)
        glTexCoord2f(1.0, 1.0); glVertex2f(t_x_end, t_y_end)
        glTexCoord2f(0.0, 1.0); glVertex2f(t_x_start, t_y_end)
        
        glEnd()
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        glDeleteTextures(1, byref(texture_id))
        SDL_DestroySurface(text_surface)

    def update_button_state(self, event, button_id, x, y, w, h):
        if event.type in (SDL_EVENT_MOUSE_BUTTON_DOWN, SDL_EVENT_FINGER_DOWN):
            if event.type == SDL_EVENT_MOUSE_BUTTON_DOWN and event.button.button == SDL_BUTTON_LEFT:
                px, py = event.button.x, event.button.y
            elif event.type == SDL_EVENT_FINGER_DOWN:
                px = event.tfinger.x * SCREEN_WIDTH
                py = event.tfinger.y * SCREEN_HEIGHT
            else:
                return False

            if x <= px <= x + w and y <= py <= y + h:
                self.active_buttons[button_id] = True
                return True

        elif event.type in (SDL_EVENT_MOUSE_BUTTON_UP, SDL_EVENT_FINGER_UP):
            if button_id in self.active_buttons:
                del self.active_buttons[button_id]
                
                if event.type == SDL_EVENT_MOUSE_BUTTON_UP and event.button.button == SDL_BUTTON_LEFT:
                    px, py = event.button.x, event.button.y
                elif event.type == SDL_EVENT_FINGER_UP:
                    px = event.tfinger.x * SCREEN_WIDTH
                    py = event.tfinger.y * SCREEN_HEIGHT
                else:
                    return False

                if x <= px <= x + w and y <= py <= y + h:
                    return True
        return False

    def init_sdl_opengl(self):
        os.environ["SDL_VIDEODRIVER"] = "x11"
        if not SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMEPAD):
            print(f"Error al inicializar SDL: {SDL_GetError().decode()}", file=sys.stderr)
            return False

        if not TTF_Init():
            print(f"Error al inicializar TTF: {SDL_GetError().decode()}", file=sys.stderr)
            return False

        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 1)
        SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_COMPATIBILITY)
        SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1)

        self.window = SDL_CreateWindow(
            b"HERO Robot Control Center",
            SCREEN_WIDTH, SCREEN_HEIGHT,
            SDL_WINDOW_OPENGL | SDL_WINDOW_BORDERLESS
        )
        SDL_SetWindowPosition(self.window, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED)
        
        if not self.window:
            print(f"Error al crear la ventana: {SDL_GetError().decode()}", file=sys.stderr)
            return False

        self.gl_context = SDL_GL_CreateContext(self.window)
        if not self.gl_context:
            print(f"Error al crear el contexto OpenGL: {SDL_GetError().decode()}", file=sys.stderr)
            return False

        glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        glClearColor(0.1, 0.1, 0.14, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        font_path = b"DejaVuSans.ttf"
        self.font = TTF_OpenFont(font_path, 24)
        if not self.font:
            print(f"Advertencia: No se pudo cargar la fuente en {font_path.decode()}. El texto podría no renderizarse.")

        self.bot_texture, self.bot_w, self.bot_h = self.load_texture("ui/bot.png")
        self.backbtn_texture, self.backbtn_w, self.backbtn_h = self.load_texture("ui/back.png")

        self.cam_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.cam_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

        return True

    def set_ui_data(self, data_name : str, data):
        self.robot_data[data_name] = data

    def set_ui_page(self, page : str):
        self.current_page = page

    def handle_events(self):
        event = SDL_Event()
        while SDL_PollEvent(byref(event)):
            if event.type == SDL_EVENT_QUIT:
                self.running = False
                    
            elif event.type == SDL_EVENT_WINDOW_RESIZED:
                global SCREEN_WIDTH, SCREEN_HEIGHT
                SCREEN_WIDTH = event.window.data1
                SCREEN_HEIGHT = event.window.data2
                glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

            if self.current_page == "HOME":
                if self.update_button_state(event, "btn_connect", 20, 120, 200, 50) \
                and event.type in (SDL_EVENT_MOUSE_BUTTON_UP, SDL_EVENT_FINGER_UP):
                    print("CONNECT_CLICKED")

                if self.update_button_state(event, "btn_back", 16, SCREEN_HEIGHT - self.backbtn_h - 16, self.backbtn_w, self.backbtn_h) \
                and event.type in (SDL_EVENT_MOUSE_BUTTON_UP, SDL_EVENT_FINGER_UP):
                    print("BACK_CLICKED")

    def render(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        white_color = SDL_Color(255, 255, 255, 255)
        btn_bg = SDL_Color(50, 120, 220, 255)

        if self.cap.isOpened():
            self.rendercam, cam_frame = self.cap.read(0)
            self.faces_detected, self.gesture_detected = self.detector.procesar_frame(cam_frame)
            cam_h, cam_w, _ = cam_frame.shape
            glBindTexture(GL_TEXTURE_2D, self.cam_texture)
            glTexImage2D(
                GL_TEXTURE_2D, 
                0, 
                GL_RGB, 
                cam_w, 
                cam_h, 
                0, 
                GL_RGB, 
                GL_UNSIGNED_BYTE, 
                cv2.cvtColor(cv2.flip(cam_frame, 0), cv2.COLOR_BGR2RGB).tobytes()
            )
            self.render_texture(self.cam_texture, self.camframe_x, self.camframe_y, cam_w, cam_h)
            glBindTexture(GL_TEXTURE_2D, 0)

        if self.current_page == "HOME":
            if self.bot_texture:
                self.render_texture(self.bot_texture, 400, 100, self.bot_w, self.bot_h)

            if self.backbtn_texture:
                self.render_texture(self.backbtn_texture, 16, SCREEN_HEIGHT - self.backbtn_h - 16, self.backbtn_w, self.backbtn_h)

            self.render_button("btn_connect", "CONECTAR", 20, 120, 200, 50, btn_bg, white_color)

        with self.data_lock:
            status_text = f"Estado: {self.robot_data['status']}"
            battery_text = f"Bateria: {self.robot_data['battery']}%"

        self.render_text_to_opengl(status_text, 20, 20, white_color)
        self.render_text_to_opengl(battery_text, 20, 60, white_color)

        SDL_GL_SwapWindow(self.window)

    def run(self):
        if not self.init_sdl_opengl():
            return

        while self.running:
            self.handle_events()
            self.render()
            SDL_Delay(16)

        if self.font:
            TTF_CloseFont(self.font)
        TTF_Quit()
        
        if self.bot_texture:
            glDeleteTextures(1, byref(self.bot_texture))
        
        if self.backbtn_texture:
            glDeleteTextures(1, byref(self.backbtn_texture))

        SDL_GL_DestroyContext(self.gl_context)
        SDL_DestroyWindow(self.window)
        SDL_Quit()

if __name__ == "__main__":
    ui = HeroUI()
    ui.run()