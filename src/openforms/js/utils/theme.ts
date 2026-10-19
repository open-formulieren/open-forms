import {createGlobalstate} from 'state-pool';

import {onLoaded} from '@/utils/dom';

export type OFTheme = 'light' | 'dark';

// in case django renames or adds themes in the future - maintain a mapping to convert
// to OF theme
type DjangoAdminTheme = 'light' | 'dark';
const THEME_MAPPING_FROM_DJANGO: Record<DjangoAdminTheme, OFTheme> = {
  light: 'light',
  dark: 'dark',
};

/**
 * Detect the active theme in JS so that the correct theme can be applied in places
 * that are not simply styled through CSS.
 */
const detectTheme = (): OFTheme => {
  // See Django's admin/js/theme.js
  const theme: string = window.localStorage.getItem('theme') || 'auto';
  switch (theme) {
    case 'light': {
      return THEME_MAPPING_FROM_DJANGO.light;
    }
    case 'dark': {
      return THEME_MAPPING_FROM_DJANGO.dark;
    }
  }
  // in auto (or unknown) mode, we need to look at the media query
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  return prefersDark ? 'dark' : 'light';
};

/**
 * Watches for changes to the data attribute of the html element.
 *
 * Note that we cannot use the storage event, as that is meant as a synchronization
 * mechanism across tabs. It does not work in the same tab/window.
 */
const watchForThemeChanges = () => {
  const htmlNode: HTMLElement = document.documentElement; // the html node

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

export const currentTheme = createGlobalstate<OFTheme>(detectTheme());
