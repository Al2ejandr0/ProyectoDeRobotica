#include <iostream>
#include <climits>
#include <unistd.h>
#include <SDL3/SDL.h>
#include <SDL3/SDL_opengl.h>
#define APP_NAME "hero_ui"

bool draw_sprite(){
    return true;
}

int main(int argc, const char **argv){
    SDL_Init(SDL_INIT_AUDIO | SDL_INIT_VIDEO | SDL_INIT_GAMEPAD);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, 3);
    SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, SDL_GL_CONTEXT_PROFILE_CORE);
    const char* title = "HeroUI";
    SDL_Window* main_window = SDL_CreateWindow(title, 800, 600, SDL_WINDOW_OPENGL | SDL_WINDOW_FULLSCREEN);
    SDL_GLContext gl_context = SDL_GL_CreateContext(main_window);
    SDL_GL_MakeCurrent(main_window, gl_context);
    SDL_GL_SetSwapInterval(1);
    SDL_Event event;

    while (true){
        while (SDL_PollEvent(&event)){
            switch (event.type){
            case SDL_EVENT_QUIT:
                SDL_GL_DestroyContext(gl_context);
                SDL_DestroyWindow(main_window);
                SDL_Quit();
                return 0;
            }
        }
        glClearColor(0.1, 0.2, 0.3, 1.0);
        glClear(GL_COLOR_BUFFER_BIT);
        SDL_GL_SwapWindow(main_window);
    }
}