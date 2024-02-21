import {THEMES} from 'utils/theme';

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

const getTinyMCEAppearance = theme => {
  return APPEARANCE[theme];
};

export default getTinyMCEAppearance;
