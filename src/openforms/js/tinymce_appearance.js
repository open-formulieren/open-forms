import {THEMES, detectTheme} from 'utils/theme';

const APPEARANCE = {
  [THEMES.light]: {
    skin: 'oxide',
    content_css: 'default',
  },
  [THEMES.dark]: {
    skin: 'oxide-dark',
    content_css: 'dark',
  },
};

const getTinyMCEAppearance = (theme = detectTheme()) => {
  return APPEARANCE[theme];
};

export default getTinyMCEAppearance;
