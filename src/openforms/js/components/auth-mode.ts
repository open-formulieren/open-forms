import {onLoaded} from '@/utils/dom';

const onModeSelect = (event: Event): void => {
  const input = event.currentTarget;
  if (!(input instanceof HTMLInputElement)) {
    throw new Error('Expected a (radio) input');
  }
  const {value: mode, checked} = input;
  if (!checked) return;

  const nodesToHide = document.querySelectorAll(`.auth-mode:not(.auth-mode--${mode})`);
  nodesToHide.forEach(node => {
    node.classList.remove('auth-mode--active');
    node.querySelectorAll('input').forEach(input => (input.value = ''));
  });

  const nodesToShow = document.querySelectorAll(`.auth-mode.auth-mode--${mode}`);
  nodesToShow.forEach(node => node.classList.add('auth-mode--active'));
};

const init = (): void => {
  const radios = document.querySelectorAll<HTMLInputElement>('#registrator-subject [name="mode"]');
  if (!radios.length) return;

  radios.forEach(node => {
    node.addEventListener('change', onModeSelect);
    node.dispatchEvent(new Event('change'));
  });
};

onLoaded(init);
