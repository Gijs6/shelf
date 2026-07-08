(function () {
    var modal = document.getElementById("search-help-modal");
    if (!modal) return;

    var trigger = document.querySelector("[data-search-help-toggle]");
    if (trigger) {
        trigger.addEventListener("click", function () {
            modal.showModal();
        });
    }

    modal.addEventListener("click", function (e) {
        if (e.target === modal) modal.close();
    });
})();
