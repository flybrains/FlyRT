import os
import cv2
import numpy as np


def run():
	frames_save_dir = "C:/Users/Patrick/FlyRT/FlyRT/frame_pkgs"

	list_of_npys = os.listdir(frames_save_dir)

	mat = np.load(os.getcwd()+"\\"+'frame_pkgs'+"\\"+list_of_npys[0])
	vis = mat[0]

	out = cv2.VideoWriter('test.avi', cv2.VideoWriter_fourcc(*'MJPG'), 30, (vis.shape[1], vis.shape[0]), True)

	for npy in list_of_npys:
		mat = np.load(os.getcwd()+"\\"+'frame_pkgs'+"\\"+npy)

		print('..')
		
		for i in range(mat.shape[0]):
			out.write(mat[i])


	out.release()

	return None

if __name__=='__main__':
	run()