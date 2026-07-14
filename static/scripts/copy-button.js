(function () {
    function copyText(text) {
        if (navigator.clipboard) {
            return navigator.clipboard.writeText(text);
        }

        var textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();

        try {
            document.execCommand("copy");
        } finally {
            textarea.remove();
        }

        return Promise.resolve();
    }

    function showTooltip(button) {
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
    }

    document.addEventListener("click", function (e) {
        var button = e.target.closest("[data-copy-target], [data-copy-html-target]");
        if (!button) return;

        var htmlTargetId = button.getAttribute("data-copy-html-target");
        var text;

        if (htmlTargetId) {
            var htmlTarget = document.getElementById(htmlTargetId);
            if (!htmlTarget) return;

            var title = button.getAttribute("data-copy-title") || "";
            text = (title ? title + "\n\n" : "") + htmlTarget.innerText.trim();
        } else {
            var target = document.getElementById(button.getAttribute("data-copy-target"));
            if (!target) return;

            text = target.value || target.textContent;
        }

        copyText(text).then(function () {
            showTooltip(button);
        });
    });
})();
