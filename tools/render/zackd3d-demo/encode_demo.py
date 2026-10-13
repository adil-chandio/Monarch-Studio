"""Encode frames/fNNNN.png -> zackd3d_demo_360p_12fps.mp4 using imageio-ffmpeg's bundled ffmpeg."""
import os
import subprocess
import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
OUT = os.path.join(HERE, 'zackd3d_demo_360p_12fps.mp4')

cmd = [
    FFMPEG, '-y', '-framerate', '12',
    '-i', os.path.join(HERE, 'frames', 'f%04d.png'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '20',
    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT,
]
subprocess.run(cmd, check=True)
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
