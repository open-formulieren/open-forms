import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {Tabs, TabList, TabPanel} from 'react-tabs';

import {FormContext} from './Context';
import Tab from './Tab';

/**
 * Wrap the children provided to the component in language tabs.
 *
 * The LanguageTabs component takes the available languages into account and repeats
 * the component tree provided as children for every language, taking into account the
 * appropriate change events.
 *
 * Any additional props provided are forwarded to the react-tabs Tabs component.
 *
 * @param  {Object} props.children The nested component tree to repeat for every language
 * @return {JSX}                   Renders a tabbed interface with a tab for every supported language.
 */
const LanguageTabs = ({children, ...props}) => {
  const {languages} = useContext(FormContext);

  return (
    <Tabs className="react-tabs react-tabs--translations" {...props}>
      <TabList>
        {languages.map(language => (
          <Tab key={language.code} title={language.name}>
            {language.code}
          </Tab>
        ))}
      </TabList>

      {languages.map(language => (
        <TabPanel key={language.code}>{children(language.code)}</TabPanel>
      ))}
    </Tabs>
  );
};

LanguageTabs.propTypes = {
  children: PropTypes.func,
};

export default LanguageTabs;
