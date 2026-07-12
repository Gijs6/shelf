(function () {
    document.addEventListener("click", function (e) {
        var button = e.target.closest("[data-copy-target]");
        if (!button) return;

        var target = document.getElementById(button.getAttribute("data-copy-target"));
        if (!target) return;

        navigator.clipboard.writeText(target.value || target.textContent).then(function () {
            var existing = button.querySelector(".tooltip");
            if (existing) existing.remove();

            var tooltip = document.createElement("span");
            tooltip.className = "tooltip";
            tooltip.textContent = "Copied!";
            button.classList.add("tooltip-anchor");
            button.appendChild(tooltip);

            setTimeout(function () {
                tooltip.remove();
            }, 1500);
        });
    });
})();
