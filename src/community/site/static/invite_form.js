// The leader's "Make an invite" form: picking "QR code for an event" ticks "Guests can join
// with just their name" (on by default for meetings); picking "Link to share" unticks it,
// until the leader sets it by hand. Without JavaScript the box simply starts unticked.
(function () {
  var box = document.getElementById("guest_ok");
  if (!box) return;
  var touched = false;
  box.addEventListener("change", function () { touched = true; });
  var radios = document.querySelectorAll('input[name="kind"]');
  function sync() {
    if (touched) return;
    var picked = document.querySelector('input[name="kind"]:checked');
    box.checked = !!picked && picked.value === "event";
  }
  for (var i = 0; i < radios.length; i++) radios[i].addEventListener("change", sync);
  sync();
})();
