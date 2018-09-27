
import cv2
import numpy as np
import numpy.ma as ma
import time
import flycapture2 as fc2
def flirGui(idx):


	cap = fc2.Context()
	cap.connect(*cap.get_camera_from_index(idx))
	cap.set_video_mode_and_frame_rate(fc2.VIDEOMODE_640x480Y8, fc2.FRAMERATE_30)
	m, f = cap.get_video_mode_and_frame_rate()
	p = cap.get_property(fc2.FRAME_RATE)
	cap.set_property(**p)
	cap.start_capture()
	img = fc2.Image()

	cap.retrieve_buffer(img)
	frame = np.array(img)

	im = frame.copy()

	im = np.expand_dims(im, 2)
	cap.stop_capture()
	cap.disconnect()

	r = cv2.selectROI(im, fromCenter=False)

	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)

	mask = np.ones((im.shape[0], im.shape[1]), np.uint8)
	mask = cv2.circle(mask, (cx,cy), int(r[3]/2), (255,255,255), -1)
	mask = (mask/255).astype(int).astype(bool)

	masked = im*mask[:,:,None]

	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)

	spread = int(r[3]*(0.52))

	a = cx - spread
	b = cx + spread
	c = cy - spread
	d = cy + spread

	crop =  im[c:d, a:b]

	cv2.destroyAllWindows()

	return mask, r, crop

