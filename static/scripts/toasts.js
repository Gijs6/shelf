(function () {
    document.addEventListener("htmx:afterSettle", function () {
        document.querySelectorAll(".toast[data-auto-dismiss]:not([data-wired])").forEach(function (el) {
            el.setAttribute("data-wired", "");
            var ms = parseInt(el.getAttribute("data-auto-dismiss"), 10) || 6000;
            setTimeout(function () {
                el.remove();
            }, ms);
            var button = el.querySelector(".toast__dismiss");
            if (button)
                button.addEventListener("click", function () {
                    el.remove();
                });
        });
    });
})();
