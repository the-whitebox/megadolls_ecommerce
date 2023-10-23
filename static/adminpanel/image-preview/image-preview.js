function image_preview(id, element_class, e) {
    let f = e.target.files[0]
    const fileReader = new FileReader();
    fileReader.onload = (function (e) {
        const file = e.target;
        $('.' + element_class).html("<img class=\"imageThumb\" id='" + id + "' src=\"" + e.target.result + "\" title=\"" + file.name + "\"/>")
    });
    fileReader.readAsDataURL(f);
}

$(document).ready(function() {
    $(document).on("change", "#files", function (e) {
        if ($('#max-image-error')) {
            $('#max-image-error').remove()
        }
        if ($('.pip').length < 5) {
            let files = e.target.files,
                filesLength = files.length;

            for (let i = 0; i < filesLength; i++) {
                let f = files[i]
                const fileReader = new FileReader();
                fileReader.onload = (function (e) {
                    const file = e.target;
                    $("<span class=\"pip\">" +
                        "<img class=\"imageThumb\" src=\"" + e.target.result + "\" title=\"" + file.name + "\"/>" +
                        "<br/><span class=\"remove\">x</span>" +
                        "</span>").insertAfter("#files");

                });
                fileReader.readAsDataURL(f);
            }
        } else {
            $('<span id="max-image-error" style="color: red; display: block">You can upload maximum 5 images</span>').insertAfter('#files')
        }
    });
})