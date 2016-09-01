from ..AudioClip import concatenate_audioclips

def audio_loop(audioclip, nloops=None, duracion=None):
    """ Loops over an audio clip.

    Returns an audio clip that plays the given clip either
    `nloops` times, or during `duracion` seconds.

    Examples
    ========
    
    >>> from moviepy.editor import *
    >>> videoclip = VideoFileClip('myvideo.mp4')
    >>> music = AudioFileClip('music.ogg')
    >>> audio = afx.audio_loop( music, duracion=videoclip.duracion)
    >>> videoclip.set_audio(audio)

    """

    if duracion is not None:

        nloops = int( duracion/ audioclip.duracion)+1
        return concatenate_audioclips(nloops*[audioclip]).set_duration(duracion)
    
    else:

        return concatenate_audioclips(nloops*[audioclip])
    
