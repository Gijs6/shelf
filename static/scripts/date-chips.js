(function () {
    if (window.shelfDateChips) return;
    window.shelfDateChips = true;

    var parts = new Intl.DateTimeFormat("en-GB", {
        timeZone: document.documentElement.dataset.tz || undefined,
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23"
    });

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
        var p = {};
        parts.formatToParts(date).forEach(function (part) {
            p[part.type] = part.value;
        });
        var day = p.year + "-" + p.month + "-" + p.day;
        if (input.type === "date") return day;
        return day + "T" + p.hour + ":" + p.minute;
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
