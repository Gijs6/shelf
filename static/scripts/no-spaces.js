(function () {
    document.querySelectorAll("[data-no-spaces]").forEach(function (input) {
        input.addEventListener("keydown", function (event) {
            if (event.key === " ") event.preventDefault();
        });

        input.addEventListener("input", function () {
            var stripped = input.value.replace(/\s+/g, "");
            if (stripped === input.value) return;
            var removed = input.value.length - stripped.length;
            var pos = Math.max(0, input.selectionStart - removed);
            input.value = stripped;
            input.setSelectionRange(pos, pos);
        });
    });
})();
