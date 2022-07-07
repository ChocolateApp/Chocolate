import subprocess, time, os, signal

moviesPath = "G:\Films-Series-Emissions\Films"
rewriteSlug = f"{moviesPath}\Barbaque.mkv"

filmEncode = None

def encode():
    global filmEncode
    if filmEncode != None:
        os.killpg(os.getpgid(filmEncode.pid), signal.SIGTERM)
    cmd = ['ffmpeg', '-i', f"{rewriteSlug}", '-g', '60', '-hls_time', '2', '-hls_list_size', '0', '-y', f'{moviesPath}\m3u8Files\movie.m3u8']
    filmEncode = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, preexec_fn=os.getpid) 

encode()
time.sleep(10)
encode()