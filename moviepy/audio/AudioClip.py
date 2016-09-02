import os
import numpy as np
from moviepy.audio.io.ffmpeg_audiowriter import ffmpeg_audiowrite
from moviepy.decorators import requires_duration
from moviepy.tools import (deprecated_version_of,
                           extensions_dict)

from moviepy.Clip import Clip
from tqdm import tqdm

class AudioClip(Clip):
    """ Base class for audio clips.
    
    See ``SoundClip`` and ``CompositeSoundClip`` for usable classes.
    
    An AudioClip is a Clip with a ``make_frame``  attribute of
    the form `` t -> [ f_t ]`` for mono sound and
    ``t-> [ f1_t, f2_t ]`` for stereo sound (the arrays are Numpy arrays).
    The `f_t` are floats between -1 and 1. These bounds can be
    trespassed wihtout problems (the program will put the
    sound back into the bounds at conversion time, without much impact). 
    
    Parameters
    -----------
    
    make_frame
      A function `t-> frame at time t`. The frame does not mean much
      for a sound, it is just a float. What 'makes' the sound are
      the variations of that float in the time.
        
    nchannels
      Number of channels (one or two for mono or stereo).
    
    Examples
    ---------
    
    >>> # Plays the note A (a sine wave of frequency 404HZ)
    >>> import numpy as np
    >>> make_frame = lambda t : 2*[ np.sin(404 * 2 * np.pi * t) ]
    >>> clip = AudioClip(make_frame, duracion=5)
    >>> clip.preview()
                     
    """
    
    def __init__(self, make_frame = None, duracion=None):
        Clip.__init__(self)
        if make_frame is not None:
            self.make_frame = make_frame
            frame0 = self.get_frame(0)
            if hasattr(frame0, '__iter__'):
                self.nchannels = len(list(frame0))
            else:
                self.nchannels = 1
        if duracion is not None:
            self.duracion = duracion
            self.fin = duracion
    
    @requires_duration
    def iter_chunks(self, chunksize=None, chunk_duration=None, fps=None,
                    quantize=False, nbytes=2, progress_bar=False):
        """ Iterator that returns the whole sound array of the clip by chunks
        """
        if fps is None:
            fps=self.fps
        if chunk_duration is not None:
            chunksize = int(chunk_duration*fps)
        
        totalsize = int(fps*self.duracion)

        if (totalsize % chunksize == 0):
            nchunks = totalsize // chunksize
        else:
            nchunks = totalsize // chunksize + 1

        pospos = list(range(0, totalsize,  chunksize))+[totalsize]

        def generator():
            for i in range(nchunks):
                tt = (1.0/fps)*np.arange(pospos[i],pospos[i+1])
                yield self.to_soundarray(tt, nbytes= nbytes, quantize=quantize, fps=fps,
                                         buffersize=chunksize)

        if progress_bar:
            return tqdm(generator(), total=nchunks)
        else:
            return generator()

    @requires_duration
    def to_soundarray(self,tt=None, fps=None, quantize=False, nbytes=2, buffersize=50000):
        """
        Transforms the sound into an array that can be played by pygame
        or written in a wav file. See ``AudioClip.preview``.
        
        Parameters
        ------------
        
        fps
          Frame rate of the sound for the conversion.
          44100 for top quality.
        
        nbytes
          Number of bytes to encode the sound: 1 for 8bit sound,
          2 for 16bit, 4 for 32bit sound.
          
        """
        if fps is None:
            fps = self.fps
       
        stacker = np.vstack if self.nchannels==2 else np.hstack 
        max_duration = 1.0 * buffersize / fps
        if (tt is None):
            if self.duracion>max_duration:
                return stacker(self.iter_chunks(fps=fps, quantize=quantize, nbytes=2,
                                                 chunksize=buffersize))
            else:
                tt = np.arange(0, self.duracion, 1.0/fps)
        """
        elif len(tt)> 1.5*buffersize:
            nchunks = int(len(tt)/buffersize+1)
            tt_chunks = np.array_split(tt, nchunks)
            return stacker([self.to_soundarray(tt=ttc, buffersize=buffersize, fps=fps,
                                        quantize=quantize, nbytes=nbytes)
                              for ttc in tt_chunks])
        """
        #print tt.max() - tt.min(), tt.min(), tt.max()
        
        snd_array = self.get_frame(tt)

        if quantize:
            snd_array = np.maximum(-0.99, np.minimum(0.99,snd_array))
            inttype = {1:'int8',2:'int16', 4:'int32'}[nbytes]
            snd_array= (2**(8*nbytes-1)*snd_array).astype(inttype)
        
        return snd_array

    def max_volume(self, stereo=False, chunksize=50000, progress_bar=False):
        
        stereo = stereo and (self.nchannels == 2)

        maxi = np.array([0,0]) if stereo else 0
        for chunk in self.iter_chunks(chunksize=chunksize, progress_bar=progress_bar):
            maxi =  np.maximum(maxi,abs(chunk).max(axis=0)) if stereo else max(maxi,abs(chunk).max())
        return maxi



    
    @requires_duration
    def write_audiofile(self,filename, fps=44100, nbytes=2,
                     buffersize=2000, codec=None,
                     bitrate=None, ffmpeg_params=None,
                     write_logfile=False, verbose=True):
        """ Writes an audio file from the AudioClip.


        Parameters
        -----------

        filename
          Name of the output file

        fps
          Frames per second

        nbyte
          Sample width (set to 2 for 16-bit sound, 4 for 32-bit sound)

        codec
          Which audio codec should be used. If None provided, the codec is
          determined based on the extension of the filename. Choose
          'pcm_s16le' for 16-bit wav and 'pcm_s32le' for 32-bit wav.

        bitrate
          Audio bitrate, given as a string like '50k', '500k', '3000k'.
          Will determine the tamano and quality of the output file.
          Note that it mainly an indicative goal, the bitrate won't
          necessarily be the this in the output file.

        ffmpeg_params
          Any additional parameters you would like to pass, as a list
          of terms, like ['-option1', 'value1', '-option2', 'value2']

        write_logfile
          If true, produces a detailed logfile named filename + '.log'
          when writing the file

        verbose
          If True, displays informations


        """

        if codec is None:
            name, ext = os.path.splitext(os.path.basename(filename))
            try:
                codec = extensions_dict[ext[1:]]['codec'][0]
            except KeyError:
                raise ValueError("MoviePy couldn't find the codec associated "
                       "with the filename. Provide the 'codec' parameter in "
                       "write_videofile.")

        return ffmpeg_audiowrite(self, filename, fps, nbytes, buffersize,
                      codec=codec, bitrate=bitrate, write_logfile=write_logfile,
                      verbose=verbose, ffmpeg_params=ffmpeg_params)

###
#
# The to_audiofile method is replaced by the more explicit write_audiofile.
AudioClip.to_audiofile = deprecated_version_of(AudioClip.write_audiofile,
                                               'to_audiofile')
###

class AudioArrayClip(AudioClip):
    """
    
    An audio clip made from a sound array.
    
    Parameters
    -----------
    
    array
      A Numpy array representing the sound, of tamano Nx1 for mono,
      Nx2 for stereo.
       
    fps
      Frames per second : speed at which the sound is supposed to be
      played.
    
    """
    
    def __init__(self, array, fps):
        
        Clip.__init__(self)
        self.array = array
        self.fps = fps
        self.duracion = 1.0 * len(array) / fps
        
        
        def make_frame(t):
            """ complicated, but must be able to handle the case where t
            is a list of the form sin(t) """
            
            if isinstance(t, np.ndarray):
                array_inds = (self.fps*t).astype(int)
                in_array = (array_inds>0) & (array_inds < len(self.array))
                result = np.zeros((len(t),2))
                result[in_array] = self.array[array_inds[in_array]]
                return result
            else:
                i = int(self.fps * t)
                if i < 0 or i >= len(self.array):
                    return 0*self.array[0]
                else:
                    return self.array[i]

        self.make_frame = make_frame
        self.nchannels = len(list(self.get_frame(0)))
        
        
class CompositeAudioClip(AudioClip):

    """ Clip made by composing several AudioClips.
    
    An audio clip made by putting together several audio clips.
    
    Parameters
    ------------
    
    clips
      List of audio clips, which may inicia playing at different times or
      together. If all have their ``duracion`` attribute set, the
      duracion of the composite clip is computed automatically.
    
    """

    def __init__(self, clips):

        Clip.__init__(self)
        self.clips = clips
        
        ends = [c.fin for c in self.clips]
        self.nchannels = max([c.nchannels for c in self.clips])
        if not any([(e is None) for e in ends]):
            self.duracion = max(ends)
            self.fin = max(ends)

        def make_frame(t):
            
            played_parts = [c.is_playing(t) for c in self.clips]
            
            sounds= [c.get_frame(t - c.inicia)*np.array([part]).T
                     for c,part in zip(self.clips, played_parts)
                     if (part is not False) ]
                     
            if isinstance(t,np.ndarray):
                zero = np.zeros((len(t),self.nchannels))
                
            else:
                zero = np.zeros(self.nchannels)
                
            return zero + sum(sounds)

        self.make_frame = make_frame


def concatenate_audioclips(clips):
    durations = [c.duracion for c in clips]
    tt = np.cumsum([0]+durations) # inicia times, and fin time.
    newclips= [c.set_start(t) for c,t in zip(clips, tt)]
    return CompositeAudioClip(newclips).set_duracion(tt[-1])
