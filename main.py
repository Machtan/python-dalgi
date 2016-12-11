from dalgi import run_simple_main_loop, Ref
from dalgi.ui import Label, ColorRect, CircleScroller
from sdl2 import Rect, Font

def main():
    def setup(window, renderer, group):
        rect = ColorRect((255, 0, 0), Rect(300, 0, 200, 10))
        fontpath = "/System/Library/Fonts/HelveticaNeueDeskInterface.ttc"
        font = Font.load(fontpath, 16)
        text = Label(10, 10, "Hello World", font, renderer)
        r_angle = Ref(val=None)
        def angle_callback(angle):
            if r_angle.val is None:
                r_angle.val = angle
                return
            
            if angle is None:
                r_angle.val = None
                return
            
            text.text = "Angle: {:>3}".format(int(round(angle)))
            SPEED = 5
            diff = r_angle.val - angle
            LIMIT = 320
            if diff > LIMIT:
                diff -= 360
            elif diff < -LIMIT:
                diff += 360
            
            #dy = int(round(diff * 0.2)) 
            if diff > 0:
                dy = SPEED
            else:
                dy = -SPEED
            r_angle.val = angle
            rect.rect.move_by(0, dy)
        
        scroller = CircleScroller(Rect(50, 50, 200, 200), angle_callback)
        group.add(scroller)
        group.add(text)
        group.add(rect)
        
    
    run_simple_main_loop(setup)
    
if __name__ == '__main__':
    main()
