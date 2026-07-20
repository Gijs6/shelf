(function () {
    var routes = JSON.parse(document.getElementById("nav-routes").textContent);

    var CHORD_DESTINATIONS = {
        g: { d: routes.dashboard, n: routes.notes, t: routes.todos, s: routes.stickyNotes },
        c: { n: routes.newNote, t: routes.newTodo, s: routes.newStickyNote }
    };

    var TODO_STATE_ORDER = ["shelved", "open", "active", "done", "cancelled"];

    var pendingChord = null;
    var chordTimer = null;

    function clearChord() {
        pendingChord = null;
        if (chordTimer) {
            clearTimeout(chordTimer);
            chordTimer = null;
        }
    }

    document.addEventListener("keydown", function (e) {
        if (e.defaultPrevented) return;

        var typing = e.target.matches("input, textarea, select") || e.target.isContentEditable;

        if (e.key === "Escape") {
            if (typing || document.querySelector("dialog[open]")) return;
            clearChord();
            history.back();
            return;
        }

        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            var form = e.target.closest("form") || document.querySelector("form.editor");
            if (form) {
                e.preventDefault();
                form.requestSubmit();
            }
            return;
        }

        if (typing || e.ctrlKey || e.metaKey || e.altKey) return;

        if (pendingChord) {
            var dest = CHORD_DESTINATIONS[pendingChord][e.key];
            clearChord();
            if (dest) {
                e.preventDefault();
                window.location.href = dest;
            }
            return;
        }

        if (e.key === "g" || e.key === "c") {
            pendingChord = e.key;
            chordTimer = setTimeout(clearChord, 1500);
            return;
        }

        if (e.key === "?") {
            e.preventDefault();
            document.getElementById("shortcuts-modal").showModal();
        } else if (e.key === "/") {
            e.preventDefault();
            var searchInput = document.getElementById("q");
            if (searchInput) {
                searchInput.focus();
            } else {
                window.location.href = routes.search;
            }
        } else if (e.key === "n" || e.key === "N") {
            var newLink = document.querySelector('[data-shortcut="new"]');
            if (newLink) {
                e.preventDefault();
                newLink.click();
            }
        } else if (e.key === "e" || e.key === "E") {
            var editLink = document.querySelector('[data-shortcut="edit"]');
            if (editLink) {
                e.preventDefault();
                editLink.click();
            }
        } else if (e.key === "a") {
            var archiveToggle = document.querySelector('[data-shortcut="archive-toggle"]');
            if (archiveToggle) {
                e.preventDefault();
                archiveToggle.requestSubmit();
                return;
            }
            var archivedLink = document.querySelector('[data-shortcut="archived"]');
            if (archivedLink) {
                e.preventDefault();
                archivedLink.click();
            }
        } else if (e.key === "t") {
            var trashLink = document.querySelector('[data-shortcut="trash"]');
            if (trashLink) {
                e.preventDefault();
                trashLink.click();
            }
        } else if (e.key === "p") {
            var pinCard = e.target.closest(".sticky-note");
            var pinForm = pinCard && pinCard.querySelector('[data-shortcut="sticky-pin"]');
            if (pinForm) {
                e.preventDefault();
                pinForm.requestSubmit();
            }
        } else if (e.key === "d") {
            var stickyCard = e.target.closest(".sticky-note");
            var stickyDeleteForm = stickyCard && stickyCard.querySelector('[data-shortcut="sticky-delete"]');
            if (stickyDeleteForm) {
                e.preventDefault();
                stickyDeleteForm.requestSubmit();
                return;
            }
            var deleteForm = document.querySelector('[data-shortcut="delete"]');
            if (deleteForm) {
                e.preventDefault();
                deleteForm.requestSubmit();
            }
        } else if (e.key >= "1" && e.key <= "5") {
            var state = TODO_STATE_ORDER[Number(e.key) - 1];
            var stateButton = document.querySelector('.state-picker button[data-state="' + state + '"]');
            if (stateButton) {
                e.preventDefault();
                stateButton.click();
            }
        }
    });
})();
