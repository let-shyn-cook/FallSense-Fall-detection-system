import numpy as np


def processing_data(features):

    # ***************************************** NORMALIZE ************************************
    def scale_pose(xy):
        """
        Normalize pose points by scale with max/min value of each pose.
        xy : (frames, parts, xy) or (parts, xy)
        """
        # Ensure input is 3D array (frames, parts, xy)
        if xy.ndim == 2:
            xy = np.expand_dims(xy, 0)
            
        # Get min/max values for x and y coordinates separately
        xy_min = np.nanmin(xy, axis=1, keepdims=True)
        xy_max = np.nanmax(xy, axis=1, keepdims=True)
        
        # Avoid division by zero
        xy_range = xy_max - xy_min
        xy_range[xy_range == 0] = 1
        
        # Normalize to [-1, 1] range
        xy_normalized = (xy - xy_min) / xy_range * 2 - 1
        return xy_normalized

    features = scale_pose(features)
    return features
