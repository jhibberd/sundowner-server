
function renderLogo() {

    var list = document.getElementById("logoType");
    var imageType = list.options[list.selectedIndex].value;

    switch (imageType) {

        case "iphone":
            drawLogo(57);
            break;
        case "iphone_retina":
            drawLogo(114);
            break;

        case "android_hdpi":
            drawLogo(72);
            break;
        case "android_mdpi":
            drawLogo(48);
            break;
        case "android_xhdpi":
            drawLogo(96);
            break;
        case "android_xxhdpi":
            drawLogo(144);
            break;

        case "facebook_s":
            drawLogo(16);
            break;
        case "facebook_m":
            drawLogo(75);
            break;
        case "facebook_l":
            drawLogo(128);
            break;
    }
};

function drawLogo(size) {

    var canvas = document.getElementById('canvas');
    var ctx = canvas.getContext('2d');

    // size the canvas
    ctx.canvas.width = size;
    ctx.canvas.height = size;

    // fill background
    ctx.fillStyle = "#33B5E5"
    ctx.fillRect(0, 0, size, size);

    var margin = size * .2;

    ctx.fillStyle = "#ffffff";
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#33B5E5";

    var cardHeight = parseInt(size * .45);
    var cardWidth = parseInt(size * (.45 * 1.618)); //.7);
    var cardOffset = parseInt(size * .05);

    var x = parseInt((size - ((cardOffset *2) + cardWidth)) / 2);
    var y = parseInt((size - ((cardOffset *2) + cardHeight)) / 2);

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

