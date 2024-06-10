import isEqual from 'lodash/isEqual';
import {useContext, useState} from 'react';
import useDebounce from 'react-use/esm/useDebounce';

import {get} from 'utils/fetch';

import {FormContext} from './Context';
import {stripIdFromComponents} from './utils';

// debounce changes for 100ms
const DEBOUNCE_MS = 100;

const useDetectConfigurationChanged = (url, configuration) => {
  const formContext = useContext(FormContext);
  const {url: formUrl} = formContext.form;
  const [changed, setChanged] = useState(false);
  const [affectedForms, setAffectedForms] = useState([]);

  // FormIO generates new IDs on changes, so we can't include those in equality comparisons
  const configurationWithoutId = stripIdFromComponents(configuration);

  // the configuration object reference changes all the time, but String objects
  // are primitives and passed by value, so that should avoid triggering all the time
  const serializedConfiguration = JSON.stringify(configurationWithoutId);

  useDebounce(
    async () => {
      if (!url) return;
      const response = await get(url);
      const existingConfigWithoutId = stripIdFromComponents(response.data.configuration);
      const definitionChanged = !isEqual(existingConfigWithoutId, configurationWithoutId);
      const affectedForms = definitionChanged
        ? response.data.usedIn.filter(affectedForm => affectedForm.url !== formUrl)
        : [];
      setChanged(affectedForms.length > 0);
      setAffectedForms(affectedForms);
    },
    DEBOUNCE_MS,
    [url, serializedConfiguration]
  );

  return {
    changed,
    affectedForms,
  };
};

export default useDetectConfigurationChanged;
