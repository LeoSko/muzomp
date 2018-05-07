function validate() {
    $("#searchbar").onchange=function() {
        let isEnabled = $("#searchbar").value.isEmpty();
        if (isEnabled) {
            $("#search_button").attr("enabled", "enabled");
        }
        else {
            $("#search_button").attr("enabled", "");
        }
    }
}
