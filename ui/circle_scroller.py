from sdl2 import Rect
import math

class CircleScroller:
    """A scroller for circular motions.
    The scroller is activated by clicking it, after which the angle of
    the mouse is returned every time it moves.
    The callback is sent the new angle every time the mouse is moved when
    activated, and a 'None' when the scroller is deactivated."""
    
    AREA_INACTIVE_COLOR = (255, 150, 150)
    AREA_ACTIVE_COLOR = (150, 255, 150)
    CENTER_COLOR = (0, 0, 0)
    
    def __init__(self, rect, angle_callback):
        """Creates a new circular motion scroller."""
        self.rect = rect
        self.activated = False
        self.angle_callback = angle_callback
        self.crect = Rect.from_center(self.rect.center(), (10, 10))
    
    def mouse_pressed(self, sx, sy, x, y, button, is_touch):
        if self.rect.contains(x, y):
            self.activated = not self.activated
            if not self.activated:
                self.angle_callback(None)
        
    def angle(self, x, y):
        """Returns the angle between the center of the scroller and the
        given point. The coordinates should be relative to the entity group
        of the scroller."""
        cx, cy = self.rect.center()
        rx = x - cx
        ry = y - cy
        dist = math.sqrt(rx**2 + ry**2)
        if dist == 0:
            return 0
        ac = rx / dist
        angle = math.degrees(math.acos(ac))
        if y > cy:
            angle = 360 - angle
        return angle
    
    def mouse_moved(self, sx, sy, x, y, dx, dy):
        if not self.activated: return
        if self.crect.contains(x, y): return
        angle = self.angle(x, y)
        self.angle_callback(angle)
        
    def draw(self, renderer, ox, oy):
        area_color = self.AREA_ACTIVE_COLOR if self.activated else self.AREA_INACTIVE_COLOR
        renderer.c_fill_rect(area_color, self.rect.moved_by(ox, oy))
        renderer.c_fill_rect(self.CENTER_COLOR, self.crect)
