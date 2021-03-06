import time
from sdl2 import init_everything, Renderer, Window
from dalgi import EntityGroup
from typing import Callable, Union

Number = Union[float, int]

def run_simple_main_loop(setup_function: Callable[[Window, Renderer, EntityGroup], None],
        title: str="Dalgi", frame_sleep_time: Number=0.001):
    """Starts a simple dalgi SDL2 main loop after running the setup function.
    The function should have the following signature:
    setup_function(window, renderer, entity_group)"""
    """Entry point"""
    with init_everything() as context:
        window = context.build_window().title(title).finish()
        renderer = window.build_renderer().finish()
        renderer.set_clear_color(255, 255, 255)
        group = EntityGroup()
        context.set_quit_handler(lambda: group.quit())
        
        setup_function(window, renderer, group)
        
        group.validate_message_connections()
        group.init()
        last_frame = time.perf_counter()
        running = True
        while running:
            # handle events
            for event in context.get_events():
                group.handle(event)
                
            # update
            now = time.perf_counter()
            delta_time = now - last_frame
            last_frame = now
            group.update(delta_time)
            #print("Deltatime: {}".format(delta_time))
            
            # render
            renderer.clear()
            group.draw(renderer)
            
            renderer.present()
            
            # act nice
            time.sleep(frame_sleep_time)

class Ref:
    """A simple object to wrap primitives when modifying them from closures."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
