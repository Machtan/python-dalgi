
class Label:
    """A widget to show text on the screen"""
    def __init__(self, x, y, text, font, renderer, color=(0, 0, 0)):
        self.x = x
        self.y = y
        self._color = color
        self._text = text
        self.renderer = renderer
        self._font = font
        self.textures = []
        self.dirty = True
    
    def redraw(self):
        self.textures.clear()
        for line in self._text.splitlines():
            surf = self._font.render_blended(line, self._color)
            tex = self.renderer.create_texture_from_surface(surf)
            self.textures.append(tex)
        
        self.dirty = False
    
    def draw(self, renderer, ox, oy):
        if self.dirty:
            self.redraw()
        x = self.x + ox
        y = self.y + oy
        ls = self._font.line_skip()
        for texture in self.textures:
            renderer.copy(texture, dst_rect=texture.rect_at(x, y))
            y += ls
    
    @property
    def font(self):
        """The font of this label. Set to update."""
        return self._font
    
    @font.setter
    def font(self, value):
        if value != self._font:
            self._font = value
            self.dirty = True
    
    @property
    def text(self):
        """The text of this label. Set to update."""
        return self._text
    
    @text.setter
    def text(self, value):
        if value != self._text:
            self._text = value
            self.dirty = True
    
    @property
    def color(self):
        """The color of this label. Set to update."""
        return self._color
    
    @color.setter
    def color(self, value):
        if value != self._color:
            self._color = value
            self.dirty = True
