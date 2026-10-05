import {setProjectAnnotations} from '@storybook/react-vite';
import * as reactIntlAnnotations from 'storybook-react-intl/preview';
import {beforeAll} from 'vitest';

import * as projectAnnotations from './.storybook/preview';

// This is an important step to apply the right configuration when testing your stories.
// More info at: https://storybook.js.org/docs/api/portable-stories/portable-stories-vitest#setprojectannotations
const annotations = setProjectAnnotations([reactIntlAnnotations, projectAnnotations]);

beforeAll(annotations.beforeAll);
