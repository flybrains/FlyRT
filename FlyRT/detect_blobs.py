import cv2
import numpy as np

def detect_blobs(frame, thresh, meas_last, meas_now):

	# Function to find valid fly contours and return centroid coordinates
	# Returns new meas_now tuple with error handling to return last valid one if
	# 	no good measurements found

	# Generate contours with no discrimination
	_, contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# Discriminate contours based on area percentage of total frame. Flies are generally between 0.001 and 0.01
	good_contours = []

	for i, contour in enumerate(contours):

			if ((cv2.contourArea(contour) / (thresh.shape[0]**2)) < 0.01) and ((cv2.contourArea(contour) / (thresh.shape[0]**2)) > 0.0001):

				good_contours.append(contour)

	meas_last = meas_now.copy()
	del meas_now[:]


	# Second round of discrimination based on whether or not centroid is filled and if it is in masked "non-arena" area
	better_contours = []

	for i, contour in enumerate(good_contours):

		M = cv2.moments(contour)

		if M['m00'] != 0:

			cx = int(M['m10']/M['m00'])
			cy = int(M['m01']/M['m00'])
			vx,vy, _, _ = cv2.fitLine(contours[i], cv2.DIST_L2,0,0.01,0.01)

			center_coords = np.asarray([int(frame.shape[0]/2), int(frame.shape[1]/2)])
			dist_to_center = np.linalg.norm(center_coords - np.asarray([cx,cy]))

			if (dist_to_center > (frame.shape[0]/2)):

				pass

			elif [int(cx), int(cy)] in [[0,0], [0, frame.shape[0]], [frame.shape[0],0], []]:

				pass

			else:

				# Check whether contour is mostly filled or not
				area = cv2.contourArea(contour)
				edge = int(np.sqrt(area))
				h = int(edge/2)
				window = thresh[(cy - h):(cy + h), (cx - h):(cx + h)]

				if np.mean(window) != np.nan:

					if (np.mean(window) > 60) and (np.mean(window) < 160):

						better_contours.append(contour)

					try:

						meas_now.append([cx, cy, vx[0], vy[0]])

					except TypeError:

						meas_now.append([cx, cy, vx, vy])

					else:

						cx = 0
						cy = 0
						vx,vy,_,_ = 0,0,0,0

	return contours, meas_last, meas_now, len(better_contours)
