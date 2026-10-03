try:
    from pygame import mixer
except ImportError:
    mixer = None
import os
import sys
import time  # for the sleep functions


def play_song(song_path=""):
    if mixer is None:
        print("pygame is not installed; skipping music {!r}".format(song_path),
              file=sys.stderr)
        return
    if not os.path.exists(os.path.normpath(song_path)):
        print("Music file not found: {!r}".format(song_path), file=sys.stderr)
        return
    mixer.init()
    mixer.music.load(os.path.normpath(song_path))
    mixer.music.play()

    while mixer.music.get_busy():
        time.sleep(10)

    mixer.music.stop()

# play_song(glob("C:/Users/Kuda/Music/edIT Ants.mp3")[0])
# play_song("C:\\Users\\Kuda\\Documents\\Programming\\Python\\Campaign Creator\\Minecraft FULL SOUNDTRACK (2016).mp3")
