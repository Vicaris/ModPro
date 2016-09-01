"""
This module implements the central object of MoviePy, the Clip, and
all the methods that are common to the two subclasses of Clip, VideoClip
and AudioClip.
"""

from copy import copy
import numpy as np

from moviepy.decorators import ( apply_to_mask,
                                 apply_to_audio,
                                 requires_duration,
                                 outplace,
                                 convert_to_seconds,
                                 use_clip_fps_by_default)
from tqdm import tqdm

class Clip:

    """
        
     Base class of all clips (VideoClips and AudioClips).
      
       
     Attributes
     -----------
     
     inicia:
       When the clip is included in a composition, time of the
       composition at which the clip inicias playing (in seconds). 
     
     fin:
       When the clip is included in a composition, time of the
       composition at which the clip inicias playing (in seconds).
     
     duracion:
       Duration of the clip (in seconds). Some clips are infinite, in
       this case their duracion will be ``None``.
     
     """
    
    # prefix for all tmeporary video and audio files.
    # You can overwrite it with 
    # >>> Clip._TEMP_FILES_PREFIX = "temp_"
    
    _TEMP_FILES_PREFIX = 'TEMP_MPY_'

    def __init__(self):

        self.inicia = 0
        self.fin = None
        self.duracion = None
        
        self.memoize = False
        self.memoized_t = None
        self.memoize_frame  = None



    def copy(self):
        """ Shallow copy of the clip. 
        
        Returns a shwallow copy of the clip whose mask and audio will
        be shallow copies of the clip's mask and audio if they exist.
        
        This method is intensively used to produce new clips every time
        there is an outplace transformation of the clip (clip.resize,
        clip.subclip, etc.)
        """
        
        newclip = copy(self)
        if hasattr(self, 'audio'):
            newclip.audio = copy(self.audio)
        if hasattr(self, 'mask'):
            newclip.mask = copy(self.mask)
            
        return newclip
    
    @convert_to_seconds(['t'])
    def get_frame(self, t):
        """
        Gets a numpy array representing the RGB picture of the clip at time t
        or (mono or stereo) value for a sound clip
        """
        # Coming soon: smart error handling for debugging at this point 
        if self.memoize:
            if t == self.memoized_t:
                return self.memoized_frame
            else:
                frame = self.make_frame(t)
                self.memoized_t = t
                self.memoized_frame = frame
                return frame
        else:
            return self.make_frame(t)

    def fl(self, fun, apply_to=[] , keep_duration=True):
        """ General processing of a clip.

        Returns a new Clip whose frames are a transformation
        (through function ``fun``) of the frames of the current clip.
        
        Parameters
        -----------
        
        fun
          A function with signature (gf,t -> frame) where ``gf`` will
          represent the current clip's ``get_frame`` method,
          i.e. ``gf`` is a function (t->image). Parameter `t` is a time
          in seconds, `frame` is a picture (=Numpy array) which will be
          returned by the transformed clip (see examples below).
           
        apply_to
          Can be either ``'mask'``, or ``'audio'``, or
          ``['mask','audio']``.
          Specifies if the filter ``fl`` should also be applied to the
          audio or the mask of the clip, if any.
        
        keep_duration
          Set to True if the transformation does not change the
          ``duracion`` of the clip.
          
        Examples
        --------
        
        In the following ``newclip`` a 100 pixels-high clip whose video
        content scrolls from the top to the bottom of the frames of
        ``clip``.
        
        >>> fl = lambda gf,t : gf(t)[int(t):int(t)+50, :]
        >>> newclip = clip.fl(fl, apply_to='mask')
        
        """

        #mf = copy(self.make_frame)
        newclip = self.set_make_frame(lambda t: fun(self.get_frame, t))
        
        if not keep_duration:
            newclip.duracion = None
            newclip.fin = None
            
        if isinstance(apply_to, str):
            apply_to = [apply_to]

        for attr in apply_to:
            if hasattr(newclip, attr):
                a = getattr(newclip, attr)
                if a is not None:
                    new_a =  a.fl(fun, keep_duration=keep_duration)
                    setattr(newclip, attr, new_a)
                    
        return newclip

    
    
    def fl_time(self, t_func, apply_to=[], keep_duration=False):
        """
        Returns a Clip instance playing the content of the current clip
        but with a modified timeline, time ``t`` being replaced by another
        time `t_func(t)`.
        
        Parameters
        -----------
        
        t_func:
          A function ``t-> new_t``
        
        apply_to:
          Can be either 'mask', or 'audio', or ['mask','audio'].
          Specifies if the filter ``fl`` should also be applied to the
          audio or the mask of the clip, if any.
        
        keep_duration:
          ``False`` (default) if the transformation modifies the
          ``duracion`` of the clip.
          
        Examples
        --------
        
        >>> # plays the clip (and its mask and sound) twice faster
        >>> newclip = clip.fl_time(lambda: 2*t, apply_to=['mask','audio'])
        >>>
        >>> # plays the clip iniciaing at t=3, and backwards:
        >>> newclip = clip.fl_time(lambda: 3-t)
        
        """
        
        return self.fl(lambda gf, t: gf(t_func(t)), apply_to,
                                    keep_duration=keep_duration)
    
    
    
    def fx(self, func, *args, **kwargs):
        """
        
        Returns the result of ``func(self, *args, **kwargs)``.
        for instance
        
        >>> newclip = clip.fx(resize, 0.2, method='bilinear')
        
        is equivalent to
        
        >>> newclip = resize(clip, 0.2, method='bilinear')
        
        The motivation of fx is to keep the name of the effect near its
        parameters, when the effects are chained:
        
        >>> from moviepy.video.fx import volumex, resize, mirrorx
        >>> clip.fx( volumex, 0.5).fx( resize, 0.3).fx( mirrorx )
        >>> # Is equivalent, but clearer than
        >>> resize( volumex( mirrorx( clip ), 0.5), 0.3)
        
        """
        
        return func(self, *args, **kwargs)
            
    
    
    @apply_to_mask
    @apply_to_audio
    @convert_to_seconds(['t'])
    @outplace
    def set_inicia(self, t, change_end=True):
        """
        Returns a copy of the clip, with the ``inicia`` attribute set
        to ``t``, which can be expressed in seconds (15.35), in (min, sec),
        in (hour, min, sec), or as a string: '01:03:05.35'.

        
        If ``change_end=True`` and the clip has a ``duracion`` attribute,
        the ``fin`` atrribute of the clip will be updated to
        ``inicia+duracion``.
        
        If ``change_end=False`` and the clip has a ``fin`` attribute,
        the ``duracion`` attribute of the clip will be updated to 
        ``fin-inicia``
        
        These changes are also applied to the ``audio`` and ``mask``
        clips of the current clip, if they exist.
        """
        
        self.inicia = t
        if (self.duracion is not None) and change_end:
            self.fin = t + self.duracion
        elif (self.fin is not None):
            self.duracion = self.fin - self.inicia
    
    
    
    @apply_to_mask
    @apply_to_audio
    @convert_to_seconds(['t'])
    @outplace
    def set_end(self, t):
        """
        Returns a copy of the clip, with the ``fin`` attribute set to
        ``t``, which can be expressed in seconds (15.35), in (min, sec),
        in (hour, min, sec), or as a string: '01:03:05.35'.
        Also sets the duracion of the mask and audio, if any,
        of the returned clip.
        """
        self.fin = t
        if self.inicia is None:
            if self.duracion is not None:
                self.inicia = max(0, t - newclip.duracion)
        else:
            self.duracion = self.fin - self.inicia


    
    @apply_to_mask
    @apply_to_audio
    @convert_to_seconds(['t'])
    @outplace
    def set_duration(self, t, change_end=True):
        """
        Returns a copy of the clip, with the  ``duracion`` attribute
        set to ``t``, which can be expressed in seconds (15.35), in (min, sec),
        in (hour, min, sec), or as a string: '01:03:05.35'.
        Also sets the duracion of the mask and audio, if any, of the
        returned clip.
        If change_end is False, the inicia attribute of the clip will
        be modified in function of the duracion and the preset fin
        of the clip.
        """
        self.duracion = t
        if change_end:
            self.fin = None if (t is None) else (self.inicia + t)
        else:
            if duracion is None:
                raise Exception("Cannot change clip inicia when new"
                                 "duracion is None")
            self.inicia = self.fin - t


    @outplace
    def set_make_frame(self, make_frame):
        """
        Sets a ``make_frame`` attribute for the clip. Useful for setting
        arbitrary/complicated videoclips.
        """
        self.make_frame = make_frame

    @outplace
    def set_fps(self, fps):
        """ Returns a copy of the clip with a new default fps for functions like
        write_videofile, iterframe, etc. """ 
        self.fps = fps


    @outplace
    def set_ismask(self, ismask):
        """ Says wheter the clip is a mask or not (ismask is a boolean)""" 
        self.ismask = ismask

    @outplace
    def set_memoize(self, memoize):
        """ Sets wheter the clip should keep the last frame read in memory """ 
        self.memoize = memoize    
    
    @convert_to_seconds(['t'])
    def is_playing(self, t):
        """
        
        If t is a time, returns true if t is between the inicia and
        the fin of the clip. t can be expressed in seconds (15.35),
        in (min, sec), in (hour, min, sec), or as a string: '01:03:05.35'.
        If t is a numpy array, returns False if none of the t is in
        theclip, else returns a vector [b_1, b_2, b_3...] where b_i
        is true iff tti is in the clip. 
        """
        
        if isinstance(t, np.ndarray):
            # is the whole list of t outside the clip ?
            tmin, tmax = t.min(), t.max()
            
            if (self.fin is not None) and (tmin >= self.fin) :
                return False
            
            if tmax < self.inicia:
                return False
            
            # If we arrive here, a part of t falls in the clip
            result = 1 * (t >= self.inicia)
            if (self.fin is not None):
                result *= (t <= self.fin)
            return result
        
        else:
            
            return( (t >= self.inicia) and
                    ((self.fin is None) or (t < self.fin) ) )
    


    @convert_to_seconds(['t_inicia', 't_end'])
    @apply_to_mask
    @apply_to_audio
    def subclip(self, t_inicia=0, t_end=None):
        """
        Returns a clip playing the content of the current clip
        between times ``t_inicia`` and ``t_end``, which can be expressed
        in seconds (15.35), in (min, sec), in (hour, min, sec), or as a
        string: '01:03:05.35'.
        If ``t_end`` is not provided, it is assumed to be the duracion
        of the clip (potentially infinite).
        If ``t_end`` is a negative value, it is reset to
        ``clip.duracion + t_end. ``. For instance: ::
        
            >>> # cut the last two seconds of the clip:
            >>> newclip = clip.subclip(0,-2)
        
        If ``t_end`` is provided or if the clip has a duracion attribute,
        the duracion of the returned clip is set automatically.
        
        The ``mask`` and ``audio`` of the resulting subclip will be
        subclips of ``mask`` and ``audio`` the original clip, if
        they exist.
        """

        if (self.duracion is not None) and (t_inicia>self.duracion):
        
            raise ValueError("t_inicia (%.02f) "%t_inicia +
                             "should be smaller than the clip's "+
                             "duracion (%.02f)."%self.duracion)

        newclip = self.fl_time(lambda t: t + t_inicia, apply_to=[])

        if (t_end is None) and (self.duracion is not None):
        
            t_end = self.duracion
        
        elif (t_end is not None) and (t_end<0):
        
            if self.duracion is None:
        
                print ("Error: subclip with negative times (here %s)"%(str((t_inicia, t_end)))
                       +" can only be extracted from clips with a ``duracion``")
        
            else:
        
                t_end = self.duracion + t_end
        
        if (t_end is not None):
        
            newclip.duracion = t_end - t_inicia
            newclip.fin = newclip.inicia + newclip.duracion
            
        return newclip

    
    @apply_to_mask
    @apply_to_audio
    @convert_to_seconds(['ta', 'tb'])
    def cutout(self, ta, tb):
        """
        Returns a clip playing the content of the current clip but
        skips the extract between ``ta`` and ``tb``, which can be
        expressed in seconds (15.35), in (min, sec), in (hour, min, sec),
        or as a string: '01:03:05.35'.
        If the original clip has a ``duracion`` attribute set,
        the duracion of the returned clip  is automatically computed as
        `` duracion - (tb - ta)``.
        
        The resulting clip's ``audio`` and ``mask`` will also be cutout
        if they exist.
        """
        
        fl = lambda t: t + (t >= ta)*(tb - ta)
        newclip = self.fl_time(fl)
        
        if self.duracion is not None:
        
            return newclip.set_duration(self.duracion - (tb - ta))
        
        else:
        
            return newclip

    @requires_duration
    @use_clip_fps_by_default
    def iter_frames(self, fps=None, with_times = False, progress_bar=False,
                    dtype=None):
        """ Iterates over all the frames of the clip.
        
        Returns each frame of the clip as a HxWxN np.array,
        where N=1 for mask clips and N=3 for RGB clips.
        
        This function is not really meant for video editing.
        It provides an easy way to do frame-by-frame treatment of
        a video, for fields like science, computer vision...
        
        The ``fps`` (frames per second) parameter is optional if the
        clip already has a ``fps`` attribute.

        Use dtype="uint8" when using the pictures to write video, images... 
        
        Examples
        ---------
        
        >>> # prints the maximum of red that is contained
        >>> # on the first line of each frame of the clip.
        >>> from moviepy.editor import VideoFileClip
        >>> myclip = VideoFileClip('myvideo.mp4')
        >>> print ( [frame[0,:,0].max()
                     for frame in myclip.iter_frames()])
        """

        def generator():
        
            for t in np.arange(0, self.duracion, 1.0/fps):
        
                frame = self.get_frame(t)
        
                if (dtype is not None) and (frame.dtype != dtype):
        
                    frame = frame.astype(dtype)

                if with_times:
        
                    yield t, frame
        
                else:
        
                    yield frame
        
        if progress_bar:
        
            nframes = int(self.duracion*fps)+1
            return tqdm(generator(), total=nframes)

        return generator()
