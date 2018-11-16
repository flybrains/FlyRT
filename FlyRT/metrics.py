import numpy as np

def ifd(centroids, old_ifds, scale_factor, mm2pixel, n_inds):
	try:
		ifds = []
		pos = [c for c in centroids]

		if n_inds == 2:
			ifds = np.linalg.norm(pos[0] - pos[1])*mm2pixel
		if n_inds == 3:
			ifds = [np.linalg.norm(pos[0] - pos[1])*mm2pixel, np.linalg.norm(pos[0] - pos[2])*mm2pixel, np.linalg.norm(pos[1] - pos[2])*mm2pixel]

	except IndexError:
		ifds = old_ifds

	return [ifds, ifds]

def relative_angle(meas_now, old_angles):
	# Draw line from animal centroid to other animal. This is baseline
	# Draw line directly based on heading
	# This metric is absolute angle between these 2 lines

	def angle_between_points( p0, p1, p2 ):

		a = (p1[0]-p0[0])**2 + (p1[1]-p0[1])**2
		b = (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2
		c = (p2[0]-p0[0])**2 + (p2[1]-p0[1])**2
		raw_angle = np.abs(np.arccos( (a+b-c) / np.sqrt(4*a*b) ) * 180/np.pi - 180)

		if raw_angle > 90:
			angle = 180 - raw_angle
		else:
			angle = raw_angle

		return angle

	try:
		animal_1_pos = (meas_now[0][0][0], meas_now[0][0][1])
		animal_1_dir = (meas_now[0][1][0], meas_now[0][1][1])

		animal_2_pos = (meas_now[1][0][0], meas_now[1][0][1])
		animal_2_dir = (meas_now[1][1][0], meas_now[1][1][1])

		one_to_two = angle_between_points(animal_1_dir, animal_1_pos, animal_2_pos)
		two_to_one = angle_between_points(animal_2_dir, animal_2_pos, animal_1_pos)

		angles = [one_to_two, two_to_one]

	except IndexError:
		angles = old_angles

	return angles, angles
