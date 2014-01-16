
function renderLogo() {

    var list = document.getElementById("logoType");
    var imageType = list.options[list.selectedIndex].value;

    // default rendering options
    var opts = {
        width:                          undefined,
        height:                         undefined,
        showName:                       false,
        backgroundColor:                "#33B5E5",
        foregroundColor:                "#FFFFFF",
        cardScale:                      .45,
        nameScale:                      .2,
        fontScale:                      .13,
        crop:                           false
    };

    switch (imageType) {

        // iPhone App ----------------------------------------------------------
        case "iphone":
            opts.width =                57;
            opts.height =               57;
            break;
        case "iphone_retina":
            opts.width =                114;
            opts.height =               114;
            break;
        case "iphone_appstore":
            opts.width =                1024;
            opts.height =               1024;
            break;
        case "iphone_app_120x120":
            opts.width =                120;
            opts.height =               120;
            break;
        case "iphone_launch":
            opts.width =                640;
            opts.height =               1136;
            break;

        // Android App ---------------------------------------------------------
        case "android_hdpi":
            opts.width =                72;
            opts.height =               72;
            break;
        case "android_mdpi":
            opts.width =                48;
            opts.height =               48;
            break;
        case "android_xhdpi":
            opts.width =                96;
            opts.height =               96;
            break;
        case "android_xxhdpi":
            opts.width =                114;
            opts.height =               114;
            break;

        // Google Play Store ---------------------------------------------------
        case "googleplay_512x512":
            opts.width =                512;
            opts.height =               512;
            break;
        case "googleplay_1024x500":
            opts.width =                1024;
            opts.height =               500;
            opts.showName =             true;
            break;
        case "googleplay_180x120":
            opts.width =                180;
            opts.height =               120;
            opts.showName =             true;
            break;

        // Facebook App --------------------------------------------------------
        case "facebook_app_16x16":
            opts.width =                16;
            opts.height =               16;
            break;
        case "facebook_app_64x64":
            opts.width =                64;
            opts.height =               64;
            break;
        case "facebook_app_75x75":
            opts.width =                75;
            opts.height =               75;
            break;
        case "facebook_app_96x96":
            opts.width =                96;
            opts.height =               96;
            break;
        case "facebook_app_128x128":
            opts.width =                128;
            opts.height =               128;
            break;

        // Facebook Banner -----------------------------------------------------
        case "facebook_banner_155x100":
            opts.width =                155;
            opts.height =               100;
            opts.showName =             true;
            break;
        case "facebook_banner_136x88":
            opts.width =                136;
            opts.height =               88;
            opts.showName =             true;
            break;
        case "facebook_banner_204x132":
            opts.width =                204;
            opts.height =               132;
            opts.showName =             true;
            break;
        case "facebook_banner_272x176":
            opts.width =                272;
            opts.height =               176;
            opts.showName =             true;
            break;
        case "facebook_banner_800x150":
            opts.width =                800;
            opts.height =               150;
            opts.showName =             true;
            break;
        case "facebook_logo":
            opts.width =                1024;
            opts.height =               1024;
            opts.showName =             true;
            break;

        // Other ---------------------------------------------------------------
        case "facebook_pp":
            opts.width =                180;
            opts.height =               180;
            break;
        case "website":
            opts.width =                300;
            opts.height =               300;
            opts.showName =             true;
            break;
        case "website_mini":
            opts.width =                65;
            opts.height =               65;
            opts.crop =                 true;
            break;
    }
    drawLogo(opts);
};

var CARD_WIDTH_TO_HEIGHT_RATIO =    1.618; // golden ratio
var CARD_OFFSET_RATIO =             .11;
var LINE_WIDTH_RATIO =              .01;
var NAME_TEXT =                     "Soaptag";
var CROP_MARGIN =                   3; // pixels

function drawLogo(opts) {

    // drawing takes place within a square, so if rectangular dimensions are
    // provided, calculate the size of the biggest square that fits inside
    // the rectangle
    var size = Math.min(opts.width, opts.height);
    
    // measure size of logo components relative to the square size
    var cardHeight =    opts.cardScale * size;
    var cardWidth =     (opts.cardScale * CARD_WIDTH_TO_HEIGHT_RATIO) * size;
    var cardOffset =    (opts.cardScale * CARD_OFFSET_RATIO) * size;
    var nameHeight =    opts.showName ? opts.nameScale * size : 0;

    // calculate derived measurements
    var logoHeight =    cardHeight + nameHeight + (cardOffset * 2);
    var logoWidth =     cardWidth + (cardOffset * 2);

    // calculate offset of square within rectange, so that it appears in the
    // middle
    var squareX = (size == opts.width) ? 0 : (opts.width - opts.height) / 2;
    var squareY = (size == opts.height) ? 0 : (opts.height - opts.width) / 2;

    // calculate the offset (relative to the square) of the logo components
    var imageX =        (size - logoWidth) / 2;
    var imageY =        (size - logoHeight) / 2;
    var nameX =         size / 2;
    var nameY =         imageX + logoHeight;

    // if `crop` is true then adjust the canvas size to fit the logo
    if (opts.crop) {
        var canvasWidth =   logoWidth + (CROP_MARGIN * 2);
        var canvasHeight =  logoHeight + (CROP_MARGIN * 2);
    } else {
        var canvasWidth =   opts.width;
        var canvasHeight =  opts.height;
    }

    // if `crop` is true, adjust the component offsets
    if (opts.crop) {
        squareX =   0;
        squareY =   0;
        imageX =    CROP_MARGIN;
        imageY =    CROP_MARGIN;
        nameX =     canvasWidth / 2;
        nameY =     imageX + logoHeight;
    }

    // prepare the canvas
    var canvas =        document.getElementById("canvas");
    var ctx =           canvas.getContext("2d");
    ctx.canvas.width =  canvasWidth;
    ctx.canvas.height = canvasHeight;
    ctx.fillStyle =     opts.backgroundColor;
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);
    ctx.fillStyle =     opts.foregroundColor;
    ctx.lineWidth =     Math.max(LINE_WIDTH_RATIO * size, 1); 
    ctx.strokeStyle =   opts.backgroundColor;
    ctx.font =          (opts.fontScale * size) + "px Helvetica Neue";
    ctx.textAlign =     "center";

    // render image
    var w = parseInt(cardWidth);
    var h = parseInt(cardHeight);
    for (var i = 2; i >= 0; i--) {
        var x = parseInt(squareX + imageX + (cardOffset * i));
        var y = parseInt(squareY + imageY + (cardOffset * i));
        ctx.fillRect(x, y, w, h);
        ctx.strokeRect(x, y, w, h);
    }

    // render name
    if (opts.showName) {
        var x = parseInt(squareX + nameX);
        var y = parseInt(squareY + nameY);
        ctx.fillText(NAME_TEXT, x, y);
    }
}

function openLogo() {
    var canvas = document.getElementById("canvas");
    var img = canvas.toDataURL("image/png");
    document.write('<img src="'+img+'"/>');
}

