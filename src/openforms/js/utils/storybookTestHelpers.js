import selectEvent from 'react-select-event';

const SB_ROOT = document.getElementById('storybook-root');

/**
 * Wrapper around selectEvent.select to ensure the portal option is used.
 */
const rsSelect = async (input, optionOrOptions) => {
  await selectEvent.select(input, optionOrOptions, {container: SB_ROOT});
};

/**
 * From the input field (retrieved by accessible queries), find the react-select container.
 *
 * Equivalent of https://github.com/romgain/react-select-event/blob/8619e8b3da349eadfa7321ea4aa2b7eee7209f9f/src/index.ts#L14,
 * however instead of relying on the DOM structure we can leverage class names that are
 * guaranteed to be set by us.
 *
 * Usage:
 *
 * const dropdown = canvas.getByLabelText('My dropdown');
 * const container = getReactSelectContainer(dropdown);
 * const options = within(container).queryByRole('option');
 */
const getReactSelectContainer = comboboxInput => {
  const container = comboboxInput.closest('.admin-react-select');
  return container;
};

/**
 * Get the (portaled) opened react select menu.
 */
const findReactSelectMenu = async canvas => {
  return await canvas.findByRole('listbox');
};

export {rsSelect, getReactSelectContainer, findReactSelectMenu};
