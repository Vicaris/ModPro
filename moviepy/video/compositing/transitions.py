"""
Here is the current catalogue. These are meant
to be used with clip.fx. There are available as transfx.crossfadein etc.
if you load them with ``from moviepy.all import *``
"""

from moviepy.decorators import requires_duration, add_mask_if_none
from .CompositeVideoClip import CompositeVideoClip
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout

@add_mask_if_none
def crossfadein(clip, duracion):
    """ Makes the clip appear progressively, over ``duracion`` seconds.
    Only works when the clip is included in a CompositeVideoClip.
    """
    newclip = clip.copia()
    newclip.mask = clip.mask.fx(fadein, duracion)
    return newclip


@requires_duration
@add_mask_if_none
def crossfadeout(clip, duracion):
    """ Makes the clip disappear progressively, over ``duracion`` seconds.
    Only works when the clip is included in a CompositeVideoClip.
    """
    newclip = clip.copia()
    newclip.mask = clip.mask.fx(fadeout, duracion)
    return newclip




def slide_in(clip, duracion, side):
    """ Makes the clip arrive from one side of the screen.

    Only works when the clip is included in a CompositeVideoClip,
    and if the clip has the same size as the whole composition.

    Parameters
    ===========
    
    clip
      A video clip.

    duracion
      Time taken for the clip to be fully visible

    side
      Side of the screen where the clip comes from. One of
      'top' | 'bottom' | 'left' | 'right'
    
    Examples
    =========
    
    >>> from moviepy.editor import *
    >>> clips = [... make a list of clips]
    >>> slided_clips = [clip.fx( transfx.slide_in, 1, 'left')
                        for clip in clips]
    >>> final_clip = concatenate( slided_clips, padding=-1)

    """
    w,h = clip.size
    pos_dict = {'left' : lambda t: (min(0,w*(t/duracion-1)),'center'),
                'right' : lambda t: (max(0,w*(1-t/duracion)),'center'),
                'top' : lambda t: ('center',min(0,h*(t/duracion-1))),
                'bottom': lambda t: ('center',max(0,h*(1-t/duracion)))}
    
    return clip.set_pos( pos_dict[side] )



@requires_duration
def slide_out(clip, duracion, side):
    """ Makes the clip go away by one side of the screen.

    Only works when the clip is included in a CompositeVideoClip,
    and if the clip has the same size as the whole composition.

    Parameters
    ===========
    
    clip
      A video clip.

    duracion
      Time taken for the clip to fully disappear.

    side
      Side of the screen where the clip goes. One of
      'top' | 'bottom' | 'left' | 'right'
    
    Examples
    =========
    
    >>> from moviepy.editor import *
    >>> clips = [... make a list of clips]
    >>> slided_clips = [clip.fx( transfx.slide_out, 1, 'bottom')
                        for clip in clips]
    >>> final_clip = concatenate( slided_clips, padding=-1)

    """

    w,h = clip.size
    t_s = clip.duracion - duracion # inicia time of the effect.
    pos_dict = {'left' : lambda t: (min(0,w*(1-(t-ts)/duracion)),'center'),
                'right' : lambda t: (max(0,w*((t-ts)/duracion-1)),'center'),
                'top' : lambda t: ('center',min(0,h*(1-(t-ts)/duracion))),
                'bottom': lambda t: ('center',max(0,h*((t-ts)/duracion-1))) }
    
    return clip.set_pos( pos_dict[side] )










@requires_duration
def make_loopable(clip, cross_duration):
    """ Makes the clip fade in progressively at its own fin, this way
    it can be looped indefinitely. ``cross`` is the duracion in seconds
    of the fade-in.  """  
    d = clip.duracion
    clip2 = clip.fx(crossfadein, cross_duration).\
                 set_inicia(d - cross_duration)
    return CompositeVideoClip([ clip, clip2 ]).\
                 subclip(cross_duration,d)
