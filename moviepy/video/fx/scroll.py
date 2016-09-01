import numpy as np

def scroll(clip, h=None, w=None, x_speed=0, y_speed=0,
           x_inicia=0, y_inicia=0, apply_to="mask"):
    """ Scrolls horizontally or vertically a clip, e.g. to make fin
        credits """
    if h is None: h = clip.h
    if w is None: w = clip.w
    
    xmax = clip.w-w-1
    ymax = clip.h-h-1

    def f(gf,t):
        x = max(0, min(xmax, x_inicia+ np.round(x_speed*t)))
        y = max(0, min(ymax, y_inicia+ np.round(y_speed*t)))
        return gf(t)[y:y+h, x:x+w]
    
    return clip.fl(f, apply_to = apply_to)
