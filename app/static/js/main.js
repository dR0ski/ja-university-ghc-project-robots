/* Robotik — minimal progressive enhancement.
   Form still works without JS. */
(function () {
  "use strict";

  // Disable submit buttons on form submit so impatient users don't double-post.
  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    var btn = form.querySelector("[data-disable-on-submit]");
    if (btn) {
      // setTimeout so the button still submits the form before being disabled.
      setTimeout(function () {
        btn.setAttribute("disabled", "disabled");
        btn.setAttribute("aria-disabled", "true");
      }, 0);
    }
  });
})();
