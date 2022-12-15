import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import {FormContext} from './Context';
import Tab from './Tab';

// TODO: expose this in API
const DEFAULT_LANGUAGE = 'nl';

/**
 * Wrap the children provided to the component in language tabs.
 *
 * The LanguageTabs component takes the available languages into account and repeats
 * the component tree provided as children for every language, taking into account the
 * appropriate change events.
 *
 * Any additional props provided are forwarded to the react-tabs Tabs component.
 *
 * @param  {Array}  props.haveErrors Array of language codes that have (validation) errors
 * @param  {Object} props.children The nested component tree to repeat for every language
 * @return {JSX}                   Renders a tabbed interface with a tab for every supported language.
 */
const LanguageTabs = ({haveErrors = [], children, ...props}) => {
  const {languages} = useContext(FormContext);

  return (
    <Tabs className="react-tabs react-tabs--translations" {...props}>
      <TabList>
        {languages.map(language => (
          <Tab
            key={language.code}
            title={language.name}
            hasErrors={haveErrors.includes(language.code)}
          >
            {language.code}
          </Tab>
        ))}
      </TabList>

      {languages.map(language => (
        <TabPanel key={language.code}>{children(language.code, DEFAULT_LANGUAGE)}</TabPanel>
      ))}
    </Tabs>
  );
};

LanguageTabs.propTypes = {
  haveErrors: PropTypes.arrayOf(PropTypes.string),
  children: PropTypes.func,
};

export {DEFAULT_LANGUAGE};
export default LanguageTabs;
