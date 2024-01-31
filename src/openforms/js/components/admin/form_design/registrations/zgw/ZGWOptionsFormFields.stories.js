import {useArgs} from '@storybook/client-api';

import {FormDecorator} from 'components/admin/form_design/story-decorators';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';

import ZGWFormFields from './ZGWOptionsFormFields';
import VariablePropertyModal from './ZGWOptionsVariablesProperties';

const render = ({index, label, name, schema}) => {
  const [{formData}, updateArgs] = useArgs();
  const onChange = newValues => {
    updateArgs({formData: newValues});
  };

  return (
    <Fieldset>
      <FormRow>
        <Field name={name} label={label}>
          <ZGWFormFields
            index={index}
            name={name}
            schema={schema}
            formData={formData}
            onChange={onChange}
          />
        </Field>
      </FormRow>
    </Fieldset>
  );
};

export default {
  title: 'Form design/Registration/ZGW',
  component: VariablePropertyModal,
  decorators: [FormDecorator],
  render,
  args: {
    schema: {
      properties: {
        zgwApiGroup: {
          enum: [1],
          enumNames: ['ZGW API'],
        },
        contentJson: '',
        informatieobjecttype: '',
        medewerkerRoltype: '',
        objecttype: '',
        objecttypeVersion: '',
        organisatieRsin: '',
        propertyMappings: [
          {
            componentKey: '',
            eigenschap: '',
          },
        ],
        zaakVertrouwelijkheidaanduiding: {
          enum: ['openbaar'],
          enumNames: ['Openbaar'],
        },
        zaaktype: 'http://example.com',
      },
    },
    formData: {
      propertyMappings: [{eigenschap: '', componentKey: ''}],
      zaaktype: '',
    },
    availableComponents: {
      textField1: {
        label: 'textfield1',
      },
      textField2: {
        label: 'textfield2',
      },
    },
  },
};

export const Default = {};
