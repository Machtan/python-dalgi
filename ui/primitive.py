class ColorRect:
    """A simple colored rectangle."""
    def __init__(self, color, rect):
        self.rect = rect
        self.color = color
    
    def draw(self, renderer, ox, oy):
        renderer.c_fill_rect(self.color, self.rect.moved_by(ox, oy))
