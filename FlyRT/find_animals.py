import cv2
import numpy as np
import math

def detect_blobs(frame, thresh, meas_last, meas_now, colors):

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

		
	if len(meas_last)==len(meas_now):
		meas_last = meas_now.copy()
		del meas_now[:]

	# Second round of discrimination based on whether or not centroid is filled and if it is in masked "non-arena" area
	better_contours = []



	for i, contour in enumerate(good_contours):

		M = cv2.moments(contour)
		if M['m00'] != 0:

			cx = np.float16(M['m10']/M['m00'])
			cy = np.float16(M['m01']/M['m00'])
			#vx,vy, _, _ = cv2.fitLine(contours[i], cv2.DIST_L2,0,0.01,0.01)

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
				perim = cv2.arcLength(contour, True)
				window = thresh[(int(cy) - h):(int(cy) + h), (int(cx) - h):(int(cx) + h)]

				if np.mean(window) != np.nan:

					if (np.mean(window) > 60) and (np.mean(window) < 160):

						better_contours.append(contour)

					try:

						ellipse = cv2.fitEllipse(contour)

						rect = cv2.minAreaRect(contour)
						box = cv2.boxPoints(rect)
						box = np.int0(box)
						#new_frame = cv2.drawContours(frame,[box],0,(0,191,255),2)

						MAG = ellipse[1][1]*0.5
						mag = ellipse[1][0]*0.5

						ellipseAngle = math.radians(ellipse[-1])

						ellipseAngle = ellipseAngle - (math.pi/2)
						ellipseAngle2 = ellipseAngle - (math.pi)

						x_ang = math.degrees(math.cos(ellipseAngle))
						y_ang = math.degrees(math.sin(ellipseAngle))
						fpx1 = int(cx - MAG*math.radians(x_ang))
						fpy1 = int(cy - MAG*math.radians(y_ang))

						x_ang2 = math.degrees(math.cos(ellipseAngle2))
						y_ang2 = math.degrees(math.sin(ellipseAngle2))
						fpx2 = int(cx - MAG*math.radians(x_ang2))
						fpy2 = int(cy - MAG*math.radians(y_ang2))

						meas_now.append([[cx, cy], [fpx1, fpy1], [fpx2, fpy2]])


					except TypeError:


						meas_now.append([[cx, cy], [fpx1, fpy1], [fpx2, fpy2]])

					else:

						cx = 0
						cy = 0
						#vx,vy,_,_ = 0,0,0,0

	return contours, meas_last, meas_now, len(better_contours)
