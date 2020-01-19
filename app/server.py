# import libraries
print('importing libraries...')
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_dropzone import Dropzone
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
import logging
import random
import time

from PIL import Image
import requests, os
from io import BytesIO

from predict import Resnet152Model

# import settings
from settings import * # import 

print('done!\nlaunching the server...')

# set flask params

app = Flask(__name__)
dropzone = Dropzone(app)

print(os.getcwd())
# Uploads settings
app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd() + '/app/uploads'
app.config['DROPZONE_UPLOAD_MULTIPLE'] = False
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image/*'
app.config['DROPZONE_REDIRECT_VIEW'] = 'results'
photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB

# model
resnet_model = Resnet152Model('app/')

# @app.route("/")
# def hello():
#     return "Image classification example\n"

# https://medium.com/@dustindavignon/upload-multiple-images-with-python-flask-and-flask-dropzone-d5b821829b1d
@app.route('/', methods=['GET', 'POST'])
def index():
    # set session for image results
    if "file_urls" not in session:
        session['file_urls'] = []
    # list to hold our uploaded image urls
    file_urls = session['file_urls']

    if request.method == 'POST':
        file_obj = request.files
        for f in file_obj:
            file = request.files.get(f)
            print (file.filename)

            t = time.time() # get execution time

            # request.files['photo'].save('test.jpg')
            filename = photos.save(
                file,
                folder='photos',
                name=file.filename    
            )
            # append image urls
            print(f'saving to {photos.url(filename)}')
            file_urls.append(photos.url(filename))

            class_name, class_probability = resnet_model.predict(Image.open(file))

            dt = time.time() - t
            app.logger.info("Execution time: %0.02f seconds" % (dt))

            prediction = f'Predicted {class_name} with a probability of {round(class_probability,4)*100}%'
            print(prediction)

        session['file_urls'] = file_urls
        session['prediction'] = prediction
        return "uploading and predicting..."
    return render_template('index.html')

@app.route('/results')
def results():
    # redirect to home if no images to display
    if "file_urls" not in session or session['file_urls'] == []:
        return redirect(url_for('index'))
        
    # set the file_urls and remove the session variable
    file_urls = session['file_urls']
    session.pop('file_urls', None)

    prediction = session['prediction']
    session.pop('prediction', None)

    return render_template('results.html', file_urls=file_urls, prediction=prediction)

@app.route('/predict', methods=['GET'])
def predict():
    
    # response = requests.get(url)
    # img = open_image(BytesIO(response.content))
    img = None

    t = time.time() # get execution time

    class_name, class_probability = resnet_model.predict(img)

    dt = time.time() - t
    app.logger.info("Execution time: %0.02f seconds" % (dt))

    print(f'predicting {class_name} with a probability of {round(class_probability,4)*100}%')

    return jsonify({"class_name": class_name, "class_probability": class_probability})

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'memcached'
    app.run(host="0.0.0.0", debug=True, port=PORT)
