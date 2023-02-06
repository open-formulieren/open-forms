import {onLoaded} from 'utils/dom';

const ID = 'e2e-test-id';

const setE2ETestMarker = () => {
  const E2ETestMarker = document.createElement('div');
  E2ETestMarker.setAttribute('id', ID);
  E2ETestMarker.setAttribute('data-testid', ID);
  document.body.appendChild(E2ETestMarker);
};

const init = () => {
  onLoaded(setE2ETestMarker);
};

export default init;
