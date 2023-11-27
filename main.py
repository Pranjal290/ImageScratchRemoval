from flask import Flask, render_template, request, send_file
import io
from PIL import Image
import cv2
import numpy as np
import zipfile


app = Flask(__name__)

MAX = 255

def remove_mask2(original_image):

    imgBlur = cv2.medianBlur(original_image, 5)
    imgDetail = cv2.absdiff(original_image, imgBlur)
    _, imgJustScratch = cv2.threshold(imgDetail, 111, MAX, cv2.THRESH_BINARY)
    imgDetailNoScratch = cv2.subtract(imgDetail, imgJustScratch)

    imgRestore = cv2.addWeighted(imgBlur, 1.25, imgDetailNoScratch, 0.8, 0.5)
    return imgRestore



def remove_mask1(original_image, hough_threshold, canny_threshold1, canny_threshold2):
    

    # Convert the image to grayscale
    gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)

    # Apply edge detection using Canny
    edges = cv2.Canny(gray_image, canny_threshold1, canny_threshold2, apertureSize=3)

    # Use Hough Line Transform to detect lines
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=hough_threshold)

    # Create a binary mask for the detected lines
    line_mask = np.zeros_like(edges)

    if lines is not None:
        for line in lines:
            rho, theta = line[0]
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho
            x1 = int(x0 + 1000 * (-b))
            y1 = int(y0 + 1000 * (a))
            x2 = int(x0 - 1000 * (-b))
            y2 = int(y0 - 1000 * (a))

            # Draw the line on the mask
            cv2.line(line_mask, (x1, y1), (x2, y2), 255, 3)

    # use inpaint to fill the mask
    inpaint = cv2.inpaint(original_image, line_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    processed_image2 = remove_mask2(inpaint)
    
    return inpaint, processed_image2


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        uploaded_file1 = request.files['imageFile']
        hough_threshold = int(request.form['houghThreshold'])
        canny_threshold1 = int(request.form['cannyThreshold1'])
        canny_threshold2 = int(request.form['cannyThreshold2'])

        if uploaded_file1.filename != '':

            # Read the image
            nparr = np.frombuffer(uploaded_file1.read(), np.uint8)
            original_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            # Process the image
            processed_image1, processed_image2 = remove_mask1(original_image, hough_threshold, canny_threshold1, canny_threshold2)
            

           # Create a zip file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                # Write processed images to the zip buffer
                img1_content = cv2.imencode('.png', processed_image1)[1]
                img2_content = cv2.imencode('.png', processed_image2)[1]
                zip_file.writestr('processed_image1.png', img1_content)
                zip_file.writestr('processed_image2.png', img2_content)


            # Prepare the zip file for download
            zip_buffer.seek(0)
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='processed_images.zip'
            )

    
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return "Error processing image", 500



if __name__ == '__main__':
    app.run(debug=True)
