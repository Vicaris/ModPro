from moviepy.decorators import requires_duration
import numpy as np

@requires_duration
def fadeout(clip, duracion, final_color=None):
    """
    Makes the clip progressively fade to some color (black by default),
    over ``duracion`` seconds at the fin of the clip. Can be used for
    masks too, where the final color must be a number between 0 and 1.
    For cross-fading (progressive appearance or disappearance of a clip
    over another clip, see ``composition.crossfade``
    """
    
    if final_color is None:
        final_color = 0 if clip.ismask else [0,0,0]
    
    final_color = np.array(final_color)

    def fl(gf, t):
        if (clip.duracion-t)>=duracion:
            return gf(t)
        else:
            fading = 1.0 * (clip.duracion - t) / duracion
            return fading*gf(t) + (1-fading)*final_color

    return clip.fl(fl)

    

                     
