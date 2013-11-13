
function renderLogo() {

    var list = document.getElementById("logoType");
    var imageType = list.options[list.selectedIndex].value;

    switch (imageType) {

        case "iphone":
            drawLogo(57, 57, false);
            break;
        case "iphone_retina":
            drawLogo(114, 114, false);
            break;
        case "iphone_appstore":
            drawLogo(1024, 1024, false);
            break;
        case "iphone_app_120x120":
            drawLogo(120, 120, false);
            break;
        case "iphone_launch":
            drawLogo(640, 1136, false);
            break;

        case "android_hdpi":
            drawLogo(72, 72, false);
            break;
        case "android_mdpi":
            drawLogo(48, 48, false);
            break;
        case "android_xhdpi":
            drawLogo(96, 96, false);
            break;
        case "android_xxhdpi":
            drawLogo(144, 144, false);
            break;

        case "googleplay_512x512":
            drawLogo(512, 512, false);
            break;
        case "googleplay_1024x500":
            drawLogo(1024, 500, true);
            break;
        case "googleplay_180x120":
            drawLogo(180, 120, true);
            break;

        case "facebook_app_16x16":
            drawLogo(16, 16, false);
            break;
        case "facebook_app_64x64":
            drawLogo(64, 64, false);
            break;
        case "facebook_app_75x75":
            drawLogo(75, 75, false);
            break;
        case "facebook_app_96x96":
            drawLogo(96, 96, false);
            break;
        case "facebook_app_128x128":
            drawLogo(128, 128, false);
            break;

        case "facebook_banner_155x100":
            drawLogo(155, 100, true);
            break;
        case "facebook_banner_136x88":
            drawLogo(136, 88, true);
            break;
        case "facebook_banner_204x132":
            drawLogo(204, 132, true);
            break;
        case "facebook_banner_272x176":
            drawLogo(272, 176, true);
            break;
        case "facebook_banner_800x150":
            drawLogo(800, 150, true);
            break;

        case "facebook_pp":
            drawLogo(180, 180, false);
            break;
    }
};

var PRODUCT_NAME = "Soaptag";
var PRODUCT_NAME_LOGO_SHRINK_FACTOR = .8;

function drawLogo(w, h, showName) {

    var canvas = document.getElementById('canvas');
    var ctx = canvas.getContext('2d');
    ctx.canvas.width = w;
    ctx.canvas.height = h;

    // fill background
    ctx.fillStyle = "#33B5E5"
    ctx.fillRect(0, 0, w, h);

    ctx.fillStyle =     "#ffffff";
    ctx.lineWidth =     1;
    ctx.strokeStyle =   "#33B5E5";

    // center the logo within the canvas regardless of canvas shape or size
    var size = Math.min(w, h);
    var xOffset = size == w ? 0 : (w - h) / 2;
    var yOffset = size == h ? 0 : (h - w) / 2;

    // optionally show the product name in the logo
    if (showName) {

        var sf = PRODUCT_NAME_LOGO_SHRINK_FACTOR;
        ctx.font = (size * .13) + "px Helvetica Neue";
        ctx.textAlign = "center";
        ctx.fillText(PRODUCT_NAME, xOffset + (size / 2), yOffset + (size * sf));

        // if the product name is being rendered then shrink the size allocated
        // for the logo and adjust the x offset accordingly.
        var originalSize = size;
        size *= sf;
        xOffset += ((originalSize - size) / 2);
    }

    var cardHeight =    parseInt(size * .45);
    var cardWidth =     parseInt(size * (.45 * 1.618)); // golden ratio
    var cardOffset =    parseInt(size * .05);

    var x = xOffset + parseInt((size - ((cardOffset *2) + cardWidth)) / 2);
    var y = yOffset + parseInt((size - ((cardOffset *2) + cardHeight)) / 2);

    ctx.fillRect(   x + cardOffset *2, y + cardOffset *2, cardWidth, cardHeight);
    ctx.strokeRect( x + cardOffset *2, y + cardOffset *2, cardWidth, cardHeight);

    ctx.fillRect(   x + cardOffset *1, y + cardOffset *1, cardWidth, cardHeight);
    ctx.strokeRect( x + cardOffset *1, y + cardOffset *1, cardWidth, cardHeight);

    ctx.fillRect(   x + cardOffset *0, y + cardOffset *0, cardWidth, cardHeight);
    ctx.strokeRect( x + cardOffset *0, y + cardOffset *0, cardWidth, cardHeight);
}

function openLogo() {
    var canvas = document.getElementById("canvas");
    var img = canvas.toDataURL("image/png");
    document.write('<img src="'+img+'"/>');
}

