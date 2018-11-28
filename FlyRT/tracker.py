
import numpy as np

def linear_assingment(list_of_detections, list_of_tracks, full=False):

    if full==True:
        matrix = [[det.centroid[0],det.centroid[1], det.head[0], det.head[1]] for det in list_of_detections]

        for i, track in enumerate(list_of_tracks):
            sub_dists = []

            if (len(list_of_tracks)-i == 1) and (len(matrix)==1):
                track.append_centroid([matrix[0][0], matrix[0][1]])
                track.append_head([matrix[0][2], matrix[0][3]])
                track.append_meas_now()

            for new_det in matrix:
                mr_track_info = np.asarray([track.get_mr_centroid()[0], track.get_mr_centroid()[1], track.get_mr_head()[0], track.get_mr_head()[1]])
                current_track_info = np.asarray(new_det)
                sub_dists.append(np.linalg.norm(mr_track_info - current_track_info))

            col_idx = sub_dists.index(min(sub_dists))
            track.append_centroid([matrix[col_idx][0], matrix[col_idx][1]])
            track.append_head([matrix[col_idx][2], matrix[col_idx][3]])
            track.append_meas_now()
            matrix = [mat for i, mat in enumerate(matrix) if i!=col_idx]

    if full==False:
        matrix = [[det.centroid[0],det.centroid[1], det.head] for det in list_of_detections]


        for i,track in enumerate(list_of_tracks):
            sub_dists = []

            if (len(list_of_tracks)-i == 1) and (len(matrix)==1):
                track.append_centroid([matrix[0][0], matrix[0][1]])

                if None in matrix[0]:
                    track.append_head(track.get_mr_head())
                else:
                    track.append_head([matrix[0][2][0], matrix[0][2][1]])
                track.append_meas_now()

            for new_det in matrix:
                mr_track_info = np.asarray([track.get_mr_centroid()[0], track.get_mr_centroid()[1]])
                current_track_info = np.asarray(new_det[0:2])
                sub_dists.append(np.linalg.norm(mr_track_info - current_track_info))

            col_idx = sub_dists.index(min(sub_dists))

            track.append_centroid([matrix[col_idx][0], matrix[col_idx][1]])

            if None not in matrix[col_idx]:
                track.append_head([matrix[col_idx][2][0], matrix[col_idx][2][1]])
            else:
                track.append_head(track.get_mr_head())
            track.append_meas_now()
            matrix = [mat for i, mat in enumerate(matrix) if i!=col_idx]



class Detection(object):
    def __init__(self):
        pass
    def add_head(self, head_points):
        if head_points is not None:
            self.head = [int(point) for point in head_points]
        else:
            self.head = head_points
        return None
    def add_centroid(self, centroid_points):
        self.centroid = [int(point) for point in centroid_points]
        return None
    def add_area(self, area):
        self.area = area
        return None


class Track(object):
    def __init__(self, start_frame):
        self.counter = start_frame
        self.measurements = []
        self.meas_now = []
        return None

    def append_centroid(self, centroid):
        self.meas_now.append(centroid)
        return None

    def append_head(self, head):
        self.meas_now.append(head)
        return None

    def get_mr_centroid(self):
        return np.asarray(self.measurements[-1][0])

    def get_cent_origin(self):
        return np.asarray(self.measurements[-20][0])

    def get_mr_head(self):
        return np.asarray(self.measurements[-1][1])

    def append_meas_now(self):
        self.meas_now.append(self.counter)
        self.measurements.append(self.meas_now)
        self.meas_now = []


class Tracker(object):
    def __init__(self, n_inds, list_of_detections, start_frame):

        self.list_of_tracks = [Track(start_frame) for det in range(n_inds)]

        for i, track in enumerate(self.list_of_tracks):
            track.append_centroid(list_of_detections[i].centroid)
            if list_of_detections[i].head is not None:
                track.append_head(list_of_detections[i].head)
            else:
                track.append_head(list_of_detections[i].centroid)
            track.append_meas_now()


    def assign_detections(self, list_of_detections, n_inds):

        # Quick special case, if detection is empty, both pull from last good one
        if len(list_of_detections) == 0:
            for track in self.list_of_tracks:
                track.append_centroid(track.get_mr_centroid())
                track.append_head(track.get_mr_head())
                track.append_meas_now()

        # Standard case, do linear assignment cascade
        elif (len(list_of_detections) >= n_inds):

            # If new head measurement is available for all, make series of 4-element
            # arrays (x, y, hx, hy) and do linear assignment with tracks most recent
            # centroid and head
            not_nones = [1 for det in list_of_detections if (det.head is not None)]

            if (len(not_nones)==n_inds) and (len(list_of_detections)==n_inds):
                linear_assingment(list_of_detections, self.list_of_tracks, full=True)
            # If any new head measurements are missing or None, do linear assignment
            # with only centroid of tracks most recent centroid and head.
            # After assignments have been made, all tracks with pure head measurements
            # are updated, tracks with Nones assign last head value
            else:
                linear_assingment(list_of_detections, self.list_of_tracks, full=False)


        # If # of detection is less than n_inds, assign available detections
        # then update remaining tracks with their last good measure
        else:
            # if len(list_of_detections) < len(self.list_of_tracks):
            #     linear_assingment(list_of_detections, self.list_of_tracks, full=False)
            # else:
            for track in self.list_of_tracks:
                track.append_centroid(track.get_mr_centroid())
                track.append_head(track.get_mr_head())
                track.append_meas_now()


        return None
