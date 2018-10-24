def subtractor(crop, thresh_val):

	subtract = crop.copy()
	img = cv2.cvtColor(subtract, cv2.COLOR_BGR2GRAY)
	_, thresh_img = cv2.threshold(img, thresh_val, 255,0)

	thresh_img_og = thresh_img.copy()
	_, contours, _ = cv2.findContours(thresh_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	good_contours = []

	for i, contour in enumerate(contours):
		if ((cv2.contourArea(contour) / (crop.shape[0]**2)) < 0.01) and ((cv2.contourArea(contour) / (crop.shape[0]**2)) > 0.0001):
			good_contours.append(contour)


	better_contours = []
	subtractor = thresh_img.copy()
	for i, contour in enumerate(good_contours):

		M = cv2.moments(contour)
		if M['m00'] != 0:
			cx = int(M['m10']/M['m00'])
			cy = int(M['m01']/M['m00'])

		area = cv2.contourArea(contour)
		edge = int(np.sqrt(area))
		h = int(edge/2)
		window = thresh_img[(cy - h):(cy + h), (cx - h):(cx + h)]

		if np.mean(window) != np.nan:
			if (np.mean(window) > 60) and (np.mean(window) < 160):
				better_contours.append(contour)

		
		subtractor[(cy - edge):(cy + edge), (cx - edge):(cx + edge)] = 255


	thresh_img = cv2.cvtColor(thresh_img, cv2.COLOR_GRAY2BGR)
	thresh_img = cv2.drawContours(thresh_img, better_contours, -1, (0,0,255), 1)
	
	cv2.imwrite('subtractor.jpg', subtractor)
	cv2.imwrite('thresh_img.jpg', thresh_img_og)

	return subtractor
