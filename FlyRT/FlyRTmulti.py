import  numpy as np
import cv2
import sys
import time
from os import system
import os
import config
from datetime import datetime
import multiprocessing as mp

import FlyRTcore

def get_frame_max(img, process_max, process_min, n_processes):

	# Function to determine how many frames to keep per package given:
	# - Max frame for the current thread
	# - Start frame for current thread
	# - How many similar processes are running concurrently
	# Returns maximum number of frames before initiating new package

	# Frame range for entire thread
	expected_load = process_max - process_min

	# Amount of RAM to allocate to storing images in memory
	n_gb = 6
	n_bytes = img.nbytes
	frames_per_batch = ((1.0e9*n_gb)/n_processes)/n_bytes

	if frames_per_batch >= expected_load:

		frames_per_batch = expected_load

	return int(frames_per_batch)



def FlyRT_worker(cd, ind_low, ind_high, n_cores):

    FlyRTcore.run(cd, process_min=ind_low, process_max=ind_high, n_processes=n_cores)


def run(cd):

    print('Collecting Frame Count...')
    cap = cv2.VideoCapture('C:/Users/Patrick/Desktop/test1.mp4')
    n_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    print('Frame count: ', n_frames)

    n_cores = mp.cpu_count()

    cwd = os.getcwd()

    if 'frame_pkgs' in os.listdir(cwd):
        pass
    else:
        os.mkdir(cwd+'\\frame_pkgs')


    def good_division(n_frames, n_cores):

        indices = []

        tail = int(n_frames%(n_cores-1))

        complete_chunks = n_frames - tail
        start_index = 0

        if tail==0:
            chunk_size = int(complete_chunks/(n_cores))
            cores_used = n_cores
        else:
            chunk_size = int(complete_chunks/(n_cores-1))
            cores_used = n_cores-1


        for core in range(cores_used):
            indices.append([start_index, start_index+chunk_size])
            start_index = start_index + chunk_size

        if tail!=0:
            indices.append([start_index, (start_index + 2*chunk_size)])
        else:
            pass

        print(indices)

        return indices



    indices = good_division(n_frames, n_cores)



    processes = []
    for i in range(n_cores):
        p = mp.Process(target=FlyRT_worker, args=(cd, indices[i][0], indices[i][1], n_cores))

        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print('Finished Processing: Begin Splice')

    frames_save_dir = os.getcwd()+"/frame_pkgs"

    list_of_npys = os.listdir(frames_save_dir)

    mat = np.load(os.getcwd()+"\\"+'frame_pkgs'+"\\"+list_of_npys[0])
    vis = mat[0]

    dt = datetime.now()
    out = cv2.VideoWriter("generated_data/movies/"+str(dt.month)+"_"+str(dt.day)+"_"+str(dt.year)+"_"+str(dt.hour)+str(dt.minute)+'.avi', cv2.VideoWriter_fourcc(*'MJPG'), 30, (vis.shape[1], vis.shape[0]), True)

    for npy in list_of_npys:
        mat = np.load(os.getcwd()+"\\"+'frame_pkgs'+"\\"+npy)

        print('..')

        for i in range(mat.shape[0]):
            out.write(mat[i])



    out.release()
    return None



if __name__=='__main__':
    run()
