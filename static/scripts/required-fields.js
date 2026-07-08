(function () {
    document.querySelectorAll('form[data-require-either]').forEach(function (form) {
        var names = form.dataset.requireEither.split(',');
        var fields = names.map(function (name) {
            return form.elements.namedItem(name);
        });
        form.addEventListener('submit', function (e) {
            var allBlank = fields.every(function (f) {
                return !f.value.trim();
            });
            fields[0].setCustomValidity(allBlank ? 'Add a title or some content.' : '');
            if (allBlank) {
                e.preventDefault();
                fields[0].reportValidity();
            }
        });
        fields.forEach(function (f) {
            f.addEventListener('input', function () {
                fields[0].setCustomValidity('');
            });
        });
    });
})();
