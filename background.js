chrome.runtime.onMessage.addListener(function (request, sender, callback) {
    if (request.action == "xhttp") {
        var xhttp = new XMLHttpRequest();
        xhttp.onload = function () {
            callback(xhttp.responseText);
        };

        xhttp.open(request.method, request.url, true);
        if (request.method == 'POST') {
            xhttp.setRequestHeader('Content-Type', 'application/json');
        }
        xhttp.send(request.data);
        return true; //https://developer.chrome.com/extensions/content_scripts#host-page-communication
    }
});
