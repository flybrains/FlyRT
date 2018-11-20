import cv2
import numpy as np
import math
from head_detector import get_head_point, crop_minAreaRect
from tracker import Detection

# def generate_patch(frame, centroid, patch):
#
#

def detect_blobs(frame, thresh, meas_last, meas_now, last_heads, colors):

	# Function to find valid fly contours and return centroid coordinates
	# Returns new meas_now tuple with error handling to return last valid one if
	# 	no good measurements found

	# Generate contours with no discrimination
	_, contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# Discriminate contours based on area percentage of total frame. Flies are generally between 0.001 and 0.01
	patches = []
	good_contours = []
	list_of_detections = []

	for i, contour in enumerate(contours):
			if ((cv2.contourArea(contour) / (thresh.shape[0]**2)) < 0.01) and ((cv2.contourArea(contour) / (thresh.shape[0]**2)) > 0.0001):
				good_contours.append(contour)

	# Second round of discrimination based on whether or not centroid is filled and if it is in masked "non-arena" area
	better_contours = []

	for i, contour in enumerate(good_contours):

		M = cv2.moments(contour)
		if M['m00'] != 0:

			cx = np.float16(M['m10']/M['m00'])
			cy = np.float16(M['m01']/M['m00'])

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

						detection = Detection()
						detection.add_centroid([cx,cy])

						try:

							ellipse = cv2.fitEllipse(contour)

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

							# Need to determine which between [fpx1, fpy1], [fpx2, fpy2]
							# is animal head, append along with cx, cy

							# Do disoriented patch coords
							# disoriented_patch = cv2.boundingRect(contour)
							#
							# # Make disoriented patch a bit bigger so full bigger animal can fit
							# scale_factor = 3
							# w = int(disoriented_patch[2]*scale_factor)
							# h = int(disoriented_patch[3]*scale_factor)
							#
							# dim = np.max([w,h])
							#
							# x = int((disoriented_patch[0]) - (dim - disoriented_patch[2])/2)
							# y = int((disoriented_patch[1]) - (dim -disoriented_patch[3])/2)
							#
							# # Grab pixels from these dims from color img:
							# patch = frame[y:(y+h), x:(x+h)]

							candidates = [[fpx1, fpy1], [fpx2, fpy2]]
							rect = cv2.minAreaRect(contour)
							patch, cd, pp, M = crop_minAreaRect(thresh.copy(), rect, candidates)


							# Take patch params and cd
							# Patch is the size of the larger threshold
							# Take dims of patch and get the smaller threshold
							# Smaaller one shoudl ahvea mostly white and a shifted oval uin teh cente  of the frame
							# Get centet of the shifted oval and see waht cd index it is closer  to
							# take this index and transfe r to candidate piointrs arrays
							# Copy this value and save as head point



							frame_low = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
							_, frame_low = cv2.threshold(frame_low, 75,255,0)
							frame_low = cv2.warpAffine(frame_low,M,(frame.shape[1],frame.shape[0]))

							patch_low = frame_low[pp[0]:pp[1], pp[2]:pp[3]]

							win = -1*(patch_low - patch - 255)
							win = np.expand_dims(win, 2)
							win = win.astype(np.uint8)

							_, contours, h = cv2.findContours(win, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

							main_dim_idx = win.shape[:2].index(max(win.shape[:2]))
							min_dim_idx = np.abs(main_dim_idx - 1)

							main = win.shape[:2][main_dim_idx]
							minor = win.shape[:2][min_dim_idx]

							half = int(main/2)

							# Tall case
							if main_dim_idx==0:
								half1, half2 = win[0:half,:], win[half:-1,:]
								half1_cent, half2_cent = (int(minor/2), int(half/2)), (int(minor/2), int(half*(1.5)))


							# Wide case
							if main_dim_idx==1:
								half1, half2 = win[:,0:half], win[:,half:-1]
								half1_cent, half2_cent = (int(half/2), int(minor/2)), (int(half*(1.5)), int(minor/2))

							win = cv2.cvtColor(win, cv2.COLOR_GRAY2BGR)

							win = cv2.circle(win, (half1_cent[0], half1_cent[1]), 3, (0,0,255), 3)
							win = cv2.circle(win, (half2_cent[0], half2_cent[1]), 3, (0,255, 0), 3)

							# Get B:W ratio for each half
							h1_ratio = (half1.shape[0]*half1.shape[1] - cv2.countNonZero(half1))/(half1.shape[0]*half1.shape[1])
							h2_ratio = (half2.shape[0]*half2.shape[1] - cv2.countNonZero(half2))/(half1.shape[0]*half1.shape[1])

							if h1_ratio > h2_ratio:
								head_side = half2_cent
							else:
								head_side = half1_cent

							dists = []
							for candidate in cd:
								head_side = np.asarray(head_side)
								candidate = np.asarray(candidate)
								dists.append(np.linalg.norm(candidate - head_side))
							col_idx = dists.index(min(dists))
							head_point = candidates[col_idx]

							# #for contour in contours:
							# win = cv2.drawContours(win,[cnt],-1,(0,0,255),3)



							#win = cv2.resize(frame_low, (0,0), fx=5, fy=5)

							#patches.append(win)

							# Generate minimum bounding rectangle around the larger contour
							#head_point, win = get_head_point(patch, [x,y], [cx, cy], [[fpx1, fpy1], [fpx2, fpy2]])

							#head_point = None

							detection.add_head(head_point)
							detection.add_area(area)



						except TypeError:
							detection.add_head(None)


					else:

						pass

		else:
			pass

		try:
			if (detection.head is None) and (detection.centroid is None):
				pass
			else:
				list_of_detections.append(detection)
		except UnboundLocalError:
			pass



	return list(set(list_of_detections)), len(better_contours), patches
