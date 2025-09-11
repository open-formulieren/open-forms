import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import ReactSelect from 'components/admin/forms/ReactSelect';

export const Merchant = ({options}) => (
  <FormRow>
    <Field
      name="merchant"
      label={
        <FormattedMessage
          description="Worldline payment options 'merchant' label"
          defaultMessage="Merchant"
        />
      }
      helpText={
        <FormattedMessage
          description="Worldline payment options 'merchant' help text"
          defaultMessage="Which merchant should be used for payments related to this form."
        />
      }
      required
    >
      <ReactSelect name="merchant" options={options} required />
    </Field>
  </FormRow>
);

Merchant.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};

export const Variant = () => {
  const [fieldProps] = useField('variant');

  return (
    <FormRow>
      <Field
        name="variant"
        label={
          <FormattedMessage
            description="Worldline payment options 'variant' label"
            defaultMessage="Variant"
          />
        }
        helpText={
          <FormattedMessage
            description="Worldline payment options 'variant' help text"
            defaultMessage={`Which template variant should be used for payments related to this form.
            This can be found under the "Variant name" field in the "Branding" section.`}
          />
        }
      >
        <TextInput {...fieldProps} />
      </Field>
    </FormRow>
  );
};

Variant.propTypes = {};

export const DescriptorTemplate = () => {
  const [fieldProps] = useField('descriptorTemplate');
  return (
    <FormRow>
      <Field
        name="descriptorTemplate"
        label={
          <FormattedMessage
            description="Worldline payment options 'descriptorTemplate' label"
            defaultMessage="Payment descriptor"
          />
        }
        helpText={
          <FormattedMessage
            description="Worldline payment options 'descriptorTemplate' help text"
            defaultMessage={`Optional custom template for the description, included in the
            payment overviews for the backoffice. Use this to link the payment back to a particular
            process or form.<br></br>
            You can include form variables (using their keys) and the public-reference variable
            (using expression <code>'{{' public_reference '}}'</code>). If unspecified, a default
            description is used.<br></br>
            <strong>Note</strong>: the length of the result is capped to 32 characters.`}
            values={{
              br: () => <br />,
              code: chunks => <code>{chunks}</code>,
              strong: chunks => <strong>{chunks}</strong>,
            }}
          />
        }
      >
        <TextInput {...fieldProps} />
      </Field>
    </FormRow>
  );
};

DescriptorTemplate.propTypes = {};
