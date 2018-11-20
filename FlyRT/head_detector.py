import numpy as np
import cv2

def crop_minAreaRect(img, rect, candidates):

	# rotate img
	angle = rect[2]
	rows,cols = img.shape[0], img.shape[1]
	M = cv2.getRotationMatrix2D((cols/2,rows/2),angle,1)
	img_rot = cv2.warpAffine(img,M,(cols,rows))

	# rotate bounding box
	rect0 = (rect[0], rect[1], 0.0)
	box = cv2.boxPoints(rect)
	pts = np.int0(cv2.transform(np.array([box]), M))[0]

	cd = np.int0(cv2.transform(np.array([candidates]), M))
	cd = np.squeeze(cd)
	pts[pts < 0] = 0

	cd[0][0] = cd[0][0] - pts[1][0]
	cd[1][0] = cd[1][0] - pts[1][0]
	cd[0][1] = cd[0][1] - pts[1][1]
	cd[1][1] = cd[1][1] - pts[1][1]

	# crop
	img_crop = img_rot[pts[1][1]:pts[0][1], pts[1][0]:pts[2][0]]

	crop_params = [pts[1][1], pts[0][1], pts[1][0], pts[2][0]]

	# img_crop = cv2.cvtColor(img_crop, cv2.COLOR_GRAY2BGR)
	# img_rot = cv2.circle(img_crop, (cd[0][0], cd[0][1]), 3, (255,0,0), 4, cv2.LINE_AA)
	# img_rot = cv2.circle(img_crop, (cd[1][0], cd[1][1]), 3, (0,0,255), 4, cv2.LINE_AA)


	return img_crop, cd, crop_params, M


def get_head_point(patch, patch_corner, centroid, candidates):

	patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

	tlx, tly = patch_corner[0], patch_corner[1]
	_, high = cv2.threshold(patch, 150,255,0)
	_, low = cv2.threshold(patch, 45,255,0)
	win = -1*(low - high - 255)
	win = np.expand_dims(win, 2)
	win = win.astype(np.uint8)

	_, contours, _ = cv2.findContours(win, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	my_contours = []
	for contour in contours:
		M = cv2.moments(contour)
		area = cv2.contourArea(contour)
		framesize = win.shape[0]*win.shape[1]*0.8
		if (area > 25) and (area < framesize):
			cx = np.float16(M['m10']/M['m00'])
			cy = np.float16(M['m01']/M['m00'])
			my_contours.append([[cx, cy], cv2.contourArea(contour), contour])
			rect = cv2.minAreaRect(contour)
			img_cropped = crop_minAreaRect(win, rect)


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

	try:
		return head_point, img_cropped
	except UnboundLocalError:
		return head_point, np.ones(patch.shape)

def lower_thresh(patch):
	patch = cv2.cvtColor(patch, cv2.COLOR_BGR2GRAY)

	_, low = cv2.threshold(patch, 45,255,0)
	win = -1*(low - high - 255)
	win = np.expand_dims(win, 2)
	win = win.astype(np.uint8)
