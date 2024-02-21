import {produce} from 'immer';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';

import {CustomFieldTemplate} from 'components/admin/RJSFWrapper';
import Tab from 'components/admin/form_design/Tab';

import LegacyConfigFields from './LegacyConfigFields';
import V2ConfigFields from './V2ConfigFields';

const Wrapper = ({children}) => (
  <form className="rjsf" name="form.registrationBackendOptions">
    <CustomFieldTemplate displayLabel={false} errors={null}>
      <fieldset id="root">{children}</fieldset>
    </CustomFieldTemplate>
  </form>
);

const ObjectsApiOptionsFormFields = ({index, name, schema, formData, onChange}) => {
  const intl = useIntl();

  const v2SwitchMessage = intl.formatMessage({
    defaultMessage: `Switching to the new registration options will remove the existing JSON templates.
    You will also not be able to save the form until the variables are correctly mapped.
    Are you sure you want to continue?
    `,
    description: 'Objects API registration backend: v2 switch warning message',
  });

  const {version = 1} = formData;

  const changeVersion = index => {
    if (index === 1) {
      const confirmV2Switch = window.confirm(v2SwitchMessage);
      if (!confirmV2Switch) return;
    }

    onChange(
      produce(formData, draft => {
        draft.version = index + 1;
        delete draft.contentJson;
        delete draft.paymentStatusUpdateJson;
      })
    );
  };

  const onFieldChange = event => {
    const {name, value} = event.target;
    const updatedFormData = produce(formData, draft => {
      draft[name] = value;
    });
    onChange(updatedFormData);
  };

  return (
    <>
      <Tabs selectedIndex={version - 1} onSelect={changeVersion}>
        <TabList>
          <Tab>
            <FormattedMessage
              defaultMessage="Legacy"
              description="Objects API registration backend options 'Legacy' tab label"
            />
          </Tab>
          <Tab>
            <FormattedMessage
              defaultMessage="Variables Mapping"
              description="Objects API registration backend options 'Variables Mapping' tab label"
            />
          </Tab>
        </TabList>

        {/* Legacy format, template based */}
        <TabPanel>
          <Wrapper>
            <LegacyConfigFields
              index={index}
              name={name}
              formData={formData}
              onChange={onFieldChange}
            />
          </Wrapper>
        </TabPanel>

        {/* Tight objecttypes integration */}
        <TabPanel>
          <Wrapper>
            <V2ConfigFields
              index={index}
              name={name}
              formData={formData}
              onChange={onFieldChange}
            />
          </Wrapper>
        </TabPanel>
      </Tabs>
    </>
  );
};

export default ObjectsApiOptionsFormFields;
