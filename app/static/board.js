(function () {
  var reasonOptions = document.getElementById("reason-options");
  var dragCard = null;

  function dropzones() {
    return Array.prototype.slice.call(document.querySelectorAll("[data-dropzone]"));
  }

  function columnFor(stage) {
    return document.querySelector('[data-dropzone][data-stage="' + stage + '"]');
  }

  function updateCount(stage) {
    var zone = columnFor(stage);
    if (!zone) return;
    var count = zone.querySelectorAll(".card").length;
    var head = zone.closest(".col, .archive-lane").querySelector(".col-count");
    if (head) head.textContent = count;
  }

  function updateEmptyMarker(zone) {
    var empty = zone.querySelector(".col-empty");
    if (empty) empty.hidden = zone.querySelectorAll(".card").length > 0;
  }

  function refreshZone(stage) {
    var zone = columnFor(stage);
    if (!zone) return;
    updateCount(stage);
    updateEmptyMarker(zone);
  }

  function clearDragOver() {
    dropzones().forEach(function (z) { z.classList.remove("drag-over"); });
  }

  document.addEventListener("dragstart", function (e) {
    var card = e.target.closest ? e.target.closest(".card[draggable]") : null;
    if (!card) return;
    dragCard = card;
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", card.dataset.id);
    setTimeout(function () { card.classList.add("dragging"); }, 0);
  });

  document.addEventListener("dragend", function (e) {
    var card = e.target.closest ? e.target.closest(".card") : null;
    if (card) card.classList.remove("dragging");
    dragCard = null;
    clearDragOver();
  });

  document.addEventListener("dragover", function (e) {
    var zone = e.target.closest ? e.target.closest("[data-dropzone]") : null;
    if (!zone || !dragCard) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    zone.classList.add("drag-over");
  });

  document.addEventListener("dragleave", function (e) {
    var zone = e.target.closest ? e.target.closest("[data-dropzone]") : null;
    if (zone && !zone.contains(e.relatedTarget)) zone.classList.remove("drag-over");
  });

  document.addEventListener("drop", function (e) {
    var zone = e.target.closest ? e.target.closest("[data-dropzone]") : null;
    clearDragOver();
    if (!zone || !dragCard) return;
    e.preventDefault();

    var card = dragCard;
    dragCard = null;

    var targetStage = zone.dataset.stage;
    var sourceStage = card.dataset.stage;
    if (targetStage === sourceStage) return;

    if (targetStage === "archived") {
      openArchivePrompt(card, zone);
    } else {
      performMove(card, zone, targetStage, null, "");
    }
  });

  function openArchivePrompt(card, zone) {
    if (card.querySelector(".archive-prompt")) return;

    var prompt = document.createElement("div");
    prompt.className = "archive-prompt";

    var select = document.createElement("select");
    select.appendChild(reasonOptions.content.cloneNode(true));
    select.value = "passed";

    var note = document.createElement("input");
    note.type = "text";
    note.placeholder = "Note (optional)";
    note.setAttribute("aria-label", "Archive note");

    var actions = document.createElement("div");
    actions.className = "archive-prompt-actions";
    var confirmBtn = document.createElement("button");
    confirmBtn.type = "button";
    confirmBtn.className = "btn";
    confirmBtn.textContent = "Archive";
    var cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "btn ghost";
    cancelBtn.textContent = "Cancel";
    actions.appendChild(confirmBtn);
    actions.appendChild(cancelBtn);

    prompt.appendChild(select);
    prompt.appendChild(note);
    prompt.appendChild(actions);
    card.appendChild(prompt);
    card.classList.add("prompting");
    select.focus();

    function close() {
      prompt.remove();
      card.classList.remove("prompting");
    }

    confirmBtn.addEventListener("click", function () {
      var reason = select.value;
      var noteText = note.value.trim();
      close();
      performMove(card, zone, "archived", reason, noteText);
    });
    cancelBtn.addEventListener("click", close);
    note.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        confirmBtn.click();
      } else if (e.key === "Escape") {
        e.preventDefault();
        close();
      }
    });
  }

  function syncArchiveDisplay(card, data) {
    var foot = card.querySelector(".card-foot");
    var chip = foot.querySelector(".chip");
    var note = card.querySelector(".card-note");

    if (data.stage !== "archived") {
      if (chip) chip.remove();
      if (note) note.remove();
      return;
    }

    if (!chip) {
      chip = document.createElement("span");
      chip.className = "chip";
      foot.appendChild(chip);
    }
    chip.textContent = "reason: " + data.reason;

    if (data.note) {
      if (!note) {
        note = document.createElement("p");
        note.className = "card-note";
        foot.parentNode.insertBefore(note, foot);
      }
      note.textContent = data.note;
    } else if (note) {
      note.remove();
    }
  }

  function performMove(card, zone, targetStage, reason, note) {
    var originalParent = card.parentNode;
    var originalNext = card.nextSibling;
    var originalStage = card.dataset.stage;
    var originalMtime = card.dataset.mtime;

    zone.appendChild(card);
    card.dataset.stage = targetStage;
    card.classList.toggle("is-archived", targetStage === "archived");
    card.classList.add("is-moving");
    refreshZone(originalStage);
    refreshZone(targetStage);

    var body = { to: targetStage, note: note || "", mtime: parseFloat(originalMtime) };
    if (reason) body.reason = reason;

    fetch("/api/cards/" + encodeURIComponent(card.dataset.id) + "/stage", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("move failed");
        return res.json();
      })
      .then(function (data) {
        card.classList.remove("is-moving");
        card.dataset.mtime = data.mtime;
        syncArchiveDisplay(card, data);
      })
      .catch(function () {
        card.classList.remove("is-moving");
        card.dataset.stage = originalStage;
        card.classList.toggle("is-archived", originalStage === "archived");
        originalParent.insertBefore(card, originalNext);
        refreshZone(originalStage);
        refreshZone(targetStage);
        card.classList.add("drop-error");
        setTimeout(function () { card.classList.remove("drop-error"); }, 1600);
      });
  }

  document.addEventListener("click", function (e) {
    if (e.target.closest && (e.target.closest(".card-link") || e.target.closest(".archive-prompt"))) return;
    var card = e.target.closest ? e.target.closest(".card[data-id]") : null;
    if (!card) return;
    window.location.href = "/cards/" + encodeURIComponent(card.dataset.id);
  });
})();
