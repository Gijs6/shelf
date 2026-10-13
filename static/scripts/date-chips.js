(function () {
    if (window.shelfDateChips) return;
    window.shelfDateChips = true;

    function pad(value) {
        return String(value).padStart(2, "0");
    }

    function shift(code) {
        var amount = parseInt(code, 10);
        var next = new Date();

        if (code.endsWith("mo")) next.setMonth(next.getMonth() + amount);
        else if (code.endsWith("w")) next.setDate(next.getDate() + amount * 7);
        else if (code.endsWith("d")) next.setDate(next.getDate() + amount);
        else if (code.endsWith("h")) next.setHours(next.getHours() + amount);

        return next;
    }

    function format(input, date) {
        var day = date.getFullYear() + "-" + pad(date.getMonth() + 1) + "-" + pad(date.getDate());
        if (input.type === "date") return day;
        return day + "T" + pad(date.getHours()) + ":" + pad(date.getMinutes());
    }

    document.addEventListener("click", function (event) {
        var chip = event.target.closest(".date-chips__chip");
        if (!chip) return;

        var input = document.getElementById(chip.dataset.target);
        if (!input) return;

        input.value = format(input, shift(chip.dataset.dateChip));
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.dispatchEvent(new Event("change", { bubbles: true }));
    });
})();
