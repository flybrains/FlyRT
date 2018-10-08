import numpy as np
import cv2

def generate_info_panel(frame, data_dict, vis_shape):

	max_pixel = 210*2

	if frame.shape[0]>max_pixel:
	    info = np.zeros((frame.shape[0], int((frame.shape[0])*0.5), 3), np.uint8)
	    padding=False
	else:
	    info = np.zeros((max_pixel, 220, 3), np.uint8)
	    pad = np.zeros((max_pixel - frame.shape[0], (frame.shape[0]), 3), np.uint8)
	    padding = True

	base = 80

	time_string = "  Trial Time: " + "{:.2f}".format(float(data_dict['frame_count']/30)) + "s"
	fps_string = "  Processing fps: " + "{:.2f}".format(data_dict['fps_calc'])

	log_string = "  Logging: " + str(data_dict['logging'])

	ifd_string = "Inter-Fly Distance: " +  "{:.2f}".format(data_dict['ifd']) + "pp"

	rec_string = "  Recording: " + str(data_dict['recording'])

	# h1_string = "Headings: "
	# h2_string = "  One-to-Two: " + "{:.2f}".format(data_dict['heading'][0])
	# h3_string = "  Two-to-One: " + "{:.2f}".format(data_dict['heading'][1])


	# ============================================================================================================
	info = cv2.putText(info, "FlySORT", (6, 24), cv2.FONT_HERSHEY_DUPLEX , 0.8, (0,255,0), 1, cv2.LINE_AA)

	info = cv2.putText(info, "System Information:", (10, base+5), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	info = cv2.putText(info, time_string, (10, base+20), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	info = cv2.putText(info, fps_string, (10, base+35), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	info = cv2.putText(info, log_string, (10, base+50), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	info = cv2.putText(info, rec_string, (10, base+65), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	info = cv2.putText(info, "------------", (10, base+80), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	info = cv2.putText(info, ifd_string, (10, base+95), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	info = cv2.putText(info, "------------", (10, base+110), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	# info = cv2.putText(info, h1_string, (10, base+125), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	# info = cv2.putText(info, h2_string, (10, base+140), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)
	# info = cv2.putText(info, h3_string, (10, base+155), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)

	info = cv2.putText(info, 'Video6', (10, base+155), cv2.FONT_HERSHEY_DUPLEX , 0.4, (0,255,0), 1, cv2.LINE_AA)

	# ============================================================================================================

	if padding==True:
		h1, w1 = frame.shape[:2]
		h2, w2 = pad.shape[:2]
		tile1 = np.zeros((max(h1, h2), w2, 3), np.uint8)

		tile1[:h1,:w1, :3] = frame

		h3, w3 = tile1.shape[:2]
		h4, w4 = info.shape[:2]

		vis = np.zeros((max(h3, h4), w3+w4,3), np.uint8)

		vis[:h3, :w3,:3] = tile1
		vis[:h4, w3:w3+w4,:3] = info

	else:
		h1, w1 = frame.shape[:2]
		h2, w2 = info.shape[:2]

		vis = np.zeros((max(h1, h2), w1+w2,3), np.uint8)

		vis[:h1, :w1,:3] = frame
		vis[:h2, w1:w1+w2,:3] = info


	if vis.shape != vis_shape:
		vis = cv2.resize(vis, (vis_shape[1], vis_shape[0]))

	return vis