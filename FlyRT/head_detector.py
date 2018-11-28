import numpy as np
import cv2
from tracker import Track

def get_moving_dir(list_of_tracks):

	targets = []

	for track in list_of_tracks:
		origin = track.get_cent_origin()
		next = track.get_mr_centroid()

		y_change = (next[1] - origin[1])/origin[1]
		x_change = (next[0] - origin[0])/origin[0]

		target_x = int(50*x_change) + origin[0]
		target_y = int(50*y_change) + origin[1]

		target = [target_x, target_y]

		targets.append(target)

	return targets




def get_head_point(patch, patch_corner, centroid, candidates, target):

	# patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)
	#
	# tlx, tly = patch_corner[0], patch_corner[1]
	#
	# _, high = cv2.threshold(patch, 142,255,0)
	# _, low = cv2.threshold(patch, 95,255,0)
	#
	# win = -1*(low - high - 255)
	# win = np.expand_dims(win, 2)
	# win = win.astype(np.uint8)
	#
	# _, contours, _ = cv2.findContours(win, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	# my_contours = []
	# for contour in contours:
	# 	M = cv2.moments(contour)
	# 	area = cv2.contourArea(contour)
	# 	framesize = win.shape[0]*win.shape[1]*0.8
	# 	if (area > 25) and (area < framesize):
	# 		cx = np.float16(M['m10']/M['m00'])
	# 		cy = np.float16(M['m01']/M['m00'])
	# 		my_contours.append([[cx, cy], cv2.contourArea(contour), contour])
	#
	# areas = [elem[1] for elem in my_contours]
	# if len(areas) > 0:
	# 	col_idx = areas.index(max(areas))
	# 	my_contour = my_contours[col_idx]
	#
	# 	cx, cy = my_contour[0]
	# 	back_centroid = np.asarray([(tlx + cx), (tly + cy)])
	#
	# 	point_dists = [np.linalg.norm(back_centroid - candidates[i]) for i in range(2)]
	# 	head_idx = point_dists.index(max(point_dists))
	# 	head_point = candidates[head_idx]
	# else:
	# 	head_point = np.nan
	#
	#
	# try:
	# 	win = cv2.circle(win, (int(cx),int(cy)), 3, (0,0,255), 4, cv2.LINE_AA)
	# except UnboundLocalError:
	# 	win = win


	target = np.asarray([target[0], target[1]])

	point_dists = [np.linalg.norm(target - candidates[i]) for i in range(2)]
	head_idx = point_dists.index(max(point_dists))
	head_point = candidates[head_idx]

	return head_point
