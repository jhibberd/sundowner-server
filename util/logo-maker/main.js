
function renderLogo() {

    var list = document.getElementById("logoType");
    var imageType = list.options[list.selectedIndex].value;

    switch (imageType) {
        case "iphone":
            drawLogo(57, true);
            break;
        case "iphone_retina":
            drawLogo(114, true);
            break;
        case "android_hdpi":
            drawLogo(72, false);
            break;
        case "android_mdpi":
            drawLogo(48, false);
            break;
        case "android_xhdpi":
            drawLogo(96, false);
            break;
        case "android_xxhdpi":
            drawLogo(144, false);
            break;
    }
};

function drawLogo(size, opaqueBackground) {

    var canvas = document.getElementById('canvas');
    var ctx = canvas.getContext('2d');

    // define circle center, radii and line width
    var circleCenterX =     size / 2;
    var circleCenterY =     size * .45;
    var circleRadius =      size * .25;
    var circleRadiusBig =   size * .37;
    var lineWidth =         size * .05;

    // size the canvas
    ctx.canvas.width = size;
    ctx.canvas.height = size;

    // fill background
    ctx.fillStyle = opaqueBackground ? '#ffffff' : 'rgba(0, 0, 0, 0)';
    ctx.fillRect(0, 0, size, size);

    // draw background column
    ctx.fillStyle = '#669900';
    ctx.beginPath();
    ctx.arc(
        circleCenterX, 
        circleCenterY, 
        circleRadiusBig, 
        1 * Math.PI, 
        2 * Math.PI, 
        false);
    ctx.lineTo(circleCenterX + circleRadiusBig, size);
    ctx.lineTo(circleCenterX - circleRadiusBig, size);
    ctx.fill();

    // draw circle
    ctx.fillStyle = '#99CC00';
    ctx.beginPath();
    ctx.arc(
        circleCenterX, 
        circleCenterY, 
        circleRadius, 
        0, 
        2 * Math.PI, 
        false);
    ctx.fill();

    // draw vertical line
    ctx.fillRect(
        circleCenterX - (lineWidth /2),
        circleCenterX + (lineWidth /2),
        lineWidth,
        size - circleCenterY);
}

function openLogo() {
    var canvas = document.getElementById("canvas");
    var img = canvas.toDataURL("image/png");
    document.write('<img src="'+img+'"/>');
}

