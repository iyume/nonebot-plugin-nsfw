"""Utilities vendor from nsfw-detector. Follow the MIT terms.

Vendor this library because:
1. dependency incorrect
2. need more parameter
"""
from __future__ import annotations

from io import BytesIO
from os import listdir
from os.path import abspath, exists, isdir, isfile, join

import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from keras.models import Model
from numpy.typing import NDArray
from PIL import Image
from tensorflow import keras

IMAGE_DIM = 224  # required/default image dimensionality


def load_images(image_paths, image_size: tuple[int, int], verbose=True):
    """
    Function for loading images into numpy arrays for passing to model.predict
    inputs:
        image_paths: list of image paths to load
        image_size: size into which images should be resized
        verbose: show all of the image path and sizes loaded

    outputs:
        loaded_images: loaded images on which keras model can run predictions
        loaded_image_indexes: paths of images which the function is able to process

    """
    loaded_images = []
    loaded_image_paths = []

    if isdir(image_paths):
        parent = abspath(image_paths)
        image_paths = [
            join(parent, f) for f in listdir(image_paths) if isfile(join(parent, f))
        ]
    elif isfile(image_paths):
        image_paths = [image_paths]

    for img_path in image_paths:
        try:
            if verbose:
                print(img_path, "size:", image_size)
            image = keras.preprocessing.image.load_img(img_path, target_size=image_size)
            image = keras.preprocessing.image.img_to_array(image)
            image /= 255
            loaded_images.append(image)
            loaded_image_paths.append(img_path)
        except Exception as ex:
            print("Image Load Failure: ", img_path, ex)

    return np.asarray(loaded_images), loaded_image_paths


def load_model(model_path: str) -> Model:
    if model_path is None or not exists(model_path):
        raise ValueError(
            "saved_model_path must be the valid directory of a saved model to load."
        )

    model = tf.keras.models.load_model(
        model_path, custom_objects={"KerasLayer": hub.KerasLayer}
    )
    return model


def classify(model: Model, input_paths, image_dim=IMAGE_DIM):
    """Classify given a model, input paths (could be single string), and image dimensionality...."""
    images, image_paths = load_images(input_paths, (image_dim, image_dim))
    probs = classify_nd(model, images)
    return dict(zip(image_paths, probs))


def classify_nd(model: Model, nd_images: NDArray[np.double]) -> list[dict[str, float]]:
    """Classify given a model, image array (numpy)...."""

    model_preds = model.predict(nd_images, verbose=0)
    # preds = np.argsort(model_preds, axis = 1).tolist()

    categories = ["drawings", "hentai", "neutral", "porn", "sexy"]

    probs = []
    for i, single_preds in enumerate(model_preds):
        single_probs = {}
        for j, pred in enumerate(single_preds):
            single_probs[categories[j]] = float(pred)
        probs.append(single_probs)
    return probs


def preprocess_pil(images: Image.Image | list[Image.Image]) -> NDArray[np.double]:
    if not isinstance(images, list):
        images = [images]
    res_images = []
    for image in images:
        # image = np.array(image.resize((IMAGE_DIM, IMAGE_DIM)), dtype=np.double)
        # image /= 255
        # above code turns into incorrect result
        # this is a trick to let keras load_img works
        # TODO: bytes version function
        image_stream = BytesIO()
        image.save(image_stream, "png")
        image = keras.preprocessing.image.load_img(
            image_stream, target_size=(IMAGE_DIM, IMAGE_DIM)
        )
        image = keras.preprocessing.image.img_to_array(image)
        image /= 255
        res_images.append(image)
    return np.asarray(res_images)


def classify_from_pil(model: Model, images: Image.Image | list[Image.Image]) -> bool:
    inputs = preprocess_pil(images)
    probs = classify_nd(model, inputs)
    has_nsfw = []
    for prob in probs:
        max_label = max(prob, key=prob.__getitem__)
        has_nsfw.append(max_label in ["hentai", "porn", "sexy"])
    return any(has_nsfw)
