import {onLoaded} from 'utils/dom';

const ID = 'selenium-test-id';

const setSeleniumMarker = () => {
  const seleniumMarker = document.createElement('div');
  seleniumMarker.setAttribute('id', ID);
  document.body.appendChild(seleniumMarker);
};

const init = () => {
  onLoaded(setSeleniumMarker);
};

export default init;
