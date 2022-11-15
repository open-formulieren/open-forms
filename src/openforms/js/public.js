import {onLoaded} from 'utils/dom';

import 'components/auth-mode';

// connect the "Print this page" link element to a handler
const registerPrintHandler = () => {
  const nodes = document.querySelectorAll('.a11y-toolbar__window-print-action');
  nodes.forEach(node => {
    node.addEventListener('click', event => {
      event.preventDefault();
      window.print();
    });
  });
};

const init = () => {
  registerPrintHandler();
};

onLoaded(init);
