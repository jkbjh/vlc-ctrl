import vlc_ctrl.player
import dbus
import tempfile
import shutil
import contextlib
import json
import time


@contextlib.contextmanager
def save_replace(filename, *a, **kw):
    with tempfile.NamedTemporaryFile(*a, **kw) as file_like:
        yield file_like
        file_like.flush()
        shutil.copy(file_like.name, filename)


def left_remove(string, substring):
    if string.startswith(substring):
        return string[len(substring):]
    return string


class Player(object):
    def __init__(self,):
        self.player = vlc_ctrl.player.Player()
        self.reconnect()

    def reconnect(self):
        self.player.get_dbus_interface()

    def get_status(self):
        tracks = {track["trackid"]: (number, left_remove(track["path"], "file://")) for number, track in enumerate(self.player.get_tracks())}
        current_track = self.player.track_info()["trackid"]
        position = self.player.get_position()
        return dict(playlist=sorted(tracks.values()), current_track=tracks[current_track], position=position)

    def clear(self):
        for track in self.player.get_tracks():
            self.player._tracklist.RemoveTrack(track["trackid"])

    def reset(self, status):
        position = status["position"]
        playlist = status["playlist"]
        current_number, current_path = status["current_track"]
        for number, track in playlist:
            self.player._tracklist.AddTrack("file://" + track, dbus.ObjectPath("/"), current_number == number)
        self.player.set_position(position)
        time.sleep(0.01)
        curr_pos = self.player.get_position()
        if(abs(curr_pos - position) > 1):
            time.sleep(0.01)
            self.player.set_position(position)



class Manager(object):
    def __init__(self, filename):
        self.filename = filename

    def restore(self):
        with open(self.filename, "r") as f:
            status = json.load(f)
        p = Player()
        p.clear()
        time.sleep(0.01)
        p.reset(status)

    def watch(self, sleeptime=1):
        while True:
            p = Player()
            status = p.get_status()
            print("Storing status")
            with save_replace(self.filename) as f:
                json.dump(status, f)
            time.sleep(sleeptime)
