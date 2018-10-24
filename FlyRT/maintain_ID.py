import numpy as np



def maintain_id(meas_now, meas_last, n_inds):

	# Check to see if the current point in meas_now
	# makes sense given the meas_last

	if len(meas_now)==len(meas_last):

		pos_distances = []
		vel_distances = []

		col_idxs = []

		for meas in meas_now:

			# Get x,y coords of current meas in loop
			base_position = np.asarray(meas)
			pos_sub_distances = [np.linalg.norm(base_position - np.asarray(meas_last[j])) for j in range(len(meas_now))]

			col_idx = pos_sub_distances.index(min(pos_sub_distances))
			col_idxs.append(col_idx)

			pos_distances.append(pos_sub_distances)


		updated_meas_now = [meas_now[i] for i in col_idxs]

		# if (np.var(pos_sub_distances) < 1000):

		# 	for meas in meas_now:
		# 		base_vel = np.asarray(meas[2:])
		# 		vel_sub_distances = [np.linalg.norm(base_vel - np.asarray(meas_last[j][2:])) for j in range(len(meas_now))]

		# 	col_idx = pos_sub_distances.index(min(vel_sub_distances))
		# 	col_idxs.append(col_idx)

		# 	vel_distances.append(vel_sub_distances)

		# updated_meas_now = [meas_now[i] for i in col_idxs]


	elif len(meas_now) < len(meas_last):
		if len(meas_last) <= n_inds:
			updated_meas_now = meas_last
				

	return updated_meas_now
