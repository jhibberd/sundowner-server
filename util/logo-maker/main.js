
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

    var COLOR_BACKGROUND =  '#b3def2';
    var COLOR_FOREGROUND =  '#33b5e5';
    var COLOR_SHADOW =      '#0099cc';
    var COLOR_DOT =         '#ffffff';
    var COLOR_TRANSPARENT = 'rgba(0, 0, 0, 0)';

    var colorBackground = opaqueBackground ? 
        COLOR_BACKGROUND : COLOR_TRANSPARENT;

    var canvas = document.getElementById('canvas');
    var ctx = canvas.getContext('2d');

    // size the canvas
    ctx.canvas.width = size;
    ctx.canvas.height = size;

    // fill background
    ctx.fillStyle = colorBackground;
    ctx.fillRect(0, 0, size, size);

    // define shadow
    ctx.save();
    ctx.shadowColor = COLOR_SHADOW;
    ctx.shadowOffsetX = 2;
    ctx.shadowOffsetY = 0;

    // draw marker
    var circleCenterX = size / 2;
    var circleCenterY = size * .4;
    var circleRadius = size * .25;
    ctx.fillStyle = COLOR_FOREGROUND;
    ctx.beginPath();
    ctx.arc(
        circleCenterX, 
        circleCenterY, 
        circleRadius, 
        0.8 * Math.PI, 
        0.2 * Math.PI, 
        false);
    ctx.lineTo(circleCenterX, size * .85);
    ctx.fill();
}

function openLogo() {
    var canvas = document.getElementById("canvas");
    var img = canvas.toDataURL("image/png");
    document.write('<img src="'+img+'"/>');
}

