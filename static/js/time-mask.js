/**
 * time-mask.js
 * ------------
 * Forces a text input into "HH:MM" shape as the user types, without
 * ever requiring them to type the ":" themselves.
 *
 * Why this exists: on many Android keyboards (especially with
 * inputmode="numeric", which shows a digits-only pad) there is no ":"
 * key available. If a user clears the field and starts typing digits
 * again, they get stuck unable to complete a valid "HH:MM" value.
 *
 * The fix is to never rely on the user typing the separator at all -
 * we only look at the digits they've entered and re-insert the ":"
 * automatically after the first two digits. Because the mask is
 * always rebuilt from "digits only" on every keystroke, backspacing
 * over a digit *or* over the auto-inserted ":" both behave correctly,
 * which is what makes this robust on Android (where "keydown" events
 * are unreliable) - we only listen to the "input" event, which every
 * browser/keyboard fires consistently.
 */
(function () {
  function applyTimeMask(input) {
    if (!input || input.dataset.timeMaskAttached === "1") return;
    input.dataset.timeMaskAttached = "1";

    input.setAttribute("maxlength", "5");
    input.setAttribute("autocomplete", "off");
    input.setAttribute("autocorrect", "off");
    input.setAttribute("autocapitalize", "off");
    input.setAttribute("spellcheck", "false");
    if (!input.getAttribute("inputmode")) {
      input.setAttribute("inputmode", "numeric");
    }

    input.addEventListener("input", function () {
      const cursorWasAtEnd = input.selectionStart === input.value.length;

      // Rebuild purely from the digits present - this is what makes
      // both typing and backspacing (over digits AND over the ":")
      // work the same way, regardless of platform/keyboard.
      const digits = input.value.replace(/\D/g, "").slice(0, 4);
      const formatted =
        digits.length > 2 ? digits.slice(0, 2) + ":" + digits.slice(2) : digits;

      input.value = formatted;

      if (cursorWasAtEnd) {
        input.setSelectionRange(formatted.length, formatted.length);
      }
    });
  }

  function initTimeMasks() {
    document.querySelectorAll('[data-mask="time"]').forEach(applyTimeMask);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTimeMasks);
  } else {
    initTimeMasks();
  }

  // Exposed in case a page needs to attach the mask to a field that's
  // added to the DOM dynamically after the initial page load.
  window.applyTimeMask = applyTimeMask;
})();
