import {createGlobalstate} from 'state-pool';

import {onLoaded} from 'utils/dom';

export const THEMES = {
  light: 'light',
  dark: 'dark',
};

/**
 * Detect the active theme in JS so that the correct theme can be applied in places
 * that are not simply styled through CSS.
 */
const detectTheme = () => {
  // See admin/js/theme.js
  const theme = window.localStorage.getItem('theme') || 'auto';

  if (theme !== 'auto') {
    // normalize to our 'constants' in case django renames themes in the future
    return THEMES[theme];
  }

  // in auto mode, we need to look at the media query
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  return prefersDark ? THEMES.dark : THEMES.light;
};

/**
 * Watches for changes to the data attribute of the html element.
 *
 * Note that we cannot use the storage event, as that is meant as a synchronization
 * mechanism across tabs. It does not work in the same tab/window.
 */
const watchForThemeChanges = () => {
  const htmlNode = document.documentElement; // the html node

  const observer = new MutationObserver(() => {
    const newTheme = detectTheme();
    currentTheme.updateValue(() => newTheme);
  });

  observer.observe(htmlNode, {
    attributes: true,
    attributeFilter: ['data-theme'],
  });
};

onLoaded(watchForThemeChanges);

export const currentTheme = createGlobalstate(detectTheme());
