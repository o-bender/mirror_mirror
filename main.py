import face_recognition
from face_recognition.api import _raw_face_landmarks
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


def face_encodings(face_encoder, face_image, known_face_locations=None, num_jitters=1, model='large'):
    """
    Given an image, return the 128-dimension face encoding for each face in the image.
    :param face_image: The image that contains one or more faces
    :param known_face_locations: Optional - the bounding boxes of each face if you already know them.
    :param num_jitters: How many times to re-sample the face when calculating encoding. Higher is more accurate, but slower (i.e. 100 is 100x slower)
    :return: A list of 128-dimensional face encodings (one for each face in the image)
    """
    raw_landmarks = _raw_face_landmarks(face_image, known_face_locations, model=model)
    return [np.array(face_encoder.compute_face_descriptor(face_image, raw_landmark_set, num_jitters)) for raw_landmark_set in raw_landmarks]


def calibrate_adjust(gamma):
    cap = cv2.VideoCapture(0)
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


def train(face_encoder, person_name, images):
    if os.path.isdir(images):
        images = [os.path.join(images, file_name) for file_name in os.listdir(images)]
    elif os.path.isfile(images):
        images = [images]

    for image in images:
        known_image = face_recognition.load_image_file(image)
        # known_image = imutils.resize(known_image, width=500)
        for biden_encoding in face_encodings(face_encoder, known_image):
            person = Person(person_name, json.dumps((list(biden_encoding))))
            session.add(person)
    session.commit()


def run(face_encoder, models):
    cap = cv2.VideoCapture(0)

    try:
        while(True):
            ret, unknown_image = cap.read()
            unknown_image = adjust_gamma(unknown_image, args.adjust_gamma)

            # Искать прямоугольники (телефоны, рамки и т.п)
            # Если лицо внутри рамки, то это подставочка
            # print(find_phone(unknown_image))

            # known_image = face_recognition.load_image_file("aaiCMWZqifg.jpg")
            # known_image = imutils.resize(known_image, width=500)
            # biden_encoding = face_encodings(known_image)[0]

            # unknown_image = face_recognition.load_image_file("71lOOv_lN5A.jpg")
            # unknown_image = imutils.resize(unknown_image, width=500)
            unknown_encodings = face_encodings(face_encoder, unknown_image, model=args.predictor)

            for unknown_encoding in unknown_encodings:
                for model_name, model in models.items():
                    results = face_recognition.compare_faces(model, unknown_encoding)
                    # file_name = str(uuid.uuid1()) + str(results) + '.jpg'
                    # cv2.imwrite(file_name, unknown_image)
                    print(model_name)
                    print(results)
                    print(np.mean(results))
    except Exception as e:
        print(e)

    cap.release()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--predictor',    required=False, help="large or small", default="large")
    parser.add_argument('-m', '--model',        required=False, help="model name")
    parser.add_argument('-t', '--train',        required=False, help="train model name")
    parser.add_argument('-l', '--list-models',  required=False, help="list trained models", action='count')
    parser.add_argument('-r', '--remove-model', required=False, help="remove trained model", type=str)
    parser.add_argument('-i', '--images',       required=False, help="dir with images or list images")
    parser.add_argument('-g', '--adjust-gamma', required=False, help="set adjust gamma", type=float, default=1.0)
    parser.add_argument('-c', '--calibrate-adjust-gamma', required=False, help="show window for calibrate adjust gamma", action='count')

    args = parser.parse_args()

    face_recognition_model = face_recognition_models.face_recognition_model_location()
    face_encoder = dlib.face_recognition_model_v1(face_recognition_model)

    if args.train:
        train(face_encoder, args.train, args.images)
    elif args.calibrate_adjust_gamma:
        calibrate_adjust(args.adjust_gamma)
    else:
        if args.model:
            marks = [np.array(json.loads(mark.marks)) for mark in session.query(Person.marks).filter(Person.person == args.model).all()]
            run(face_encoder, {args.model: marks})
        else:
            models = {}
            for person in session.query(Person).all():
                if person.person not in models:
                    models[person.person] = []
                models[person.person].append(np.array(json.loads(person.marks)))
            run(face_encoder, models)