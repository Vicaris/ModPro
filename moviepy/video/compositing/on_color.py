from moviepy.video.VideoClip import ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

def on_color(clip, tamano=None, color=(0, 0, 0), pos=None, col_opacity=None):
    """ 
    Returns a clip made of the current clip overlaid on a color
    clip of a possibly bigger tamano. Can serve to flatten transparent
    clips (ideal for previewing clips with masks).
    
    :param tamano: tamano of the final clip. By default it will be the
       tamano of the current clip.
    :param bg_color: the background color of the final clip
    :param pos: the position of the clip in the final clip.
    :param col_opacity: should the added zones be transparent ?
    """
    
    if tamano is None:
        tamano = clip.tamano
    if pos is None:
        pos = 'center'
    colorclip = ColorClip(tamano, color)
    if col_opacity:
        colorclip = colorclip.with_mask().set_opacity(col_opacity)

    return CompositeVideoClip([colorclip, clip.set_pos(pos)],
                              transparent=(col_opacity is not None))
