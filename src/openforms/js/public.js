import 'components/auth-mode';
import {onLoaded} from 'utils/dom';

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

// observe whether cookiebanner is in sticky mode or not
// note: rootMargin must be specified in pixels or percent, not REMs/EMs.
const observer = new IntersectionObserver(
  ([e]) => e.target.classList.toggle('stuck', e.intersectionRatio < 1),
  {root: document.querySelector('body'), rootMargin: '0px 0px 31px 0px', threshold: [1]}
);

observer.observe(document.querySelector('.cookie-notice'));

// in case page height is less than the full device height
// (this is a state where the IntersectionObserver will not be triggered, but shadow still needs to be removed)
const hasScrollbar = document.body.scrollHeight > window.innerHeight;

if (hasScrollbar === false) {
  document.querySelector('.cookie-notice').classList.add('no-shadow');
}

// ugly solution that may sent too many requests:

// window.onscroll = function () {
//   var totalPageHeight = document.body.scrollHeight;
//   var scrollPoint = window.scrollY + window.innerHeight;

//   // check if we hit the bottom of the page
//   if (scrollPoint >= totalPageHeight) {
//     console.log('scrolled to the bottom');
//     document.querySelector('.cookie-notice').classList.add('stuck');
//   } else {
//     document.querySelector('.cookie-notice').classList.remove('stuck');
//   }
// };
