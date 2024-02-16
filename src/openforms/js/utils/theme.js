export const THEMES = {
  light: 'light',
  dark: 'dark',
};

/**
 * Detect the active theme in JS so that the correct theme can be applied in places
 * that are not simply styled through CSS.
 */
export const detectTheme = () => {
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
