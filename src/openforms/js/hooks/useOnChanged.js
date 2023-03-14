import isEqual from 'lodash/isEqual';
import {useEffect} from 'react';
import usePrevious from 'react-use/esm/usePrevious';

// FIXME: code is duplicated between this file and components/admin/form_design/logic/hooks

/**
 * Invoke a callback if the value has changed (deep equal comparison).
 */
const useOnChanged = (value, callback) => {
  const previousValue = usePrevious(value);
  useEffect(() => {
    // if it's the first render, do not fire an update
    if (!previousValue) return;
    // if nothing changed, do not fire an update
    if (previousValue && isEqual(previousValue, value)) return;
    callback();
  }, [value]);
};

export default useOnChanged;
