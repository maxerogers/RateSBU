$(document).ready(function () {
    //check to see if we are in "Search for Classes" page
    $('#ptifrmtgtframe').load(function () {
        var iframe = $('#ptifrmtgtframe').contents();
        // call on "Search" button clicked
        $(iframe).delegate('#CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH', 'click', function () {
            console.log('enter from iframe');
            passThrough();
        });
        // call on enter key
        iframe.keypress(function (event) {
            if (event.which == 13) {
                console.log('enter from iframe');
                passThrough();
            }
        });
    });
});

function passThrough() {
    var iframe = $('#ptifrmtgtframe').contents();
    //check if there is any professor's name on the page
    var existsInIframe = iframe.find('span[id="MTG_INSTR\\$0"]').text();
    if (existsInIframe) {
        console.log(existsInIframe);
        getInstructors();
    } else {
        setTimeout(passThrough, 2000);
        console.log('setTimeout');
    }
}

/*
- looks through the DOM and gets professor's name
- Sends POST request to the backend
*/
function getInstructors() {
    //find the iframe that is loaded
    var iframe = $('#ptifrmtgtframe').contents();

    // find if any professor list exist and collect them into a list
    var jsonArray = [];
    iframe.find('span[id*="MTG_INSTR"]').each(function () {
        var item = {};
        var profName = $(this).text().replace(/<br>|\n/g, "").split(', ');
        if (profName && profName != "Staff") {
            item['id'] = $(this).attr("id");
            item['names'] = profName;
            jsonArray.push(item);
        }
    });
    if (jsonArray.length > 0) {
        console.log(JSON.stringifyjsonArray);
        $.each(jsonArray, function (index, value) {
            var name = value.names[0].toString().replace(/\s+/g, '');
            var obj = [];
            obj.push(value);
            var tempJson = JSON.stringify({
                'prof': obj
            });
            getResponse(tempJson, function (professors) {
                parseResponse(JSON.parse(professors));
            });
        });
    } else {
        setTimeout(passThrough, 2000);
        console.log('setTimeout else');
    }
}

function getResponse(p_data, callback) {
    chrome.runtime.sendMessage({
        method: 'POST',
        action: 'xhttp',
        url: 'http://127.0.0.1:5000/',
        data: p_data
    }, function (response) {
        callback(response);
    });
}


function parseResponse(p_data) {
    var iframe = $('#ptifrmtgtframe').contents();
    //load custom css and append to iframe's head
    var path = chrome.extension.getURL('quality.css');
    $(iframe.find('head')).append($('<link>')
        .attr("rel", "stylesheet")
        .attr("type", "text/css")
        .attr("href", path));

    if (p_data.prof.length > 0) {
        $.each(p_data.prof, function (index, item) {
            var id = item.id.toString();
            var name = item.name;
            var quality = item.quality[0];
            var parentDiv = iframe.find('#win0div' + id);
            //remove existing MTG_INSTR div 
            var _id = id.replace(/\\/g, '');
            if (parentDiv.children(':first').attr('id') == _id) {
                parentDiv.children().remove();
            }
            if (quality) {
                //add it back with info
                if (!parentDiv.find("#" + quality.tid).attr('id')) {
                    parentDiv.append('<a class="nostyle" href="http://www.ratemyprofessors.com/ShowRatings.jsp?tid=' + quality.tid + '" target="_blank" title="Click to view in Rate My Professor website"><div id="' + quality.tid + '" class="wrap-quality"><div id="prof-quality"><div id="prof-name">' + name + '</div><div class="prof-avg-quality"><div id="prof-overallQuality">' + quality.OverallQuality + '</div><div id="prof-averagegrade">' + quality.AverageGrade + '</div><div id="prof-hotness"><img class="prof-hot" src="' + quality.Hotness + '" alt="cat?" height="100%" width="100%"></div></div><div class="prof-rate"><div id="prof-helpfulness">' + quality.Helpfulness + '</div><div id="prof-clarity">' + quality.Clarity + '</div><div id="prof-easiness">' + quality.Easiness + '</div></div></div></div></a>');
                }
            } else {
                if (!parentDiv.find('#prof-quality').attr('id')) {
                    parentDiv.append('<div id="prof-quality"><div id="prof-name">' + name + '</div><div id="prof-ratings-notfound">N/A</div></div>');
                }
            }
        });
    }
}
