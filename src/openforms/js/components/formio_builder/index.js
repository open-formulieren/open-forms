import flatpickr from 'flatpickr';
import {Dutch} from 'flatpickr/dist/l10n/nl.js';
import React from 'react';
import {createRoot} from 'react-dom/client';

import AppWrapper, {getWrapperProps} from 'components/admin/AppWrapper';
import {onLoaded} from 'utils/dom';

import FormIOBuilder from './builder';

onLoaded(async () => {
  const nodes = document.querySelectorAll('.form-builder');
  const wrapperProps = await getWrapperProps();

  for (const node of nodes) {
    const configurationInput = node.querySelector('.form-builder__configuration-input');
    const componentTranslationsInput = node
      .closest('form')
      .querySelector('.form-builder__component-translations');

    const configuration = JSON.parse(configurationInput.value) || {display: 'form'};
    let componentTranslations = JSON.parse(componentTranslationsInput.value) || {};

    const onChange = newConfiguration => {
      // extract translations
      configurationInput.value = JSON.stringify(newConfiguration);
    };

    const root = createRoot(node.querySelector('.form-builder__container'));
    root.render(
      <AppWrapper {...wrapperProps}>
        <FormIOBuilder
          configuration={configuration}
          onChange={onChange}
          componentTranslations={componentTranslations}
        />
      </AppWrapper>
    );
  }

  initFlatpickr();
});

const initFlatpickr = () => {
  flatpickr.localize(Dutch);
};
