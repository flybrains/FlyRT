import numpy as np
import cv2

def get_head_point(patch, patch_corner, centroid, candidates):

	patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

	tlx, tly = patch_corner[0], patch_corner[1]

	_, high = cv2.threshold(patch, 142,255,0)
	_, low = cv2.threshold(patch, 95,255,0)

	win = -1*(low - high - 255)
	win = np.expand_dims(win, 2)
	win = win.astype(np.uint8)

	_, contours, _ = cv2.findContours(win, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	my_contours = []
	for contour in contours:
		M = cv2.moments(contour)
		area = cv2.contourArea(contour)
		framesize = win.shape[0]*win.shape[1]*0.8
		if (area > 25) and (area < framesize):
			cx = np.float16(M['m10']/M['m00'])
			cy = np.float16(M['m01']/M['m00'])
			my_contours.append([[cx, cy], cv2.contourArea(contour), contour])

	areas = [elem[1] for elem in my_contours]
	if len(areas) > 0:
		col_idx = areas.index(max(areas))
		my_contour = my_contours[col_idx]

		cx, cy = my_contour[0]
		back_centroid = np.asarray([(tlx + cx), (tly + cy)])

		point_dists = [np.linalg.norm(back_centroid - candidates[i]) for i in range(2)]
		head_idx = point_dists.index(max(point_dists))
		head_point = candidates[head_idx]
	else:
		head_point = np.nan


	return head_point
