
import numpy as np

class Track(object):
    def __init__(self, initial_detection):
        self.coords = [[initial_detection[0], initial_detection[1]]]

    def append_detection(self, detection):

        self.coords.append([detection[0], detection[1]])

        return None

    def get_coords(self):
        return self.coords[-1]


class Tracker(object):
    def __init__(self, n_inds, initial_meas_now):

        print(len(initial_meas_now))

        self.list_of_tracks = [Track(meas) for meas in initial_meas_now]

    def assign_detection(self, meas_now, ifd):

        detection_coords = [np.asarray([meas[0], meas[1]]) for meas in meas_now]

        if (len(self.list_of_tracks) == len(detection_coords)):

            for track in self.list_of_tracks:

                if len(detection_coords)==0:
                    track.append_detection(track.get_coords())

                else:
                    sub_dists = []
                    for i in range(len(detection_coords)):
                        sub_dists.append(np.linalg.norm(track.coords[-1] - detection_coords[i]))
                    col_idx = sub_dists.index(min(sub_dists))
                    track.append_detection(detection_coords[col_idx])

                    del detection_coords[col_idx]

        else:
            if len(self.list_of_tracks) < len(detection_coords):
                for i in range(len(detection_coords)):
                    sub_dists.append(np.linalg.norm(track.coords[-1] - detection_coords[i]))
                col_idx = sub_dists.index(max(sub_dists))

                del detection_coords[col_idx]

                for track in self.list_of_tracks:
                    sub_dists = []
                    for i in range(len(detection_coords)):
                        sub_dists.append(np.linalg.norm(track.coords[-1] - detection_coords[i]))
                    col_idx = sub_dists.index(min(sub_dists))
                    track.append_detection(detection_coords[col_idx])

                    del detection_coords[col_idx]

        return None
