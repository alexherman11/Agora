// shell-separator: a thin rule between groups of the dock (or the bar).
export default {mount(api) {
  return api.part('body', 'i', { class: 'sep', 'aria-hidden': 'true' });
}};
