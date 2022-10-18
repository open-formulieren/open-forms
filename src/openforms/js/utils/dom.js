const onLoaded = callback => {
  if (document.readyState !== 'loading') {
    callback();
  } else {
    document.addEventListener('DOMContentLoaded', event => callback());
  }
};

export {onLoaded};
