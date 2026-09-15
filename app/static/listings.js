(function () {
  var rowsEl = document.getElementById("rows");
  var emptyEl = document.getElementById("empty");
  var locFilter = document.getElementById("loc-filter");

  function rows() {
    return Array.prototype.slice.call(rowsEl.querySelectorAll(".row"));
  }

  function visibleRows() {
    return rows().filter(function (r) { return !r.hidden; });
  }

  function applyFilter() {
    var val = locFilter.value;
    rows().forEach(function (r) {
      r.hidden = val !== "all" && r.dataset.loc !== val;
    });
    updateEmptyState();
  }

  function updateEmptyState() {
    emptyEl.hidden = visibleRows().length > 0;
  }

  function removeRow(row) {
    row.classList.add("leaving");
    setTimeout(function () {
      row.remove();
      updateEmptyState();
    }, 150);
  }

  function setRowBusy(row, busy) {
    row.querySelectorAll("button").forEach(function (b) { b.disabled = busy; });
  }

  function submitReview(row, interested, note) {
    setRowBusy(row, true);
    fetch("/api/listings/" + encodeURIComponent(row.dataset.id) + "/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ interested: interested, note: note || "" }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("request failed");
        removeRow(row);
      })
      .catch(function () {
        setRowBusy(row, false);
        row.classList.add("error");
      });
  }

  function openPassNote(row) {
    var actions = row.querySelector(".rowactions");
    var noteBox = row.querySelector(".passnote");
    var input = noteBox.querySelector("input");
    actions.hidden = true;
    noteBox.hidden = false;
    input.value = "";
    input.focus();

    function close() {
      noteBox.hidden = true;
      actions.hidden = false;
    }

    input.onkeydown = function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        submitReview(row, false, input.value.trim());
      } else if (e.key === "Escape") {
        e.preventDefault();
        close();
      }
    };
    input.onblur = close;
  }

  rowsEl.addEventListener("click", function (e) {
    var btn = e.target.closest ? e.target.closest("button[data-act]") : null;
    if (!btn) return;
    var row = btn.closest(".row");
    if (btn.dataset.act === "interested") submitReview(row, true, "");
    if (btn.dataset.act === "pass") openPassNote(row);
  });

  rowsEl.addEventListener("keydown", function (e) {
    var row = e.target.closest ? e.target.closest(".row") : null;
    if (!row || e.target.tagName === "INPUT") return;

    if (e.key === "i") {
      e.preventDefault();
      submitReview(row, true, "");
    } else if (e.key === "p") {
      e.preventDefault();
      openPassNote(row);
    } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      var visible = visibleRows();
      var idx = visible.indexOf(row);
      var next = e.key === "ArrowDown" ? visible[idx + 1] : visible[idx - 1];
      if (next) next.focus();
    }
  });

  locFilter.addEventListener("change", applyFilter);

  applyFilter();
})();
