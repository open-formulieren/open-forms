const init = () => {
  // connect the "Print this page" link element to a handler
  document.querySelectorAll('.a11y-toolbar__window-print-action').forEach(elem => {
    elem.addEventListener('click', event => {
      window.print();
    });
  });
};

if (document.readyState !== 'loading') {
  init();
} else {
  document.addEventListener('DOMContentLoaded', init);
}
