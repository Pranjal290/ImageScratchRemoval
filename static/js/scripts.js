$(document).ready(function() {
    // Event listener for the form submission
    $('#uploadForm').submit(function(e) {
        e.preventDefault();
    
        var formData = new FormData(this);
    
        fetch('/process-image', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Network response was not ok.');
        })
        .then(blob => {
            var reader = new FileReader();
            reader.onload = function(event) {
                var zip = new JSZip();
                zip.loadAsync(event.target.result)
                .then(function(zip) {
                    var img1Data = zip.file('processed_image1.png');
                    if (img1Data) {
                        img1Data.async('uint8array')
                        .then(function(data) {
                            var blob1 = new Blob([data], { type: 'image/png' });
                            document.getElementById('processedImage1').src = URL.createObjectURL(blob1);
                            document.getElementById('processedImage1').style.display = 'block';
                            document.getElementById('processedImageTitle1').style.display = 'block';
                        })
                        .catch(function(error) {
                            console.error('Error reading image1 data:', error);
                        });
                    } else {
                        console.error('Could not find processed_image1.png in the zip file.');
                    }
                    var img2Data = zip.file('processed_image2.png');
                    if (img2Data) {
                        img2Data.async('uint8array')
                        .then(function(data) {
                            var blob2 = new Blob([data], { type: 'image/png' });
                            document.getElementById('processedImage2').src = URL.createObjectURL(blob2);
                            document.getElementById('processedImage2').style.display = 'block';
                            document.getElementById('processedImageTitle2').style.display = 'block';
                        })
                        .catch(function(error) {
                            console.error('Error reading image2 data:', error);
                        });
                    } else {
                        console.error('Could not find processed_image2.png in the zip file.');
                    }
                })
                .catch(function(error) {
                    console.error('Error loading zip file:', error);
                });
            };
            reader.readAsArrayBuffer(blob);
        })
        .catch(error => console.error('Error:', error));
    });

    // Event listener for image upload change
    $('#uploadInput').on('change', function(e) {
        var reader = new FileReader();

        reader.onload = function(event) {
            var uploadedImageUrl = event.target.result;

            // Show the uploaded image
            $('#uploadedImage').attr('src', uploadedImageUrl).show();
            $('#uploadedImageTitle').show();
        }

        reader.readAsDataURL(e.target.files[0]);
    });

    // Event listener for slider input changes
    $('#houghThreshold').on('input', function() {
        $('#houghThresholdValue').text($(this).val());
    });

    $('#cannyThreshold1').on('input', function() {
        $('#cannyThreshold1Value').text($(this).val());
    });

    $('#cannyThreshold2').on('input', function() {
        $('#cannyThreshold2Value').text($(this).val());
    });
});
