(function () {
  var root = document.querySelector(".detail");
  var cardId = root.dataset.id;
  var mtime = parseFloat(root.dataset.mtime);

  function showState(el, text, ok) {
    el.textContent = text;
    el.classList.toggle("state-error", !ok);
    el.classList.toggle("state-ok", ok);
    window.clearTimeout(el._fadeTimer);
    el._fadeTimer = window.setTimeout(function () { el.textContent = ""; }, 1800);
  }

  function patch(url, body, stateEl, onOk) {
    body.mtime = mtime;
    fetch(url, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (res) {
        if (res.status === 409) {
          showState(stateEl, "Changed elsewhere — reloading…", false);
          window.setTimeout(function () { window.location.reload(); }, 1200);
          throw new Error("conflict");
        }
        if (!res.ok) throw new Error("save failed");
        return res.json();
      })
      .then(function (data) {
        mtime = data.mtime;
        showState(stateEl, "Saved", true);
        if (onOk) onOk(data);
      })
      .catch(function (err) {
        if (err.message !== "conflict") showState(stateEl, "Save failed", false);
      });
  }

  // Notes
  var notes = document.getElementById("notes");
  var notesState = document.getElementById("notes-state");
  notes.addEventListener("blur", function () {
    patch("/api/cards/" + encodeURIComponent(cardId), { notes: notes.value }, notesState);
  });

  // Referral
  var refStatus = document.getElementById("ref-status");
  var refVia = document.getElementById("ref-via");
  var refChecked = document.getElementById("ref-checked");
  var refState = document.getElementById("referral-state");

  function saveReferral() {
    patch(
      "/api/cards/" + encodeURIComponent(cardId),
      { referral: { status: refStatus.value, via: refVia.value, checked: refChecked.value || null } },
      refState
    );
  }
  refStatus.addEventListener("change", saveReferral);
  refVia.addEventListener("blur", saveReferral);
  refChecked.addEventListener("change", saveReferral);

  // Contacts
  var contactsList = document.getElementById("contacts-list");
  var contactsState = document.getElementById("contacts-state");

  function collectContacts() {
    return Array.prototype.slice
      .call(contactsList.querySelectorAll(".contact-row"))
      .map(function (row) {
        return {
          name: row.querySelector(".c-name").value.trim(),
          role: row.querySelector(".c-role").value.trim(),
          note: row.querySelector(".c-note").value.trim(),
        };
      })
      .filter(function (c) { return c.name; });
  }

  function saveContacts() {
    patch("/api/cards/" + encodeURIComponent(cardId), { contacts: collectContacts() }, contactsState);
  }

  contactsList.addEventListener(
    "blur",
    function (e) {
      if (e.target.tagName === "INPUT") saveContacts();
    },
    true
  );

  document.getElementById("add-contact").addEventListener("click", function () {
    var row = document.createElement("div");
    row.className = "contact-row";
    row.innerHTML =
      '<input type="text" class="c-name" placeholder="Name">' +
      '<input type="text" class="c-role" placeholder="Role">' +
      '<input type="text" class="c-note" placeholder="Note">' +
      '<button type="button" class="btn ghost remove-contact">Remove</button>';
    contactsList.appendChild(row);
    row.querySelector(".c-name").focus();
  });

  contactsList.addEventListener("click", function (e) {
    var btn = e.target.closest ? e.target.closest(".remove-contact") : null;
    if (!btn) return;
    btn.closest(".contact-row").remove();
    saveContacts();
  });

  // History
  var timeline = document.getElementById("timeline");

  function saveHistoryRow(row) {
    var index = row.dataset.index;
    var occurred = row.querySelector(".h-occurred").value;
    var note = row.querySelector(".h-note").value;
    var stateEl = row.querySelector(".save-state");
    patch(
      "/api/cards/" + encodeURIComponent(cardId) + "/history/" + index,
      { occurred: occurred, note: note },
      stateEl
    );
  }

  timeline.addEventListener(
    "blur",
    function (e) {
      if (e.target.tagName === "INPUT") saveHistoryRow(e.target.closest(".timeline-row"));
    },
    true
  );
})();
