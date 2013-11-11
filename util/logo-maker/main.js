
function renderLogo() {

    var list = document.getElementById("logoType");
    var imageType = list.options[list.selectedIndex].value;

    switch (imageType) {

        case "iphone":
            drawLogo(57, 57);
            break;
        case "iphone_retina":
            drawLogo(114, 114);
            break;
        case "iphone_appstore":
            drawLogo(1024, 1024);
            break;
        case "iphone_app_120x120":
            drawLogo(120, 120);
            break;
        case "iphone_launch":
            drawLogo(640, 1136);
            break;

        case "android_hdpi":
            drawLogo(72, 72);
            break;
        case "android_mdpi":
            drawLogo(48, 48);
            break;
        case "android_xhdpi":
            drawLogo(96, 96);
            break;
        case "android_xxhdpi":
            drawLogo(144, 144);
            break;

        case "facebook_app_16x16":
            drawLogo(16, 16);
            break;
        case "facebook_app_64x64":
            drawLogo(64, 64);
            break;
        case "facebook_app_75x75":
            drawLogo(75, 75);
            break;
        case "facebook_app_96x96":
            drawLogo(96, 96);
            break;
        case "facebook_app_128x128":
            drawLogo(128, 128);
            break;

        case "facebook_banner_155x100":
            drawLogo(155, 100);
            break;
        case "facebook_banner_136x88":
            drawLogo(136, 88);
            break;
        case "facebook_banner_204x132":
            drawLogo(204, 132);
            break;
        case "facebook_banner_272x176":
            drawLogo(272, 176);
            break;
        case "facebook_banner_800x150":
            drawLogo(800, 150);
            break;

        case "facebook_pp":
            drawLogo(180, 180);
            break;
    }
};

function drawLogo(w, h) {

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

