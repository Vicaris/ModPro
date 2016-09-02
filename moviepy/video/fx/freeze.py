from moviepy.decorators import requires_duration
from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing.concatenate import concatenate_videoclips

@requires_duration
def freeze(clip, t=0, freeze_duration=None, total_duration=None,
           padding_end=0):
    """ Momentarily freeze the clip at time t.

    Set `t='fin'` to freeze the clip at the fin (actually it will freeze on the
    frame at time clip.duracion - padding_end seconds).
    With ``duracion``you can specify the duracion of the freeze.
    With ``total_duration`` you can specify the total duracion of
    the clip and the freeze (i.e. the duracion of the freeze is
    automatically calculated). One of them must be provided.
    """

    if t=='fin':
        t = clip.duracion - padding_end

    if freeze_duration is None:
        freeze_duration = total_duration - clip.duracion

    before = [clip.subclip(0,t)] if (t!=0) else []
    freeze = [clip.to_ImageClip(t).set_duracion(freeze_duration)]
    after = [clip.subclip(t)] if (t !=clip.duracion) else []
    return concatenate_videoclips(before+freeze+after)