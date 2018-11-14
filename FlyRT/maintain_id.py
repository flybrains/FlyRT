import numpy as np



def minimum_distance(meas_now, meas_last, n_inds):

	# Check to see if the current point in meas_now
	# makes sense given the meas_last

	if len(meas_now)==len(meas_last):
		#
		# pos_distances = []
		# vel_distances = []

		# col_idxs = []
		#
		# for meas in meas_now:
		#
		# 	# Get x,y coords of current meas in loop
		# 	base_position = np.asarray(meas)
		# 	pos_sub_distances = [np.linalg.norm(base_position - np.asarray(meas_last[j])) for j in range(len(meas_now))]
		#
		# 	col_idx = pos_sub_distances.index(min(pos_sub_distances))
		# 	col_idxs.append(col_idx)
		#
		# 	pos_distances.append(pos_sub_distances)
		#
		# updated_meas_now = [meas_now[i] for i in col_idxs]

		state_distances = []

		col_idxs = []

		for meas in meas_now:

			base_state = np.asarray(meas)

			state_sub_distances = [np.linalg.norm(base_state - np.asarray(meas_last[j])) for j in range(len(meas_now))]

			col_idx = state_sub_distances.index(min(state_sub_distances))

			col_idxs.append(col_idx)

			state_distances.append(state_sub_distances)

		updated_meas_now = [meas_now[i] for i in col_idxs]


	elif len(meas_now) < len(meas_last):
		if len(meas_last) <= n_inds:
			updated_meas_now = meas_last


	return updated_meas_now

def check_impossible_moves(meas_now, meas_last, mm2pixel):

	movements = []

	if (len(meas_now) > len(meas_last)):
		meas_now = meas_now[0:len(meas_last)]

	elif (len(meas_now) < len(meas_last)):
		meas_now = meas_last

	else:
		pass

	for i in range(len(meas_now)):

		movement = np.linalg.norm(np.asarray(meas_now[i][0:2]) - np.asarray(meas_last[i][0:2]))
		movement = movement*mm2pixel
		movements.append(movement)

	print(movements)

	num_big_moves = len([1 for movement in movements if movement > 1.5])

	if num_big_moves >= 2:
		return [meas_now[1], meas_now[0]]
	else:
		return meas_now

def preserve_id(ifd, meas_now, meas_last, mm2pixel):

	if ifd > 0.5:
		return check_impossible_moves(meas_now, meas_last, mm2pixel)
	else:
		return meas_now
