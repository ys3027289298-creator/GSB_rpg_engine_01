try:
    from pygame import mixer
except ImportError:
    mixer = None
import os
import time  # for the sleep functions


def play_song(song_path=""):
    if mixer is None:
        return
    try:
        mixer.init()
        mixer.music.load(os.path.normpath(song_path))
        mixer.music.play()

        while mixer.music.get_busy():
            time.sleep(10)

        mixer.music.stop()
    except Exception:
        # missing audio device or song file should never crash the game
        return

# play_song(glob("C:/Users/Kuda/Music/edIT Ants.mp3")[0])
# play_song("C:\\Users\\Kuda\\Documents\\Programming\\Python\\Campaign Creator\\Minecraft FULL SOUNDTRACK (2016).mp3")
