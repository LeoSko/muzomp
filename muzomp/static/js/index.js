function refreshable(from, to, refreshRate = 5000) {
    return {
        from: '#' + from,
        to: to,
        refreshRate: refreshRate
    };
}

const function_list = [
        refreshable('audio', '/index/audio'),
        refreshable('processing', '/index/processing'),
        refreshable('queue', '/index/queue'),
    ];

for (let i = 0; i < function_list.length; i++) {
    let div_id = function_list[i].from;
    let url = function_list[i].to;
    $(div_id).load(url);
    setInterval(function () {
        $(div_id).load(url);
    }, function_list[i].refreshRate);
}