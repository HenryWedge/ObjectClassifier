import time

import numpy as np
from PIL import Image
from keras.api.preprocessing import image
from keras.src.applications.resnet_v2 import ResNet50V2, preprocess_input, decode_predictions, ResNet101V2, ResNet152V2

model = ResNet50V2(weights="imagenet")
ResNet101V2(weights="imagenet")
ResNet152V2(weights="imagenet")

img = Image.open("dog.jpg")
x = image.img_to_array(img.resize((224, 224), Image.Resampling.LANCZOS))
x = np.expand_dims(x, axis=0)
x = preprocess_input(x)
start_time = time.time()
preds = model.predict(x)
end_time = time.time()
prediction = decode_predictions(preds, top=3)[0][0][1]
