import face_recognition
# from face_recognition.api import _raw_face_landmarks
from face_recognition.api import _raw_face_locations
import face_recognition_models
import numpy as np
import dlib
import cv2 
# import imutils
import time
import uuid
import argparse
from db_models import Person, session
import os
import json
import logging

formatter = logging.Formatter('%(asctime)-15s - %(message)s')

log = logging.getLogger('mirror')
log.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.DEBUG)
log.addHandler(sh)

face_detector = dlib.get_frontal_face_detector()

predictor_68_point_model = face_recognition_models.pose_predictor_model_location()
pose_predictor_68_point = dlib.shape_predictor(predictor_68_point_model)

predictor_5_point_model = face_recognition_models.pose_predictor_five_point_model_location()
pose_predictor_5_point = dlib.shape_predictor(predictor_5_point_model)

# cnn_face_detection_model = face_recognition_models.cnn_face_detector_model_location()
# cnn_face_detector = dlib.cnn_face_detection_model_v1(cnn_face_detection_model)

face_recognition_model = face_recognition_models.face_recognition_model_location()
face_encoder = dlib.face_recognition_model_v1(face_recognition_model)


def _raw_face_landmarks(face_image, face_locations=None, model="large"):
    face_locations = face_locations or _raw_face_locations(face_image)
    pose_predictor = {'small': pose_predictor_5_point, 'large': pose_predictor_68_point}[model]

    return [pose_predictor(face_image, face_location) for face_location in face_locations]


def face_encodings(face_image, face_locations=None, num_jitters=1, model='large'):
    """
    Given an image, return the 128-dimension face encoding for each face in the image.
    :param face_image: The image that contains one or more faces
    :param known_face_locations: Optional - the bounding boxes of each face if you already know them.
    :param num_jitters: How many times to re-sample the face when calculating encoding. Higher is more accurate, but slower (i.e. 100 is 100x slower)
    :return: A list of 128-dimensional face encodings (one for each face in the image)
    """
    raw_landmarks = _raw_face_landmarks(face_image, face_locations, model=model)
    return [np.array(face_encoder.compute_face_descriptor(face_image, raw_landmark_set, num_jitters)) for raw_landmark_set in raw_landmarks]


def calibrate_adjust(cap, gamma):
    # cap = cv2.VideoCapture(0)
    ret, image = cap.read()

    image = adjust_gamma(image, gamma)
    cv2.imshow('Calibrate adjust gamma', image)

    cap.release()
    cv2.waitKey()
    cv2.destroyAllWindows()


def adjust_gamma(image, gamma=1.0):
    # build a lookup table mapping the pixel values [0, 255] to
    # their adjusted gamma values
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
        for i in np.arange(0, 256)]).astype("uint8")
 
    # apply gamma correction using the lookup table
    return cv2.LUT(image, table)


def find_phone(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    edged = cv2.Canny(gray, 10, 250)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
    cnts = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]
    return cnts


def train(person_name, images):
    if os.path.isdir(images):
        images = [os.path.join(images, file_name) for file_name in os.listdir(images)]
    elif os.path.isfile(images):
        images = [images]

    for image in images:
        known_image = face_recognition.load_image_file(image)
        # known_image = imutils.resize(known_image, width=500)
        for biden_encoding in face_encodings(known_image):
            person = Person(person_name, json.dumps((list(biden_encoding))))
            session.add(person)
    session.commit()


def run(cap, models, gamma, predictor):
    # try:
        # while(True):
        ret, unknown_image = cap.read()
        unknown_image = adjust_gamma(unknown_image, gamma)

        # Искать прямоугольники (телефоны, рамки и т.п)
        # Если лицо внутри рамки, то это подставочка
        # log.info(find_phone(unknown_image))

        # known_image = face_recognition.load_image_file("aaiCMWZqifg.jpg")
        # known_image = imutils.resize(known_image, width=500)
        # biden_encoding = face_encodings(known_image)[0]

        # unknown_image = face_recognition.load_image_file("71lOOv_lN5A.jpg")
        # unknown_image = imutils.resize(unknown_image, width=500)
        _face_locations = _raw_face_locations(unknown_image)
        unknown_encodings = face_encodings(unknown_image, face_locations=_face_locations, model=predictor)
        for unknown_encoding in unknown_encodings:
            for model_name, model in models.items():
                results = face_recognition.compare_faces(model, unknown_encoding)
                # file_name = str(uuid.uuid1()) + str(results) + '.jpg'
                # cv2.imwrite(file_name, unknown_image)
                log.info(model_name)
                log.info(results)
                log.info(np.mean(results))
                if np.mean(results) > 0.7:
                    log.info(model_name)
                    yield model_name
    # except Exception as e:
    #     log.info(e)

    # cap.release()


def get_models():
    models = {}
    for person in session.query(Person).all():
        if person.person not in models:
            models[person.person] = []
        models[person.person].append(np.array(json.loads(person.marks)))
    return models


def get_cap():
    return cv2.VideoCapture(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--predictor',    required=False, help="large or small", default="large")
    parser.add_argument('-m', '--model',        required=False, help="model name")
    parser.add_argument('-l', '--list-models',  required=False, help="list trained models", action='count')
    parser.add_argument('-r', '--remove-model', required=False, help="remove trained model", type=str)

    parser.add_argument('-t', '--train',        required=False, help="train model name")
    parser.add_argument('-i', '--images',       required=False, help="dir with images or list images")

    parser.add_argument('-g', '--adjust-gamma', required=False, help="set adjust gamma", type=float, default=1.0)
    parser.add_argument('-c', '--calibrate-adjust-gamma', required=False, help="show window for calibrate adjust gamma", action='count')

    args = parser.parse_args()

    log.info('started')
    cap = get_cap()

    if args.train:
        train(args.train, args.images)
    elif args.calibrate_adjust_gamma:
        calibrate_adjust(cap, args.adjust_gamma)
    else:
        if args.model:
            marks = [np.array(json.loads(mark.marks)) for mark in session.query(Person.marks).filter(Person.person == args.model).all()]
            run(cap, {args.model: marks}, args.adjust_gamma, args.predictor)
        else:
            models = get_models()
            while True:
                list(run(cap, models, args.adjust_gamma, args.predictor))
