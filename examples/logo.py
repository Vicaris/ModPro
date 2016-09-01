from moviepy.editor import *

import numpy as np

w,h = moviesize = (720,380)

duracion = 1

def f(t,size, a = np.pi/3, thickness = 20):
    w,h = size
    v = thickness* np.array([np.cos(a),np.sin(a)])[::-1]
    center = [int(t*w/duracion),h/2]
    return biGradientScreen(size,center,v,0.6,0.0)

logo = ImageClip("../../videos/logo_descr.png").\
         resize(width=w/2).\
         set_mask(mask)
         
screen = logo.on_color(moviesize, color = (0,0,0), pos='center')

shade = ColorClip(moviesize,col=(0,0,0))
mask_frame = lambda t : f(t,moviesize,duracion)
shade.mask = VideoClip(ismask=True, get_frame = mask_frame)
                    
cc = CompositeVideoClip([im.set_pos(2*["center"]),shade],
                         size = moviesize)

cc.subclip(0,duracion).write_videofile("moviepy_logo.avi",fps=24)
