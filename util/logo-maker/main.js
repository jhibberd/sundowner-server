
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

function dot(x, y, ctx, size) {

    var s = parseInt(size * .07);
    var X = parseInt(size * .21);
    var Y = parseInt(size * .35);

    ctx.fillStyle = "#888";
    ctx.fillRect(X + (x * s), Y + (y * s), s, s);
}

function dot2(x, y, ctx, size) {

    var s = parseInt(size * .04);
    var X = parseInt(size * .21);
    var Y = parseInt(size * .65);

    ctx.fillStyle = "#0099CC";
    ctx.fillRect(X + (x * s), Y + (y * s), s, s);
}

function drawLogo(size, opaqueBackground) {

    var canvas = document.getElementById('canvas');
    var ctx = canvas.getContext('2d');

    // size the canvas
    ctx.canvas.width = size;
    ctx.canvas.height = size;

    // fill background
    ctx.fillStyle = "#33B5E5"
    ctx.fillRect(0, 0, size, size);

    var margin = size * .2;

    // box
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(size * .1, size * .2, size * .8, size * .6);

    dot(0, 0, ctx, size);
    dot(1, 0, ctx, size);
    dot(2, 0, ctx, size); //
    dot(3, 0, ctx, size);
    dot(4, 0, ctx, size); //
    dot(5, 0, ctx, size);
    dot(6, 0, ctx, size);
    dot(7, 0, ctx, size); //

    dot(0, 2, ctx, size);
    dot(1, 2, ctx, size); //
    dot(2, 2, ctx, size);
    dot(3, 2, ctx, size);
    dot(4, 2, ctx, size); //
    dot(5, 2, ctx, size);
    dot(6, 2, ctx, size);
    dot(7, 2, ctx, size);

    dot2(0, 0, ctx, size);
    dot2(1, 0, ctx, size);
    dot2(2, 0, ctx, size); //
    dot2(3, 0, ctx, size);
}

function openLogo() {
    var canvas = document.getElementById("canvas");
    var img = canvas.toDataURL("image/png");
    document.write('<img src="'+img+'"/>');
}

