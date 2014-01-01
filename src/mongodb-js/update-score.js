/*
 * Script to update the score in all content documents.
 *
 * Usage:
 *
 *   mongo --eval "var DATABASE_NAME='sundowner_sandbox';" update-score.js
 *
 */

// TODO to be added automatically by script
var WEIGHT_VOTE             = 0.8;
var WEIGHT_DAY_OFFSET       = 0.3;
var WEIGHT_WEEK_OFFSET      = 0.1;

// Helpers ---------------------------------------------------------------------

/* Given the ratings I have, there is a 95% chance that the "real" fraction 
 * of positive ratings is at least what?
 *
 * http://stackoverflow.com/questions/10029588/python-implementation-of-the-wilson-score-interval
 * http://amix.dk/blog/post/19588
 * http://blog.reddit.com/2009/10/reddits-new-comment-sorting-system.html
 * http://www.evanmiller.org/how-not-to-sort-by-average-rating.html
 */
var calcWilsonScoreInterval = function(up, down) {

    var n = up + down;
    if (n == 0) {
        return 0;
    }
    z = 1.96; // 95% confidence
    var phat = up / n;
    return ((phat + z*z/(2*n) - z * Math.sqrt((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n));
};

var calcOverallScore = function(scoreVote, scoreDayOffset, scoreWeekOffset) {
    return
        scoreVote * WEIGHT_VOTE +
        scoreDayOffset * WEIGHT_DAY_OFFSET +
        scoreWeekOffset * WEIGHT_WEEK_OFFSET;
};

/* Distance in seconds between two times of day (00:00 - 23:59).
 *
 * Because the dimension is cyclical (a repeating 24 hour circle) the max
 * distance between 2 points is 12 hours (anything greater and the distance to 
 * a point in the previous/next day because the shortest.
 */
var SECONDS_PER_DAY = 86400;
var calcDayOffsetScore = function(created) {

    var contentOffset = created % SECONDS_PER_DAY;
    var nowOffset = now % SECONDS_PER_DAY;

    var shortestDiff = Math.abs(contentOffset - nowOffset);
    if (shortestDiff > (SECONDS_PER_DAY / 2)) {
        shortestDiff = SECONDS_PER_DAY - shortestDiff; 
    }

    var proportionOfDay = shortestDiff / (SECONDS_PER_DAY / 2.0);
    return 1 - proportionOfDay;
};

// See 'calcDayOffsetScore'
var SECONDS_PER_WEEK = 604800;
var calcWeekOffsetScore = function(created) {

    var contentOffset = created % SECONDS_PER_WEEK;
    var nowOffset = now % SECONDS_PER_WEEK;

    var shortestDiff = Math.abs(contentOffset - nowOffset);
    if (shortestDiff > (SECONDS_PER_WEEK / 2)) {
        shortestDiff = SECONDS_PER_WEEK - shortestDiff; 
    }

    var proportionOfWeek = shortestDiff / (SECONDS_PER_WEEK / 2.0);
    return 1 - proportionOfWeek;
};

// Main ------------------------------------------------------------------------

var now = Math.floor((new Date()).getTime() / 1000);
var db = db.getSiblingDB(DATABASE_NAME);

db.content.find().forEach(function(doc) {

    // individual scores are maintained so that in the future the entity that
    // updates one of the scores will be able to update the overall scare
    var scoreVote =         calcWilsonScoreInterval(doc.votes.up, doc.votes.down);
    var scoreDayOffset =    calcDayOffsetScore(doc.created);
    var scoreWeekOffset =   calcWeekOffsetScore(doc.created);
    var scoreOverall =      calcOverallScore(scoreVote, scoreDayOffset, scoreWeekOffset);

    var score = {
        overall:        scoreOverall,
        vote:           scoreVote,
        day_offset:     scoreDayOffset,
        week_offset:    scoreWeekOffset,
    };
    
    db.content.update({_id: doc._id}, {$set: {score: score}});
});

