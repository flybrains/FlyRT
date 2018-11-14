import numpy as np
import cv2


def draw_global_results(img, meas_now, colors, history, n_inds, DL = False, wings=False, traces=True, heading=True):

    for i in range(n_inds):
        if len(history)>0:
            try:
                new_frame = cv2.putText(img, str(i+1), (history[-1][i][0] + 5, history[-1][i][1] + 5), cv2.FONT_HERSHEY_DUPLEX , 0.8, colors[i], 1, cv2.LINE_AA)
            except IndexError:
                pass

        if traces==True:
            for centroid in history:
                if len(centroid)==n_inds:
                    new_frame = cv2.circle(img, (centroid[i][0], centroid[i][1]), 1, colors[i], 1, cv2.LINE_AA)
                else:
                    pass

        if heading==True:
            try:
                fpx1 = meas_now[i][1][0]
                fpy1 = meas_now[i][1][1]
                fpx2 = meas_now[i][2][0]
                fpy2 = meas_now[i][2][1]

                new_frame = cv2.line(img, (fpx1, fpy1), (fpx2, fpy2), colors[i], 1)
                new_frame = cv2.circle(img, (fpx1, fpy1), 3, (0,0,255), 4, cv2.LINE_AA)

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
