import numpy as np
import cv2


def process_image(img, size):
    """Resize an image by cropping and scaling to size :param: size.

    Parameters
    ----------
    img: array_like (N x M x 3)
        A 2D colored image with color range [0, 255].
    size: int
        The size of the returned image.

    Returns
    -------
    array_like (1 x :param: size x :param: size, 3)
        A 2D image, with 1 batch dimension, of size :param: size and 3 color channels normalized in range [-1, 1].
    """
    if np.max(img.shape[:2]) != size:
        scale = float(size) / np.max(img.shape[:2])
    else:
        scale = 1.0
    center = np.round(np.array(img.shape[:2]) / 2).astype(int)
    center = center[::-1]  # image center in (x,y)

    crop, proc_param = scale_and_crop(img, scale, center, size)

    # Normalize image to [-1, 1]
    crop = 2 * ((crop / 255.0) - 0.5)

    # Add batch dimension: 1 x D x D x 3
    return np.expand_dims(crop, 0), proc_param


def scale_and_crop(image, scale, center, size):
    image_scaled, scale_factors = resize_img(image, scale)

    scale_factors = [scale_factors[1], scale_factors[0]]  # swap so it's [x, y]
    center_scaled = np.round(center * scale_factors).astype(np.int)

    margin = int(size / 2)
    image_pad = np.pad(image_scaled, ((margin,), (margin,), (0,)), mode="edge")
    center_pad = center_scaled + margin
    # figure out starting point
    start_pt = center_pad - margin
    end_pt = center_pad + margin
    # crop:
    crop = image_pad[start_pt[1] : end_pt[1], start_pt[0] : end_pt[0], :]
    proc_param = {
        "scale": scale,
        "start_pt": start_pt,
        "end_pt": end_pt,
        "img_size": size,
    }

    return crop, proc_param


def resize_img(img, scale_factor):
    new_size = (np.floor(np.array(img.shape[0:2]) * scale_factor)).astype(int)
    new_img = cv2.resize(img, (new_size[1], new_size[0]))
    # This is scale factor of [height, width] i.e. [y, x]
    actual_factor = [
        new_size[0] / float(img.shape[0]),
        new_size[1] / float(img.shape[1]),
    ]
    return new_img, actual_factor
