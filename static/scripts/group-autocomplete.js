(function () {
    document.querySelectorAll("[data-autocomplete]").forEach(function (input) {
        var datalist = document.getElementById(input.getAttribute("data-autocomplete"));
        if (!datalist) return;

        var options = Array.from(datalist.options).map(function (option) {
            return option.value;
        });

        var field = input.closest(".field");
        field.classList.add("autocomplete");

        var menu = document.createElement("ul");
        menu.className = "autocomplete__menu";
        menu.hidden = true;
        field.appendChild(menu);

        var activeIndex = -1;

        function items() {
            return menu.querySelectorAll(".autocomplete__option");
        }

        function close() {
            menu.hidden = true;
            menu.innerHTML = "";
            activeIndex = -1;
        }

        function setActive(index) {
            var current = items();
            current.forEach(function (item) {
                item.classList.remove("autocomplete__option--active");
            });

            activeIndex = index;
            if (index < 0 || index >= current.length) return;

            current[index].classList.add("autocomplete__option--active");
            current[index].scrollIntoView({ block: "nearest" });
        }

        function open() {
            var query = input.value.trim().toLowerCase();
            var matches = query
                ? options.filter(function (option) {
                      return option.toLowerCase().includes(query);
                  })
                : options;

            menu.innerHTML = "";
            activeIndex = -1;

            matches.forEach(function (value) {
                var item = document.createElement("li");
                item.className = "autocomplete__option";
                item.textContent = value;
                item.addEventListener("mousedown", function (event) {
                    event.preventDefault();
                    input.value = value;
                    close();
                });
                menu.appendChild(item);
            });

            menu.hidden = matches.length === 0;
        }

        input.addEventListener("input", open);
        input.addEventListener("focus", open);
        input.addEventListener("blur", close);

        input.addEventListener("keydown", function (event) {
            var current = items();
            if (menu.hidden || current.length === 0) return;

            if (event.key === "ArrowDown") {
                event.preventDefault();
                setActive((activeIndex + 1) % current.length);
            } else if (event.key === "ArrowUp") {
                event.preventDefault();
                setActive((activeIndex - 1 + current.length) % current.length);
            } else if (event.key === "Enter" && activeIndex >= 0) {
                event.preventDefault();
                input.value = current[activeIndex].textContent;
                close();
            } else if (event.key === "Escape") {
                close();
            }
        });
    });
})();
