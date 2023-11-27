from flask import Flask, render_template, request, send_file
import io
from PIL import Image
import cv2
import numpy as np
import zipfile


app = Flask(__name__)

imgBlue, imgBlur, imgDetail, imgDetailNoScratch, imgJustScratch, imgCombine, imgRestore, img, hg, histImg = None, None, None, None, None, None, None, None, None, None
MAX = 255
alpha = 0.5
beta = 0.0

def imHist(hist, scaleX=1, scaleY=1):
    maxVal = 0
    _, maxVal, _, _ = cv2.minMaxLoc(hist)
    rows = 64
    cols = hist.shape[0]
    histImg = np.zeros((int(rows*scaleX), int(cols*scaleY), 3), dtype=np.uint8)

    for i in range(cols - 1):
        histValue = hist[i]
        nextValue = hist[i + 1]
        pt1 = (int(i*scaleX), int(rows*scaleY))
        pt2 = (int(i*scaleX + scaleX), int(rows*scaleY))
        pt3 = (int(i*scaleX + scaleX), int((rows - nextValue * rows / maxVal)*scaleY))
        pt4 = (int(i*scaleX), int((rows - nextValue * rows / maxVal)*scaleY))

        pts = np.array([pt1, pt2, pt3, pt4], dtype=np.int32)
        pts = pts.reshape((-1, 1, 2))

        cv2.fillPoly(histImg, [pts], color=(255, 255, 255))

    return histImg

def remove_mask2(original_image):
    try:
        nparr = np.frombuffer(original_image.read(), np.uint8)
        if len(nparr) > 0:
            original_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if original_image is not None and not original_image.size == 0:
                global imgBlue, hg, histImg, img, imgBlur, imgDetail, imgJustScratch, imgDetailNoScratch, imgRestore    

                hist = cv2.calcHist([img], [0], None, [256], [0, 255])

                histImg = imHist(hist, 3, 3)

                imgBlur = cv2.medianBlur(original_image, 5)

                imgDetail = cv2.absdiff(original_image, imgBlur)

                _, imgJustScratch = cv2.threshold(imgDetail, 111, MAX, cv2.THRESH_BINARY)
                
                imgDetailNoScratch = cv2.subtract(imgDetail, imgJustScratch)

                imgRestore = cv2.addWeighted(imgBlur, 1.25, imgDetailNoScratch, 0.8, 0.5)

                return imgRestore
            else:
                print("Invalid image format or empty image.")
                return None  # or handle this case accordingly
        else:
            print("Empty or corrupt image file.")
            return None  # or handle this case accordingly
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None 



def remove_mask(original_image, hough_threshold, canny_threshold1, canny_threshold2):
    
    # Read the image
    nparr = np.frombuffer(original_image.read(), np.uint8)
    original_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # original_image = cv2.imread(image)

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

    # Save the binary mask
    inpaint = cv2.inpaint(original_image, line_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    
    # cv2.imshow("Result", inpaint)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return inpaint


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process-image', methods=['POST'])
def process_image():
    try:
        uploaded_file = request.files['imageFile']
        hough_threshold = int(request.form['houghThreshold'])
        canny_threshold1 = int(request.form['cannyThreshold1'])
        canny_threshold2 = int(request.form['cannyThreshold2'])

        if uploaded_file.filename != '':
            # Process the image
            processed_image1 = remove_mask(uploaded_file, hough_threshold, canny_threshold1, canny_threshold2)
            # processed_image2 = remove_mask2(uploaded_file)


            # _, img_encoded2 = cv2.imencode('.png', processed_image2)
            # img_byte_array2 = io.BytesIO(img_encoded2)

            # Return the processed images
            # return send_file(img_byte_array1, mimetype='image/png', as_attachment=True, download_name='processed_image1.png'), send_file(img_byte_array1, mimetype='image/png', as_attachment=True, download_name='processed_image2.png')

             # Create a zip file
            # Create a zip file
           # Create a zip file
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                # Write processed images to the zip buffer
                img1_content = cv2.imencode('.png', processed_image1)[1]
                zip_file.writestr('processed_image1.png', img1_content)
                zip_file.writestr('processed_image2.png', img1_content)


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

def process_image_function(uploaded_file):
    # Replace this with your actual image processing logic
    image = Image.open(uploaded_file)
    # Example: Convert the image to grayscale
    processed_image = image.convert('L')
    return processed_image

if __name__ == '__main__':
    app.run(debug=True)
