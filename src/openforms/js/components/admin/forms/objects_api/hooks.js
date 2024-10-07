import {useFormikContext} from 'formik';
import {useEffect} from 'react';

/**
 * Ensure that if no valid value is set, the first possible option is selected.
 *
 * This synchronizes the form field state with the UI state, since selects with no
 * empty/blank option display the first option as if it was selected, which isn't
 * guaranteed to be the case in the form state.
 */
// synchronizing the UI state back to the form state, because a select displays the
// first possible option as if it's actually selected)
export const useSynchronizeSelect = (name, loading, choices) => {
  const {getFieldProps, getFieldHelpers} = useFormikContext();

  const {value: currentValue} = getFieldProps(name);
  const {setValue} = getFieldHelpers(name);

  useEffect(() => {
    // do nothing if no options have been loaded
    if (loading || !choices.length) return;
    // check if a valid option is selected, if this is the case -> do nothing
    const isOptionPresent = choices.find(([optionValue]) => optionValue === currentValue);
    if (isOptionPresent) return;

    // otherwise select the first possible option and persist that back into the state
    setValue(choices[0][0]);
  });
};
