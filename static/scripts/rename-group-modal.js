(function () {
    var modal = document.getElementById("rename-group-modal");
    if (!modal) return;

    var title = modal.querySelector(".modal__title");
    var oldNameInput = modal.querySelector("input[name='old_name']");
    var newNameInput = modal.querySelector("input[name='new_name']");

    document.querySelectorAll("[data-rename-group]").forEach(function (trigger) {
        trigger.addEventListener("click", function () {
            var name = trigger.getAttribute("data-rename-group");
            title.textContent = 'Rename "' + name + '"';
            oldNameInput.value = name;
            newNameInput.value = name;
            modal.showModal();
            newNameInput.select();
        });
    });

    modal.addEventListener("click", function (e) {
        if (e.target === modal) modal.close();
    });
})();
