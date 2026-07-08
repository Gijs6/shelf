(function () {
    document.addEventListener("click", function (e) {
        var button = e.target.closest("[data-copy-target]");
        if (!button) return;

        var target = document.getElementById(button.getAttribute("data-copy-target"));
        if (!target) return;

        navigator.clipboard.writeText(target.value || target.textContent).then(function () {
            var original = button.textContent;
            button.textContent = "Copied!";
            setTimeout(function () {
                button.textContent = original;
            }, 1500);
        });
    });
})();
