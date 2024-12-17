import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import ReactSelect from 'components/admin/forms/ReactSelect';

export const MerchantID = ({options}) => (
  <FormRow>
    <Field
      name="merchantId"
      label={
        <FormattedMessage
          description="Ogone legacy payment options 'merchantId' label"
          defaultMessage="Merchant ID"
        />
      }
      helpText={
        <FormattedMessage
          description="Ogone legacy payment options 'merchantId' help text"
          defaultMessage="Which merchant should be used for payments related to this form."
        />
      }
      required
    >
      <ReactSelect name="merchantId" options={options} required />
    </Field>
  </FormRow>
);

MerchantID.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.number,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};

export const TitleTemplate = () => {
  const [fieldProps] = useField('titleTemplate');
  return (
    <FormRow>
      <Field
        name="titleTemplate"
        label={
          <FormattedMessage
            description="Ogone legacy payment options 'titleTemplate' label"
            defaultMessage="TITLE parameter"
          />
        }
        helpText={
          <FormattedMessage
            description="Ogone legacy payment options 'titleTemplate' help text"
            defaultMessage={`Optional custom template for the title displayed on the payment page.<br></br>
            You can use all form variables (using their keys) and the <code>public_reference</code>
            template variable. If unspecified, a default description is used.`}
            values={{
              br: () => <br />,
              code: chunks => <code>{chunks}</code>,
            }}
          />
        }
      >
        <TextInput {...fieldProps} />
      </Field>
    </FormRow>
  );
};

TitleTemplate.propTypes = {};

export const ComTemplate = () => {
  const [fieldProps] = useField('comTemplate');
  return (
    <FormRow>
      <Field
        name="comTemplate"
        label={
          <FormattedMessage
            description="Ogone legacy payment options 'comTemplate' label"
            defaultMessage="COM parameter"
          />
        }
        helpText={
          <FormattedMessage
            description="Ogone legacy payment options 'comTemplate' help text"
            defaultMessage={`Optional custom template for the the description, included in the
            payment overviews for the backoffice. Use this to link the payment back to a particular
            process or form.<br></br>
            You can use all form variables (using their keys) and the <code>public_reference</code>
            template variable. If unspecified, a default description is used.<br></br>
            <strong>Note</strong>: the length of the result is capped to 100 characters.`}
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

ComTemplate.propTypes = {};
