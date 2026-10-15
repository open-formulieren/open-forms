import type {OFTheme} from '@/utils/theme';

interface ThemeOptions {
  skin: string;
  content_css: string;
}

const APPEARANCE: Record<OFTheme, ThemeOptions> = {
  light: {
    skin: 'oxide',
    content_css: 'default',
  },
  dark: {
    skin: 'oxide-dark',
    content_css: 'dark',
  },
};

const getTinyMCEAppearance = (theme: OFTheme): ThemeOptions => {
  return APPEARANCE[theme];
};

export default getTinyMCEAppearance;
