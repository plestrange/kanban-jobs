(function () {
  var reasonOptions = document.getElementById("reason-options");
  var board = document.querySelector(".board");
  var roundStages = board ? board.dataset.roundStages.split(" ") : [];
  var dragListing = null;

  function dropzones() {
    return Array.prototype.slice.call(document.querySelectorAll("[data-dropzone]"));
  }

  function columnFor(stage) {
    return document.querySelector('[data-dropzone][data-stage="' + stage + '"]');
  }

  function updateCount(stage) {
    var zone = columnFor(stage);
    if (!zone) return;
    var count = zone.querySelectorAll(".listing").length;
    var head = zone.closest(".col, .archive-lane").querySelector(".col-count");
    if (head) head.textContent = count;
  }

  function updateEmptyMarker(zone) {
    var empty = zone.querySelector(".col-empty");
    if (empty) empty.hidden = zone.querySelectorAll(".listing").length > 0;
  }

  function refreshZone(stage) {
    var zone = columnFor(stage);
    if (!zone) return;
    updateCount(stage);
    updateEmptyMarker(zone);
  }

  // Done rounds sit below unfinished ones; each group is oldest first (views.interview_board).
  function sortKey(listing) {
    return [listing.classList.contains("is-done") ? 1 : 0, -parseInt(listing.dataset.days || "0", 10)];
  }

  function placeListing(zone, listing) {
    var key = sortKey(listing);
    var cards = zone.querySelectorAll(".listing");
    for (var i = 0; i < cards.length; i++) {
      if (cards[i] === listing) continue;
      var other = sortKey(cards[i]);
      if (key[0] < other[0] || (key[0] === other[0] && key[1] < other[1])) {
        zone.insertBefore(listing, cards[i]);
        return;
      }
    }
    var empty = zone.querySelector(".col-empty");
    if (empty) zone.insertBefore(listing, empty);
    else zone.appendChild(listing);
  }

  function setRoundState(listing, done, days) {
    listing.classList.toggle("is-done", done);
    if (days !== undefined) {
      listing.dataset.days = days;
      var daysEl = listing.querySelector(".days");
      if (daysEl) daysEl.textContent = days + " days";
    }
    var btn = listing.querySelector(".round-toggle");
    if (!btn) {
      btn = document.createElement("button");
      btn.type = "button";
      btn.className = "round-toggle";
      listing.querySelector(".listing-foot").appendChild(btn);
    }
    btn.hidden = roundStages.indexOf(listing.dataset.stage) === -1;
    btn.textContent = done ? "\u2713 done" : "Mark done";
    btn.title = done ? "Undo \u2014 round not done" : "Mark this round done";
  }

  function clearDragOver() {
    dropzones().forEach(function (z) { z.classList.remove("drag-over"); });
  }

  document.addEventListener("dragstart", function (e) {
    var listing = e.target.closest ? e.target.closest(".listing[draggable]") : null;
    if (!listing) return;
    dragListing = listing;
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", listing.dataset.id);
    setTimeout(function () { listing.classList.add("dragging"); }, 0);
  });

  document.addEventListener("dragend", function (e) {
    var listing = e.target.closest ? e.target.closest(".listing") : null;
    if (listing) listing.classList.remove("dragging");
    dragListing = null;
    clearDragOver();
  });

  document.addEventListener("dragover", function (e) {
    var zone = e.target.closest ? e.target.closest("[data-dropzone]") : null;
    if (!zone || !dragListing) return;
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
    if (!zone || !dragListing) return;
    e.preventDefault();

    var listing = dragListing;
    dragListing = null;

    var targetStage = zone.dataset.stage;
    var sourceStage = listing.dataset.stage;
    if (targetStage === sourceStage) return;

    if (targetStage === "archived") {
      openArchivePrompt(listing, zone);
    } else {
      performMove(listing, zone, targetStage, null, "");
    }
  });

  function openArchivePrompt(listing, zone) {
    if (listing.querySelector(".archive-prompt")) return;

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
    listing.appendChild(prompt);
    listing.classList.add("prompting");
    select.focus();

    function close() {
      prompt.remove();
      listing.classList.remove("prompting");
    }

    confirmBtn.addEventListener("click", function () {
      var reason = select.value;
      var noteText = note.value.trim();
      close();
      performMove(listing, zone, "archived", reason, noteText);
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

  function syncArchiveDisplay(listing, data) {
    var foot = listing.querySelector(".listing-foot");
    var chip = foot.querySelector(".chip");
    var note = listing.querySelector(".listing-note");

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
        note.className = "listing-note";
        foot.parentNode.insertBefore(note, foot);
      }
      note.textContent = data.note;
    } else if (note) {
      note.remove();
    }
  }

  function performMove(listing, zone, targetStage, reason, note) {
    var originalParent = listing.parentNode;
    var originalNext = listing.nextSibling;
    var originalStage = listing.dataset.stage;
    var originalMtime = listing.dataset.mtime;

    var originalDone = listing.classList.contains("is-done");
    var originalDays = listing.dataset.days;

    listing.dataset.stage = targetStage;
    listing.classList.toggle("is-archived", targetStage === "archived");
    setRoundState(listing, false, 0);
    placeListing(zone, listing);
    listing.classList.add("is-moving");
    refreshZone(originalStage);
    refreshZone(targetStage);

    var body = { to: targetStage, note: note || "", mtime: parseFloat(originalMtime) };
    if (reason) body.reason = reason;

    fetch("/api/interview-board/" + encodeURIComponent(listing.dataset.id) + "/stage", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("move failed");
        return res.json();
      })
      .then(function (data) {
        listing.classList.remove("is-moving");
        listing.dataset.mtime = data.mtime;
        setRoundState(listing, data.round_done, data.days);
        syncArchiveDisplay(listing, data);
      })
      .catch(function () {
        listing.classList.remove("is-moving");
        listing.dataset.stage = originalStage;
        listing.classList.toggle("is-archived", originalStage === "archived");
        setRoundState(listing, originalDone, originalDays);
        originalParent.insertBefore(listing, originalNext);
        refreshZone(originalStage);
        refreshZone(targetStage);
        listing.classList.add("drop-error");
        setTimeout(function () { listing.classList.remove("drop-error"); }, 1600);
      });
  }

  function toggleRound(listing) {
    if (listing.classList.contains("is-moving")) return;
    var zone = listing.parentNode;
    var originalNext = listing.nextSibling;
    var originalDone = listing.classList.contains("is-done");
    var originalDays = listing.dataset.days;

    // Optimistic for marking done (the clock restarts at 0); undo waits for the
    // server, since only it knows how long the listing has been in the stage.
    if (!originalDone) {
      setRoundState(listing, true, 0);
      placeListing(zone, listing);
    }
    listing.classList.add("is-moving");

    fetch("/api/interview-board/" + encodeURIComponent(listing.dataset.id) + "/complete", {
      method: originalDone ? "DELETE" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mtime: parseFloat(listing.dataset.mtime) }),
    })
      .then(function (res) {
        if (!res.ok) throw new Error("toggle failed");
        return res.json();
      })
      .then(function (data) {
        listing.classList.remove("is-moving");
        listing.dataset.mtime = data.mtime;
        setRoundState(listing, data.round_done, data.days);
        placeListing(zone, listing);
      })
      .catch(function () {
        listing.classList.remove("is-moving");
        setRoundState(listing, originalDone, originalDays);
        zone.insertBefore(listing, originalNext);
        listing.classList.add("drop-error");
        setTimeout(function () { listing.classList.remove("drop-error"); }, 1600);
      });
  }

  document.addEventListener("click", function (e) {
    var toggle = e.target.closest ? e.target.closest(".round-toggle") : null;
    if (toggle) {
      toggleRound(toggle.closest(".listing"));
      return;
    }
    if (e.target.closest && (e.target.closest(".listing-link") || e.target.closest(".archive-prompt"))) return;
    var listing = e.target.closest ? e.target.closest(".listing[data-id]") : null;
    if (!listing) return;
    window.location.href = "/interview-board/" + encodeURIComponent(listing.dataset.id);
  });
})();
