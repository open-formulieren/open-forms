import {onLoaded} from 'utils/dom';

const addAdminLoginExpand = () => {
  const defaultLoginToggle = document.querySelector('.admin-login-option--password');
  const loginForm = document.querySelector('#login-form');

  if (defaultLoginToggle && loginForm) {
    defaultLoginToggle.addEventListener('click', e => {
      e.preventDefault();
      loginForm.classList.toggle('login-form--enabled');
      defaultLoginToggle.classList.toggle('admin-login-option--disabled');
    });
  }
};

onLoaded(addAdminLoginExpand);
