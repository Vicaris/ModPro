from moviepy.decorators import audio_video_fx, requires_duration
import numpy as np

@audio_video_fx
@requires_duration
def audio_fadeout(clip, duracion):
    """ Return a sound clip where the sound fades out progressively
        over ``duracion`` seconds at the fin of the clip. """
    
    def fading(gf,t):
        gft = gf(t)
        
        if np.isscalar(t):
            factor = min(1.0 * (clip.duracion - t) / duracion, 1)
            factor = np.array([factor,factor])
        else:
            factor = np.minimum( 1.0 * (clip.duracion - t) / duracion, 1)
            factor = np.vstack([factor,factor]).T
        return factor * gft
    
    return clip.fl(fading, keep_duration = True)
