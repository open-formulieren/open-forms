import flatpickr from 'flatpickr';
import {Dutch} from 'flatpickr/dist/l10n/nl.js';
import React from 'react';
import {createRoot} from 'react-dom/client';

import AppWrapper, {getWrapperProps} from 'components/admin/AppWrapper';
import {
  clearObsoleteLiterals,
  isNewBuilderComponent,
  persistComponentTranslations,
} from 'components/formio_builder/translation';
import {onLoaded} from 'utils/dom';

import FormIOBuilder from './builder';

onLoaded(async () => {
  const nodes = document.querySelectorAll('.form-builder');
  const wrapperProps = await getWrapperProps();

  const {react_formio_builder_enabled = false} = wrapperProps.featureFlags;

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

    /**
     * Update the translations store when a component is altered.
     */
    const onComponentMutated = (mutationType, schema, ...rest) => {
      let configuration;

      switch (mutationType) {
        case 'changed': {
          configuration = rest[1];
          break;
        }
        case 'removed': {
          configuration = rest[0];
          break;
        }
        default:
          throw new Error(`Unknown mutation type '${mutationType}'`);
      }

      if (!react_formio_builder_enabled || !isNewBuilderComponent(schema)) {
        persistComponentTranslations(componentTranslations, schema);
        componentTranslations = clearObsoleteLiterals(componentTranslations, configuration);
        componentTranslationsInput.value = JSON.stringify(componentTranslations);
      }
    };
    const root = createRoot(node.querySelector('.form-builder__container'));
    root.render(
      <AppWrapper {...wrapperProps}>
        <FormIOBuilder
          configuration={configuration}
          onChange={onChange}
          onComponentMutated={onComponentMutated}
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
