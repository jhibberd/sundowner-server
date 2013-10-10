
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

    // size the canvas
    ctx.canvas.width = size;
    ctx.canvas.height = size;

    // fill background
    var grd = ctx.createLinearGradient(0, 0, 0, size);
    grd.addColorStop(1, "#0099CC");
    grd.addColorStop(0, "#33B5E5");
    ctx.fillStyle = grd
    ctx.fillRect(0, 0, size, size);

    // box
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(size * .15, size * .15, size * .7, size * .4);

    // callout
    ctx.beginPath();
    ctx.moveTo((size / 2) - (size * .09), size * .54);
    ctx.lineTo((size / 2), size * .64);
    ctx.lineTo((size / 2) + (size * .09), size * .54);
    ctx.fill();

    // circle
    ctx.fillStyle = "#99CC00";
    ctx.beginPath();
    ctx.arc(
        size / 2, 
        size * .78, 
        size * .11, 
        0, 
        2 * Math.PI, 
        false);
    ctx.fill();
}

function openLogo() {
    var canvas = document.getElementById("canvas");
    var img = canvas.toDataURL("image/png");
    document.write('<img src="'+img+'"/>');
}

