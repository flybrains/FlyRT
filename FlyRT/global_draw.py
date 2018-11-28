import numpy as np
import cv2


def draw_global_results(img, cent_meas, head_meas, colors, history, n_inds, targets, traces=True, heading=True):


    for i in range(n_inds):
        if len(history)>0:
            try:
                new_frame = cv2.putText(img, str(i+1), (history[-1][i][0] + 5, history[-1][i][1] + 5), cv2.FONT_HERSHEY_DUPLEX , 0.8, colors[i], 1, cv2.LINE_AA)
            except IndexError:
                pass

        # if targets[0] is not None:
        #     new_frame = cv2.circle(img, (targets[i][0], targets[i][1]), 10, (255,0,0), 10, cv2.LINE_AA)


        if traces==True:
            for centroid in history:
                if len(centroid)==n_inds:
                    new_frame = cv2.circle(img, (int(centroid[i][0]), int(centroid[i][1])), 1, colors[i], 1, cv2.LINE_AA)


                else:
                    pass

        if heading==True:
            try:
                head_x = head_meas[i][0]
                head_y = head_meas[i][1]


                #new_frame = cv2.line(img, (int(centroid[i][0]), int(centroid[i][1])), (int(head_x), int(head_y)), colors[i], 1)
                new_frame = cv2.circle(img, (int(head_x), int(head_y)), 3, (0,0,255), 4, cv2.LINE_AA)

            except IndexError:
                    pass

    return new_frame



def add_thumbnails(img, patches, results, colors, wings=False):
    patch_list = []

    for idx, idv in enumerate(results):
        tail = (idv[3][0], idv[3][1])

        new_patch = cv2.putText(patches[idx], str(idx), (10, 20), cv2.FONT_HERSHEY_DUPLEX , 0.8, colors[idx], 1, cv2.LINE_AA)
        patch_list.append(new_patch)

    if len(patch_list) != 0:
      frames = patch_list[0]
      for patch in patch_list[1:]:
          frames = np.concatenate((frames, patch), axis=1)

    img[0:frames.shape[0], 0:frames.shape[1]] = frames

    return img
