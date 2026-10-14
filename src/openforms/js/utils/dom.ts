const onLoaded = (callback: (e?: Event) => void) => {
  if (document.readyState !== 'loading') {
    callback();
  } else {
    document.addEventListener('DOMContentLoaded', callback);
  }
};

export {onLoaded};
