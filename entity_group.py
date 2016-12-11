from collections import deque
from sdl2.events import Quit, KeyDown, KeyUp, MouseButtonDown, MouseButtonUp
from sdl2.events import MouseMotion, MouseWheel, TextInput, DropFile
from sdl2 import Renderer, MouseButton, Event
import os
from typing import Any, Optional, Callable, Iterator, cast

LISTENERS = [
    "init",
    "destroy",
    "update",
    "key_pressed",
    "key_repeated",
    "key_released",
    "mouse_pressed",
    "mouse_released",
    "mouse_moved",
    "mouse_scrolled",
    "text_input",
    "file_dropped",
    "directory_dropped",
    "quit",
]
DEFAULT_DRAW_LAYER = 1
class EntityGroup:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self.x = x
        self.y = y
        self._listeners = {}
        for category in LISTENERS:
            self._listeners[category] = []
        self._tags = {}
        self._entities = set()
        self._tagged = {}
        self._drawables = { DEFAULT_DRAW_LAYER : [] }
        self._layers = [ DEFAULT_DRAW_LAYER ]
        self._messages = set()
        self._message_handlers = {} # {message: {entity: handler}}
        self._destruction_queue = deque()
        self._removal_queue = deque()
        self.parent = None
    
    def init(self, parent: Any=None):
        """Called when all entities have been added to the group, and is meant
        to let entities refer to the group and make connections to other
        entities."""
        self.parent = parent
        for listener in self._listeners["init"]:
            listener.init(self)
        
    def add(self, entity: Any, draw_layer: int = DEFAULT_DRAW_LAYER):
        """Adds a new entity to the group"""
        assert(entity not in self._entities)
        if hasattr(entity, "draw"):
            if not draw_layer in self._drawables:
                self._drawables[draw_layer] = []
                self._layers.append(draw_layer)
                self._layers.sort()
            self._drawables[draw_layer].append(entity)
        
        for category, entities in self._listeners.items():
            if hasattr(entity, category):
                entities.append(entity)
        
        self._entities.add(entity)
    
    def register_messages(self, *messages: str):
        for message in messages:
            self._messages.add(message)
            if not message in self._message_handlers:
                self._message_handlers[message] = {}
    
    def connect(self, entity: Any, message: str, handler: Callable):
        #print("Connecting {} -> {}".format(entity, message))
        handlers = self._message_handlers.setdefault(message, {})
        assert(entity not in handlers)
        handlers[entity] = handler
    
    def send_message(self, message: str, *args):
        assert(message in self._messages)
        for handler in self._message_handlers[message].values():
            handler(*args)
    
    def validate_message_connections(self, ignore: Optional[set]=None):
        """Validates that all messages are used"""
        if ignore is None:
            ignore = set()
        unused = []
        unregistered = []
        for message, handlers in self._message_handlers.items():
            if message not in self._messages:
                unregistered.append(message)
                continue
            if not handlers:
                if message in ignore:
                    continue
                unused.append(message)
        
        if unused or unregistered:
            raise Exception("Unregistered message(s): {}, Unused message type(s): {}".format(
                unregistered, unused
            ))
    
    def remove(self, entity: Any):
        """Queues the removal of this entity at the beginning of the next call
        to 'update'"""
        self._removal_queue.append(entity)
    
    def _remove(self, entity: Any):
        assert(entity in self._entities)
        for tag, entities in self._tagged.items():
            for i, ent in enumerate(entities):
                if ent == entity:
                    entities.remove(i)
                    break
        
        if hasattr(entity, "draw"):
            for layer in self._drawables:
                for i, ent in enumerate(layer):
                    if ent == entity:
                        layer.remove(i)
                        break
        
        for category in LISTENERS:
            if hasattr(entity, category):
                for i, ent in enumerate(self._listeners[category]):
                    if ent == entity:
                        self._listeners[category].remove(i)
                        break
        
        for handlers in self._message_handlers.values():
            if entity in handlers:
                handlers.remove(entity)
        
        self._entities.remove(entity)
    
    def destroy(self, entity: Any):
        """Queues the destruction of this entity at the beginning of the next
        call to 'update'"""
        self._destruction_queue.append(entity)
    
    def _destroy(self, entity: Any):
        assert(entity in self._entities)
        if hasattr(entity, "destroy"):
            entity.destroy()
        self._remove(entity)
    
    def add_tags(self, entity: Any, *tags: str):
        assert(entity in self._entities)
        for tag in tags:
            if not tag in self._tagged:
                self._tagged[tag] = set()
            self._tagged[tag].add(entity)
    
    def find_all_with_tag(self, tag: str) -> Iterator[Any]:
        assert(tag in self._tagged)
        return self._tagged[tag]
    
    def remove_tags(self, entity, *tags: str):
        assert(entity in self._entities)
        for tag in tags:
            assert(tag in self._tagged)
            entities = self._tagged[tag]
            for i, ent in enumerate(entities):
                if ent == entity:
                    entities.remove(i)
                    break
    
    def update(self, delta_time: float):
        while self._destruction_queue:
            self._destroy(self._destruction_queue.popleft())
        
        while self._removal_queue:
            self._remove(self._removal_queue.popleft())
        
        for listener in self._listeners["update"]:
            listener.update(delta_time)
    
    def draw(self, renderer: Renderer):
        """Called when it is time to render the frame."""
        with renderer.offset_context(self.x, self.y):
            for layer in self._layers:
                for entity in self._drawables[layer]:
                    entity.draw(renderer, self.x, self.y)
    
    def key_pressed(self, event: KeyDown):
        """Called when a key on the keyboard is pressed."""
        for listener in self._listeners["key_pressed"]:
            listener.key_pressed(event)
    
    def key_repeated(self, event: KeyDown):
        """Called when a key on the keyboard is held long enough for it to
        start repeating the input. This is called repeatedly after that."""
        for listener in self._listeners["key_repeated"]:
            listener.key_repeated(event)
    
    def key_released(self, event: KeyUp):
        """Called when a key on the keyboard is released."""
        for listener in self._listeners["key_released"]:
            listener.key_released(event)
    
    # TODO: Check that this is correct behavior for nested groups
    def mouse_moved(self, sx: int, sy: int, x: int, y: int, dx: int, dy: int):
        """Called when the mouse is moved.
        'sx' and 'sy' are the 'screen coordinates' (pixels) while 'x' and 'y'
        are the screen coordinates mapped relative to the entity group.
        'dx' and 'dy' are the relative movement of the mouse in pixels on the
        horizontal and vertical axes."""
        for listener in self._listeners["mouse_moved"]:
            listener.mouse_moved(sx, sy, x-self.x, y-self.y, dx, dy)
    
    def mouse_pressed(self, sx: int, sy: int, x: int, y: int, button: MouseButton, is_touch: bool):
        """Called when a mouse button is pressed.
        sx and sy are the 'screen coordinates' (pixels) while x and y
        are the screen coordinates mapped relative to the entity group."""
        for listener in self._listeners["mouse_pressed"]:
            listener.mouse_pressed(sx, sy, x-self.x, y-self.y, button, is_touch)
    
    def mouse_released(self, sx: int, sy: int, x: int, y: int, button: MouseButton, is_touch: bool):
        for listener in self._listeners["mouse_released"]:
            listener.mouse_released(sx, sy, x-self.x, y-self.y, button, is_touch)
    
    def mouse_scrolled(self, dx: int, dy: int, direction: int):
        for listener in self._listeners["mouse_scrolled"]:
            listener.mouse_scrolled(dx, dy, direction)
    
    def text_input(self, text: str):
        for listener in self._listeners["text_input"]:
            listener.text_input(text)
    
    def directory_dropped(self, path: str):
        for listener in self._listeners["directory_dropped"]:
            listener.directory_dropped(path)
    
    def file_dropped(self, path: str):
        for listener in self._listeners["mouse_moved"]:
            listener.file_dropped(path)
    
    def quit(self):
        for entity in self._listeners["quit"]:
            abort_shutdown = entity.quit()
            if abort_shutdown:
                return True
        
        return False
    
    def handle(self, event: Event):
        t = type(event)
        if t == Quit:
            self.quit()
        
        elif t == KeyDown:
            event = cast(KeyDown, event)
            if event.repeat:
                self.key_repeated(event)
            else:
                self.key_pressed(event)
        
        elif t == KeyUp:
            event = cast(KeyUp, event)
            self.key_released(event)
        
        elif t == MouseButtonDown:
            event = cast(MouseButtonDown, event)
            self.mouse_pressed(event.x, event.y, event.x, event.y, event.button, False)
        
        elif t == MouseButtonUp:
            event = cast(MouseButtonUp, event)
            self.mouse_released(event.x, event.y, event.x, event.y, event.button, False)
        
        elif t == MouseMotion:
            event = cast(MouseMotion, event)
            self.mouse_moved(event.x, event.y, event.x, event.y, event.xrel, event.yrel)
        
        elif t == MouseWheel:
            event = cast(MouseWheel, event)
            self.mouse_scrolled(event.x, event.y, event.direction)
        
        elif t == TextInput:
            event = cast(TextInput, event)
            self.text_input(event.text)
        
        elif t == DropFile:
            event = cast(DropFile, event)
            if os.path.isdir(event.file):
                self.directory_dropped(event.file)
            else:
                self.file_dropped(event.file)
        
        
        
    