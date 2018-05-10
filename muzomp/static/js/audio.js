window.chartColors = {
	red: 'rgb(255, 99, 132)',
	orange: 'rgb(255, 159, 64)',
	yellow: 'rgb(255, 205, 86)',
	green: 'rgb(75, 192, 192)',
	blue: 'rgb(54, 162, 235)',
	purple: 'rgb(153, 102, 255)',
	grey: 'rgb(201, 203, 207)'
};

let bpm_values = [];
let time_labels = [];
let time_values = [];

let trace1 = { };
let data = [ trace1 ];
let layout = { };
let intervalMap = { };

function updateChart() {
    trace1 = {
        x: time_values,
        y: bpm_values,
        mode: 'lines+markers',
        type: 'scatter',
        name: 'BPM',
        line: {shape: 'hv'},
        text: time_labels
    };

    data = [ trace1 ];
    Plotly.newPlot('bpmChart', data, layout);
}

function refreshable(url, callback, refreshRate = 5000) {
    return {
        url: url,
        callback: function(data) {
            callback(data);
            if (data['finished']) {
                clearInterval(intervalMap[url]);
            }
        },
        refreshRate: refreshRate,
        successCount: 0,
        interval_id: -1
    };
}

const function_list = [
    refreshable(window.location.pathname + '/bpm_data', function (data) {
        bpm_values = data['bpm_values'];
        time_values = data['time_values'];
        time_labels = data['time_labels'];
        updateChart();
    }),
    refreshable(window.location.pathname + '/data', function (data) {
        layout = {
            xaxis: {
                range: [ 0, data['duration'] ]
            },
            yaxis: {
                range: [ 0, 200 ]
            },
            title: 'BPMs of ' + data['artist'] + ' - ' + data['title']
        };
        updateChart();
    })
];

for (let i = 0; i < function_list.length; i++) {
    $.getJSON(function_list[i].url, function_list[i].callback);
    intervalMap[function_list[i].url] = setInterval(function () {
        $.getJSON(function_list[i].url, function_list[i].callback);
    }, function_list[i].refreshRate);
}

function refreshableDiv(from, to, refreshRate = 5000) {
    return {
        from: '#' + from,
        to: to,
        refreshRate: refreshRate
    };
}

const refreshableDivList = [
        refreshableDiv('bpm', window.location.pathname + '/bpm')
    ];

for (let i = 0; i < refreshableDivList.length; i++) {
    let div_id = refreshableDivList[i].from;
    let url = refreshableDivList[i].to;
    $(div_id).load(url);
    setInterval(function () {
        $(div_id).load(url);
    }, refreshableDivList[i].refreshRate);
}