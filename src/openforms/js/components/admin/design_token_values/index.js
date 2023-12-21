import React from 'react';
import {createRoot} from 'react-dom/client';
import ReactModal from 'react-modal';

import AppWrapper, {getWrapperProps} from 'components/admin/AppWrapper';
import {onLoaded} from 'utils/dom';

import DesignTokenValues from './DesignTokenValues';

const SELECTOR = '.react-design-token-values';

const init = async () => {
  const nodes = document.querySelectorAll(SELECTOR);
  if (!nodes.length) return;

  const wrapperProps = await getWrapperProps();

  for (const node of nodes) {
    const initialValue = JSON.parse(node.value) || {};

    // replace the textarea with a div containing the react root + cloned original div
    const container = node.parentNode;
    const clonedTextArea = node.cloneNode(true);
    const replacement = document.createElement('div');
    replacement.classList.add('column-field-value');
    const reactRoot = document.createElement('div');
    replacement.appendChild(reactRoot);
    replacement.appendChild(clonedTextArea);
    container.replaceChild(replacement, node);
    const root = createRoot(reactRoot);

    const onChange = newValues => {
      const serialized = JSON.stringify(newValues, null, 2);
      clonedTextArea.value = serialized;
      render(newValues);
    };

    const render = value => {
      root.render(
        <AppWrapper {...wrapperProps}>
          <DesignTokenValues initialValue={value} onChange={onChange} />
        </AppWrapper>
      );
    };

    // call onChange once to get the pretty formatting
    onChange(initialValue);
    render(initialValue);
  }

  const main = document.getElementById('content-main');
  ReactModal.setAppElement(main);
};

onLoaded(init);
