import {onLoaded} from 'utils/dom';

const addAdminLoginExpand = () => {
  const defaultLoginToggle = document.querySelector('.admin-login-option--password');
  const loginForm = document.querySelector('#login-form');

  if (defaultLoginToggle && loginForm) {
    const showLoginForm = () => {
      loginForm.classList.toggle('login-form--enabled');
      defaultLoginToggle.classList.toggle('admin-login-option--disabled');
    };

    // bind click event
    defaultLoginToggle.addEventListener('click', e => {
      e.preventDefault();
      showLoginForm();
    });

    // if the form is bound, there is feedback, so toggle it to visible
    const {bound, wizardstep} = defaultLoginToggle.dataset;
    if (bound === 'true' || wizardstep !== 'auth') {
      showLoginForm();
    }
  }
};

onLoaded(addAdminLoginExpand);
