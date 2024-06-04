const defaultLogin = document.querySelector('.admin-login-password');
const loginForm = document.querySelector('#login-form');

if (defaultLogin && loginForm) {
  defaultLogin.addEventListener('click', e => {
    loginForm.style.display = 'block';
    defaultLogin.style.display = 'none';
  });
}
