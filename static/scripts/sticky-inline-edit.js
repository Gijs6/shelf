(function () {
    var autoEdit = document.querySelector(".sticky-note[data-autoedit]");
    if (autoEdit) {
        autoEdit.classList.add("sticky-note--editing");
        var autoInput = autoEdit.querySelector(".sticky-note__content-input");
        if (autoInput) autoInput.focus();
        history.replaceState(null, "", location.pathname);
    }

    if (window.shelfStickyEdit) return;
    window.shelfStickyEdit = true;

    function openSticky(article) {
        article.classList.add("sticky-note--editing");
    }

    function saveSticky(article) {
        var li = article.closest("li");
        var form = article.querySelector(".sticky-note__edit");
        var url = article.dataset.updateUrl;
        article.classList.remove("sticky-note--editing");

        fetch(url, { method: "PUT", body: new FormData(form) })
            .then(function (response) {
                if (response.redirected || !response.ok) throw new Error(response.statusText);
                if (response.status === 204) {
                    li.remove();
                    return;
                }
                return response.text().then(function (html) {
                    var template = document.createElement("template");
                    template.innerHTML = html.trim();
                    li.replaceWith(template.content.firstElementChild);
                });
            })
            .catch(function () {
                openSticky(article);
                window.toast("Couldn't save the sticky note. Your text is still here, so try again.", { type: "danger" });
            });
    }

    document.addEventListener("click", function (e) {
        var article = e.target.closest(".sticky-note");
        if (!article || article.classList.contains("sticky-note--editing")) return;
        if (e.target.closest("a, button, input, label")) return;
        if (!e.target.closest(".sticky-note__view")) return;

        openSticky(article);
        var contentInput = article.querySelector(".sticky-note__content-input");
        if (contentInput) contentInput.focus();
    });

    document.addEventListener("focusout", function (e) {
        var article = e.target.closest(".sticky-note");
        if (!article || !article.classList.contains("sticky-note--editing")) return;
        setTimeout(function () {
            if (!document.hasFocus()) return;
            if (article.classList.contains("sticky-note--editing") && !article.contains(document.activeElement)) {
                saveSticky(article);
            }
        }, 0);
    });

    document.addEventListener("submit", function (e) {
        if (e.target.classList.contains("sticky-note__edit")) e.preventDefault();
    });

    document.addEventListener("visibilitychange", function () {
        if (!document.hidden) return;
        document.querySelectorAll(".sticky-note--editing").forEach(saveSticky);
    });

    document.addEventListener("click", function (e) {
        var swatch = e.target.closest(".colour-picker__option");
        if (!swatch) return;
        var article = swatch.closest(".sticky-note");
        var colour = swatch.dataset.colour;

        article.querySelector(".sticky-note__colour-value").value = colour;
        article.querySelectorAll(".colour-picker__option").forEach(function (option) {
            var selected = option === swatch;
            option.classList.toggle("colour-picker__option--selected", selected);
            option.setAttribute("aria-pressed", selected ? "true" : "false");
        });
        article.className = article.className.replace(/\bsticky-note--(?!pinned\b|editing\b)\S+/, "sticky-note--" + colour);
    });

    document.addEventListener("keydown", function (e) {
        var article = e.target.closest(".sticky-note");
        if (!article || !article.classList.contains("sticky-note--editing")) return;

        if (e.key === "Escape") {
            e.target.blur();
        }
    });
})();
