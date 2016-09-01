from moviepy.decorators import audio_video_fx
import numpy as np

@audio_video_fx
def audio_fadein(clip, duracion):
    """ Return an audio (or video) clip that is first mute, then the
        sound arrives progressively over ``duracion`` seconds. """
        
    def fading(gf,t):
        gft = gf(t)
        
        if np.isscalar(t):
            factor = min(1.0 * t / duracion, 1)
            factor = np.array([factor,factor])
        else:
            factor = np.minimum(1.0 * t / duracion, 1)
            factor = np.vstack([factor,factor]).T
        return factor * gft
    return clip.fl(fading, keep_duration = True)
