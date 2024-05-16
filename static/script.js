// Function to validate IP address format
function isValidIP(ip) {
    const ipRegex = /^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.((25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.){2}(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$/;
    return ipRegex.test(ip);
}

function updateButtons() {
    $.getJSON('/list_images', function(data) {
        const hasImages = data.images.length > 0;
        $('#saveZipBtn').prop('disabled', !hasImages);
        $('#downloadGifBtn').prop('disabled', !hasImages);
        $('#downloadVideoBtn').prop('disabled', !hasImages);
        $('#clearImagesBtn').prop('disabled', !hasImages); // Disable/Enable Clear All Images button
    });

    const ip = $('#ipAddress').val();
    const interval = $('#interval').val();
    const validIP = isValidIP(ip);

    $('#startBtn').prop('disabled', !ip || !interval || !validIP);
    $('#stopBtn').prop('disabled', !ip || !interval || !validIP);
}

$(document).ready(function() {
    var running = false;
    var intervalId;
    var animatedImages = [];
    var animatedIndex = 0;
    var animationIntervalId;

    function updateAnimatedPreview() {
        $.getJSON('/list_images', function(data) {
            animatedImages = data.images;
            animatedImages.sort();
        });
    }

    function startAnimationLoop() {
        animationIntervalId = setInterval(function() {
            if (animatedImages.length > 0) {
                var image = animatedImages[animatedIndex];
                $("#videoPreview").attr('src', '/saved_images/' + image);
                animatedIndex = (animatedIndex + 1) % animatedImages.length;
            }
        }, 500); // Change this value to control the speed of the animated preview
    }

    $("#startBtn").click(function() {
        if (running) {
            return;
        }
        running = true;

        var interval = $("#interval").val() || 5;
        var startTime = $("#startTime").val();
        var endTime = $("#endTime").val();
        var ipAddress = $("#ipAddress").val();

        updateAnimatedPreview(); // Initial load
        startAnimationLoop(); // Start the animation loop

        $.get("/snapshot", { ip_address: ipAddress, start_time: startTime, end_time: endTime }, function(data) {
            $("#preview").attr("src", "data:image/jpg;base64," + data.image);
        });

        intervalId = setInterval(function() {
            $.getJSON('/snapshot', { ip_address: ipAddress, start_time: startTime, end_time: endTime }, function(data) {
                var imgData = 'data:image/jpeg;base64,' + data.image;
                $("#preview").attr('src', imgData);
            });
            
            updateAnimatedPreview(); // Update list of images periodically

        }, interval * 1000);
    });

    $("#stopBtn").click(function() {
        if (!running) {
            return;
        }
        running = false;
        clearInterval(intervalId);
        clearInterval(animationIntervalId); // Stop the animation loop
    });

    $("#saveZipBtn").click(function() {
        window.location.href = '/download_images';
    });

    $("#downloadGifBtn").click(function() {
        var frameRate = $("#frameRate").val();
        console.log("Downloading GIF with frame rate:", frameRate);
        window.location.href = '/download_gif?frame_rate=' + frameRate;
    });
    
    $("#downloadVideoBtn").click(function() {
        var frameRate = $("#frameRate").val();
        console.log("Downloading Video with frame rate:", frameRate);
        window.location.href = '/download_video?frame_rate=' + frameRate;
    });
    
    $("#clearImagesBtn").click(function() {
        $.get("/clear_images", function(data) {
            if (data.status === 'success') {
                alert("All images have been deleted.");
            } else {
                alert("Failed to delete images.");
            }
        });
    });
    
    $("#openDirBtn").click(function() {
        $.getJSON('/list_images', function(data) {
            var images = data.images;
            var imageList = "<ul>";
            images.forEach(function(image) {
                imageList += "<li>" + image + "</li>";
            });
            imageList += "</ul>";
            alert("Saved Images:\n" + imageList);
        });
    });
    // Initial button state update
    updateButtons();

    // Periodic button state update
    setInterval(updateButtons, 1000);

    // Listen for changes in IP and interval fields
    $('#ipAddress, #interval').on('input', updateButtons);    
});