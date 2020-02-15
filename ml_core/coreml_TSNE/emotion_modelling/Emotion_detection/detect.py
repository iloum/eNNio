import numpy as np
import argparse
import cv2
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import sys
from pathlib import Path
import tqdm



# command line argument

def plot_model_history(model_history):
    """
    Plot Accuracy and Loss curves given the model_history
    """
    fig, axs = plt.subplots(1,2,figsize=(15,5))
    # summarize history for accuracy
    axs[0].plot(range(1,len(model_history.history['acc'])+1),model_history.history['acc'])
    axs[0].plot(range(1,len(model_history.history['val_acc'])+1),model_history.history['val_acc'])
    axs[0].set_title('Model Accuracy')
    axs[0].set_ylabel('Accuracy')
    axs[0].set_xlabel('Epoch')
    axs[0].set_xticks(np.arange(1,len(model_history.history['acc'])+1),len(model_history.history['acc'])/10)
    axs[0].legend(['train', 'val'], loc='best')
    # summarize history for loss
    axs[1].plot(range(1,len(model_history.history['loss'])+1),model_history.history['loss'])
    axs[1].plot(range(1,len(model_history.history['val_loss'])+1),model_history.history['val_loss'])
    axs[1].set_title('Model Loss')
    axs[1].set_ylabel('Loss')
    axs[1].set_xlabel('Epoch')
    axs[1].set_xticks(np.arange(1,len(model_history.history['loss'])+1),len(model_history.history['loss'])/10)
    axs[1].legend(['train', 'val'], loc='best')
    fig.savefig('plot.png')
    plt.show()

def create_model():

    num_train = 28709
    num_val = 7178
    batch_size = 64
    num_epoch = 50

    # Create the model
    model = Sequential()

    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48,48,1)))
    model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Flatten())
    model.add(Dense(1024, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(7, activation='softmax'))

    print("now detecting emotions")
    model.load_weights(str(os.path.join(os.path.dirname(__file__),'model/model.h5')))

    return model



def predict_emotion(file,model,step=0.1,show_processing=False):
    # Define data generators
    train_dir = 'data/train'
    val_dir = 'data/test'

    # prevents openCL usage and unnecessary logging messages
    cv2.ocl.setUseOpenCL(False)



    # dictionary which assigns each label an emotion (alphabetical order)
    emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}

    emotion_predictions=[]


    # start the webcam feed
    capture = cv2.VideoCapture(str(file))

    n_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = capture.get(cv2.CAP_PROP_FPS)
    duration, next_timestamp_proc = n_frames / fps, 0.0
    frames_to_process = int(duration/step)
    pbar = tqdm.tqdm(total=frames_to_process)
    features_all, timestamps, count = [], [], 0
    facecasc = cv2.CascadeClassifier(str(os.path.join(os.path.dirname(__file__),'haarcascade_frontalface_default.xml')))

    while True:
        ret, frame = capture.read()
        timestamp = float(count) / fps
        if timestamp >= next_timestamp_proc:
            next_timestamp_proc += step;
            PROCESS_NOW = True
        if ret:
            count += 1
            if PROCESS_NOW:
                timestamps.append(timestamp)
                pbar.update(1)
                # Find haar cascade to draw bounding box around face
                if not ret:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = []
                faces = facecasc.detectMultiScale(gray,scaleFactor=1.3, minNeighbors=5)

                if len(faces)==0:
                    emotion_predictions.append(None)
                    #print(faces)

                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y-50), (x+w, y+h+10), (255, 0, 0), 2)
                    roi_gray = gray[y:y + h, x:x + w]
                    cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray, (48, 48)), -1), 0)
                    prediction = model.predict(cropped_img)
                    maxindex = int(np.argmax(prediction))
                    emotion_predictions.append(emotion_dict[maxindex])

                if show_processing:
                    cv2.putText(frame, emotion_dict[maxindex], (x+20, y-60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.imshow('Video', cv2.resize(frame,(1600,960),interpolation = cv2.INTER_CUBIC))
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                PROCESS_NOW = False
        else:
            break

    capture.release()
    print("made %i "%(len([x for x in emotion_predictions if x])),"detections")
    #cv2.destroyAllWindows()
    # None statds for no feature descriptions
    return [emotion_predictions,None]

def generate_emotionfeatures(path):
    model=create_model()
    emotions_dict={}
    if os.path.isdir(path):
        emotions_dict={}
        for file_path in Path(path).glob('*.mp4'):
            print(file_path)
            try:
                emotions_dict[str(file_path)]=predict_emotion(file_path,model)
            except:
                pass
    elif os.path.isfile(path):
        print("initializing emotion detector")
        return predict_emotion(path,model)
    return emotions_dict

if __name__=="__main__":
    model=create_model()
    print("initializing emotion detector")
    predict_emotion(sys.argv[1],model,True)
