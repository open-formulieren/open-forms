import {showCookieBar} from 'django-cookie-consent';

import 'components/auth-mode';
import {onLoaded} from 'utils/dom';

// connect the "Print this page" link element to a handler
const registerPrintHandler = () => {
  const node = document.getElementById('print-button');
  node.addEventListener('click', event => {
    event.preventDefault();
    window.print();
  });
};

const initCookieBar = () => {
  const templateNode = document.getElementById('cookie-consent__cookie-bar');
  if (!templateNode) return;

  const {varName, statusUrl} = templateNode.dataset;
  showCookieBar({
    statusUrl,
    templateSelector: '#cookie-consent__cookie-bar',
    cookieGroupsSelector: '#cookie-consent__cookie-groups',
    acceptSelector: '.cookie-notice__accept',
    declineSelector: '.cookie-notice__decline',
    insertBefore: '#cookie-consent__cookie-bar',
    onAccept: groups => {
      const isAnalyticsEnabled = groups.find(group => group.varname === varName);
      if (!isAnalyticsEnabled) return;
      const analyticsTemplateNodes = document.querySelectorAll('.analytics-scripts');
      analyticsTemplateNodes.forEach(templateNode => {
        const clone = templateNode.content.cloneNode(true);
        templateNode.parentNode.insertBefore(clone, templateNode);
      });
    },
  });
};

const init = () => {
  registerPrintHandler();
  initCookieBar();
};

onLoaded(init);
