from collections import deque
from sdl2.events import *
import os

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
    def __init__(self, x=0, y=0):
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
    
    def init(self):
        for listener in self._listeners["init"]:
            listener.init(self)
        
    def add(self, entity, draw_layer: int = DEFAULT_DRAW_LAYER):
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
    
    def connect(self, entity, message: str, handler):
        #print("Connecting {} -> {}".format(entity, message))
        handlers = self._message_handlers.setdefault(message, {})
        assert(entity not in handlers)
        handlers[entity] = handler
    
    def send_message(self, message: str, *args):
        assert(message in self._messages)
        for handler in self._message_handlers[message].values():
            handler(*args)
    
    def validate_message_connections(self, ignore=None):
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
    
    def remove(self, entity):
        """Queues the removal of this entity at the beginning of the next call
        to 'update'"""
        self._removal_queue.append(entity)
    
    def _remove(self, entity):
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
    
    def destroy(self, entity):
        """Queues the destruction of this entity at the beginning of the next
        call to 'update'"""
        self._destruction_queue.append(entity)
    
    def _destroy(self, entity):
        assert(entity in self._entities)
        if hasattr(entity, "destroy"):
            entity.destroy()
        self._remove(entity)
    
    def add_tags(self, entity, *tags):
        assert(entity in self._entities)
        for tag in tags:
            if not tag in self._tagged:
                self._tagged[tag] = set()
            self._tagged[tag].add(entity)
    
    def find_all_with_tag(self, tag):
        assert(tag in self._tagged)
        return self._tagged[tag]
    
    def remove_tags(self, entity, *tags):
        assert(entity in self._entities)
        for tag in tags:
            assert(tag in self._tagged)
            entities = self._tagged[tag]
            for i, ent in enumerate(entities):
                if ent == entity:
                    entities.remove(i)
                    break
    
    def update(self, delta_time):
        while self._destruction_queue:
            self._destroy(self._destruction_queue.popleft())
        
        while self._removal_queue:
            self._remove(self._removal_queue.popleft())
        
        for listener in self._listeners["update"]:
            listener.update(delta_time)
    
    def draw(self, renderer, ox=0, oy=0):
        for layer in self._layers:
            for entity in self._drawables[layer]:
                entity.draw(renderer, self.x+ox, self.y+oy)
    
    def key_pressed(self, event):
        for listener in self._listeners["key_pressed"]:
            listener.key_pressed(event)
    
    def key_repeated(self, event):
        for listener in self._listeners["key_repeated"]:
            listener.key_repeated(event)
    
    def key_released(self, event):
        for listener in self._listeners["key_released"]:
            listener.key_released(event)
    
    # TODO: Check that this is correct behavior for nested groups
    def mouse_moved(self, sx, sy, x, y, dx, dy):
        for listener in self._listeners["mouse_moved"]:
            listener.mouse_moved(sx, sy, x-self.x, y-self.y, dx, dy)
    
    def mouse_pressed(self, sx, sy, x, y, button, is_touch):
        for listener in self._listeners["mouse_pressed"]:
            listener.mouse_pressed(sx, sy, x-self.x, y-self.y, button, is_touch)
    
    def mouse_released(self, sx, sy, x, y, button, is_touch):
        for listener in self._listeners["mouse_released"]:
            listener.mouse_released(sx, sy, x-self.x, y-self.y, button, is_touch)
    
    def mouse_scrolled(self, dx, dy, direction):
        for listener in self._listeners["mouse_scrolled"]:
            listener.mouse_scrolled(dx, dy, direction)
    
    def text_input(self, text):
        for listener in self._listeners["text_input"]:
            listener.text_input(text)
    
    def directory_dropped(self, path):
        for listener in self._listeners["directory_dropped"]:
            listener.directory_dropped(path)
    
    def file_dropped(self, path):
        for listener in self._listeners["mouse_moved"]:
            listener.file_dropped(path)
    
    def quit(self):
        for entity in self._listeners["quit"]:
            abort_shutdown = entity.quit()
            if abort_shutdown:
                return True
        
        return False
    
    def handle(self, event):
        t = type(event)
        if t == Quit:
            self.quit()
        
        elif t == KeyDown:
            if event.repeat:
                self.key_repeated(event)
            else:
                self.key_pressed(event)
        
        elif t == KeyUp:
            self.key_released(event)
        
        elif t == MouseButtonDown:
            self.mouse_pressed(event.x, event.y, event.x, event.y, event.button, False)
        
        elif t == MouseButtonUp:
            self.mouse_released(event.x, event.y, event.x, event.y, event.button, False)
        
        elif t == MouseMotion:
            self.mouse_moved(event.x, event.y, event.x, event.y, event.xrel, event.yrel)
        
        elif t == MouseWheel:
            self.mouse_scrolled(event.x, event.y, event.direction)
        
        elif t == TextInput:
            self.text_input(event.text)
        
        elif t == DropFile:
            if os.path.isdir(event.path):
                self.directory_dropped(event.path)
            else:
                self.file_dropped(event.path)
        
        
        
    