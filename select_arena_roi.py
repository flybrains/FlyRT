import cv2
import numpy as np
import numpy.ma as ma


def launch_GUI(input_vidpath):

	cap = cv2.VideoCapture(input_vidpath)

	ret, frame = cap.read()

	if ret==True:
		im = frame
	cap.release()

	r = cv2.selectROI(im, fromCenter=False)

	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)

	mask = np.ones((im.shape[0], im.shape[1]), np.uint8)
	mask = cv2.circle(mask, (cx,cy), int(r[3]/2), (255,255,255), -1)
	mask = (mask/255).astype(int).astype(bool)

	masked = im*mask[:,:,None]

	cv2.destroyAllWindows()

	cy = r[1] + int(r[3]/2)
	cx = r[0] + int(r[2]/2)

	spread = int(r[3]*(0.52))

	a = cx - spread
	b = cx + spread
	c = cy - spread
	d = cy + spread

	crop =  frame[c:d, a:b]

	return mask, r, crop

def mask_frame(frame, mask, r, mask_on=True, crop_on=True):

	if mask_on:
		new_frame = frame * mask[:,:,None]
	else:
		new_frame = frame


	if crop_on:
			cy = r[1] + int(r[3]/2)
			cx = r[0] + int(r[2]/2)

			spread = int(r[3]*(0.52))

			a = cx - spread
			b = cx + spread
			c = cy - spread
			d = cy + spread

			new_frame =  new_frame[c:d, a:b]


	return new_frame


