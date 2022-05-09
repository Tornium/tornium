/* Copyright (C) tiksan - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by tiksan <webmaster@deek.sh>*/

function getTID(string) {
    var matches = string.match(/\[(.*?)\]/);

    if(matches) {
        return matches[1];
    } else {
        return 0;
    }
}


function commas(number) {
    return number.toLocaleString('en-US');
}


function reltime(timestamp) {
    delta = new Date().getTime() - timestamp;

    if(delta < 60) {  // One minute
        return "Now";
    } else if(delta < 3600) {  // Sixty minutes
        return Number(delta/60) + " minutes ago";
    } else if(delta < 86400) {  // One day
        return Number(delta/3600) + " hours ago";
    } else if(delta < 2592000) {  // Thirty days
        return Number(delta/86400) + " days ago";
    } else if(delta < 31104000) {  // Twleve months
        return Number(delta/2592000) + " months ago";
    } else {
        return "A long time ago";
    }
}
