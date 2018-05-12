function li(filename, id, totalFileSizeHuman, totalFileSize, link) {
    return `<li class="list-group-item list-group-item-action list-group-item-primary">
                <a id="link-${id}" href="${link}">
                    <div class="row">
                        <div class="col col-filename">${filename}</div>
                        <div id="filesize-${id}" class="col col-filesize" value="${totalFileSize}">0</div>
                        <div class="col col-filesize">${totalFileSizeHuman}</div>
                    </div>
                    <div class="progress">
                        <div id="progress-${id}" class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                </a>
            </li>`;
}

function humanFileSize(bytes, si = false) {
    let thresh = si ? 1000 : 1024;
    if(Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }
    let units = si
        ? ['kB','MB','GB','TB','PB','EB','ZB','YB']
        : ['KiB','MiB','GiB','TiB','PiB','EiB','ZiB','YiB'];
    let u = -1;
    do {
        bytes /= thresh;
        ++u;
    } while(Math.abs(bytes) >= thresh && u < units.length - 1);
    return bytes.toFixed(1) + ' ' + units[u];
}

$('#submitBtn').on('click', function() {
    let formData = new FormData();
    let files = $('input[type=file]')[0].files;
    let n = files.length;
    let currentOffset = $('.progress').length;
    for (let i = 0; i < n; i++) {
        let id = currentOffset + i;
        formData.append('audio', files[i]);
        $('#uploadProgress').append(li(files[i].name, id, humanFileSize(files[i].size), files[i].size));
        $(document).queue('upload', function() {
            $.ajax({
                url: '/upload/',
                type: 'POST',
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-CSRFToken', $("[name=csrfmiddlewaretoken]").val());
                },
                data: formData,
                cache: false,
                contentType: false,
                processData: false,

                xhr: function () {
                    let myXhr = $.ajaxSettings.xhr();
                    if (myXhr.upload) {
                        // For handling the progress of the upload
                        myXhr.upload.addEventListener('progress', function (e) {
                            let progress = $(`#progress-${id}`);
                            if (e.lengthComputable) {
                                progress.removeClass('hidden');
                            }
                            progress.attr({
                                'aria-valuenow': e.loaded,
                                'aria-valuemax': e.total
                            });
                            let percentage = Math.round(e.loaded * 100.0 / e.total);
                            let filesize = $(`#filesize-${id}`);
                            filesize.html(humanFileSize(percentage / 100.0 * filesize.attr('value')));
                            progress.css('width', percentage + '%');
                        }, false);
                    }
                    return myXhr;
                },

                success: function (msg) {
                    $(`#link-${id}`).attr('href', msg.link[0]);
                    $(document).dequeue('upload');
                    let progress = $(`#progress-${id}`);
                    progress.parent().parent().removeClass("list-group-item-primary");
                    progress.parent().parent().addClass("list-group-item-success");
                },

                error: function() {
                    $(document).dequeue('upload');
                    let progress = $(`#progress-${id}`);
                    progress.parent().parent().removeClass("list-group-item-primary");
                    progress.parent().parent().addClass("list-group-item-danger");
                }
            });
        });
    }
    $(document).dequeue('upload');
});
