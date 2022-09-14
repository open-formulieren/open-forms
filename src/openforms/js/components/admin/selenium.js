const ID = 'selenium-test-id';

const setSeleniumMarker = () => {
  const seleniumMarker = document.createElement('div');
  seleniumMarker.setAttribute('id', ID);
  document.body.appendChild(seleniumMarker);
};

const init = () => {
  if (document.readyState !== 'loading') {
    setSeleniumMarker();
  } else {
    document.addEventListener('DOMContentLoaded', setSeleniumMarker);
  }
};

export default init;
