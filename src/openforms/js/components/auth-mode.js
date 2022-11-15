import {onLoaded} from 'utils/dom';

const onModeSelect = event => {
  const {value: mode, checked} = event.target;
  if (!checked) return;

  const nodesToHide = document.querySelectorAll(`.auth-mode:not(.auth-mode--${mode})`);
  nodesToHide.forEach(node => {
    node.classList.remove('auth-mode--active');
    node.querySelectorAll('input').forEach(input => (input.value = ''));
  });

  const nodesToShow = document.querySelectorAll(`.auth-mode.auth-mode--${mode}`);
  nodesToShow.forEach(node => node.classList.add('auth-mode--active'));
};

const init = () => {
  const radios = document.querySelectorAll('#registrator-subject [name="mode"]');
  if (!radios.length) return;

  radios.forEach(node => {
    node.addEventListener('change', onModeSelect);
    node.dispatchEvent(new Event('change'));
  });
};

onLoaded(init);
