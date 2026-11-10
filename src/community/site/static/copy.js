// Copy buttons for invite links. The page works without this; it only adds the button.
document.querySelectorAll('[data-copy]').forEach(function (btn) {
  var field = document.getElementById(btn.getAttribute('data-copy'));
  if (!field || !navigator.clipboard) return;
  btn.hidden = false;
  btn.addEventListener('click', function () {
    navigator.clipboard.writeText(field.value).then(function () {
      btn.textContent = 'Copied';
      setTimeout(function () { btn.textContent = 'Copy'; }, 1600);
    });
  });
});
