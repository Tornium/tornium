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
