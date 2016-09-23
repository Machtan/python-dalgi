from sdl2 import Rect
import ftoml as toml

class Resources:
    def __init__(self, renderer, scale=1):
        self._renderer = renderer
        self._textures = {}
        self._sprites = {}
        self._scale = scale
        self._loaded_resource_files = set()
        self._loaded_resource_names = set()
    
    def declare_simple_sprite(self, name: str, texture_path: str):
        print("Declaring: {} => {!r}".format(name, texture_path))
        self.declare_sprite(name, texture_path, None)
        
    def declare_sprite(self, name: str, texture_path: str, rect: Rect):
        assert(name not in self._sprites)
        
        if not texture_path in self._textures:
            self._textures[texture_path] = self._renderer.load_texture(texture_path)
        
        texture = self._textures[texture_path]
        # Allow passing a None rect to use the full texture
        dest = Rect(0, 0, 0, 0).resize(texture.width * self._scale, texture.height * self._scale)
        def draw_func(x, y, angle=0, flip_hor=False, flip_ver=False):
            self._renderer.copy_ex(
                texture,
                rect, 
                dest.moved_to(int(round(x)), int(round(y))),
                angle=angle, 
                flip_hor=flip_hor, 
                flip_ver=flip_ver
            )
        
        self._sprites[name] = draw_func
    
    def draw_function(self, sprite_name: str):
        assert(sprite_name in self._sprites)
        return self._sprites[sprite_name]
    
    def load(self, filepath: str):
        """Loads the resources specified in the given TOML file"""
        if filepath in self._loaded_resource_files: return
        with open(filepath, "r") as f:
            data = toml.loads(f.read())
        
        # TODO: validate the TOML structure
        
        resource_name = data["name"]
        assert(resource_name not in self._loaded_resource_names)
        if "simple" in data:
            for name, path in data["simple"].items():
                name = "{}/{}".format(resource_name, name)
                self.declare_simple_sprite(name, path)
        
        self._loaded_resource_files.add(filepath)
        self._loaded_resource_names.add(resource_name)