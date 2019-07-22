/**
 * Created by mitsui on 2018/08/20.
 */

/**
 * フォームをロード
 */
function load_contents(url, id) {
    // フォームをAjaxで作成する
    $.ajax({
        url: url,
        type: 'GET',
        cache: false,
        dataType: 'text',
        success: function (data) {
            $('#'+id).html(data);
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            console.log("Failed to read content.");
            alert("Internal server error.");
        }
    });
}