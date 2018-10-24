import numpy as np
import cv2

def extract_image_patches(image, centroids, patch_shape, bw = False):
	patches = []
	patch_rets = []

	patch_width = patch_shape[0]
	patch_height = patch_shape[1]

	if len(centroids)==0:
		patch = np.ones(patch_shape)
		patches.append(patch)

	for centroid in centroids:
		c_x = centroid[0]
		c_y = centroid[1]
		
		if bw==False:
			img_x, img_y, _ = image.shape

		else:
			img_x, img_y = image.shape

		patch_Lx = (c_x - int(patch_width/2))
		patch_Ux = (c_x + int(patch_width/2))
		patch_Ly = (c_y - int(patch_height/2))
		patch_Uy = (c_y + int(patch_height/2))

		if (patch_Lx < 0) or (patch_Ly < 0) or (patch_Ux > img_x) or (patch_Uy > img_y):
			patch = np.ones(patch_shape)

		patch = image[patch_Ly:patch_Uy, patch_Lx:patch_Ux]

		
		if patch.shape==(40, 40, 3):
			patches.append(patch)
			patch_rets.append(True)
		else:
			patch = np.ones((40,40,3))
			patches.append(patch)
			patch_rets.append(True)

	return patches, patch_rets
