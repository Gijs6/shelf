(function () {
    var shortcutsModal = document.getElementById('shortcuts-modal');

    shortcutsModal.addEventListener('click', function (e) {
        if (e.target === shortcutsModal) shortcutsModal.close();
    });
})();
