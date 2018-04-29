function li(artist, title, id) {
    return `<li class="list-group-item list-group-item-action list-group-item-primary">
                <div class="row">
                    <div class="col col-filename">${artist} - ${title}</div>
                </div>
                <div class="progress">
                    <div id="progress-${id}" class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
                </div>
            </li>`;
}

$('#submitBtn').on('click', function() {
    let formData = new FormData();
    let files = $('input[type=file]')[0].files;
    let n = files.length;
    let currentOffset = $('.progress').length;
    for (let i = 0; i < n; i++) {
        let id = currentOffset + i;
        formData.append('audio', files[i]);
        $('#uploadProgress').append(li(id, id, id));
        $.ajax({
            // Your server script to process the upload
            url: '/upload/',
            type: 'POST',
            beforeSend: function(xhr) {
                xhr.setRequestHeader('X-CSRFToken', $("[name=csrfmiddlewaretoken]").val());
            },

            // Form data
            data: formData,

            // Tell jQuery not to process data or worry about content-type
            // You *must* include these options!
            cache: false,
            contentType: false,
            processData: false,

            // Custom XMLHttpRequest
            xhr: function() {
                let myXhr = $.ajaxSettings.xhr();
                if (myXhr.upload) {
                    // For handling the progress of the upload
                    myXhr.upload.addEventListener('progress', function(e) {
                        let progress = $(`#progress-${id}`);
                        if (e.lengthComputable)
                            progress.removeClass('hidden');
                            progress.attr({
                                'aria-valuenow': e.loaded,
                                'aria-valuemax': e.total
                            });
                            progress.css('width', Math.round(e.loaded * 100.0 / e.total) + '%');
                        }, false);
                }
                return myXhr;
            }
        });
    }
});
