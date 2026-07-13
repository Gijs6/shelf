(function () {
    document.querySelectorAll("textarea.editor__content").forEach(function (textarea) {
        var mde = new EasyMDE({
            element: textarea,
            toolbar: false,
            status: false,
            spellChecker: false,
            autoDownloadFontAwesome: false,
            forceSync: true,
            placeholder: textarea.getAttribute("placeholder") || ""
        });

        mde.codemirror.on("change", function () {
            textarea.dispatchEvent(new Event("input", { bubbles: true }));
        });
    });
})();
