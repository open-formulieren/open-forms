import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import {getFormComponents} from 'components/admin/form_design/utils';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import {COSIGN_V1_TYPE} from 'components/form/coSignOld';

import TYPES from './types';
import {VARIABLE_SOURCES} from './variables/constants';

/**
 * Component to render the metadata admin form for an Open Forms form.
 */
const FormAdvancedConfiguration = ({form, formSteps, onChange}) => {
  const {formVariables} = useContext(FormContext);
  const userDefinedVariables = formVariables.filter(
    variable => variable.source === VARIABLE_SOURCES.userDefined
  );

  const {brpPersonenRequestOptions} = form;

  const components = Object.values(getFormComponents(formSteps));

  // TODO This plugin id will be renamed at some point.
  const hasBRPPrefill = components.some(comp => comp.prefill?.plugin === 'haalcentraal');

  // These two could not be relevant if using Stuf-BG, but this information is not available in the frontend.
  const hasNpFamilyMembers = components.some(comp => comp.type === 'npFamilyMembers');
  const hasCosign = components.some(comp => comp.type === COSIGN_V1_TYPE);

  // The new Family members prefill plugin
  const hasFamilyMembersPrefill = userDefinedVariables.some(
    variable => variable.prefillPlugin === 'family_members'
  );

  return (
    <>
      {hasBRPPrefill || hasNpFamilyMembers || hasCosign || hasFamilyMembersPrefill ? (
        <Fieldset
          title={
            <FormattedMessage
              defaultMessage="Processing"
              description="Form processing fieldset title"
            />
          }
        >
          <FormRow>
            <Field
              name="form.brpPersonenRequestOptions.brpPersonenPurposeLimitationHeaderValue"
              label={
                <FormattedMessage
                  defaultMessage="BRP Personen purpose limitation header value"
                  description="Form 'BRP Personen purpose limitation header value' field label"
                />
              }
              helpText={
                <FormattedMessage
                  defaultMessage='The purpose limitation ("doelbinding") for queries to the BRP Persoon API.'
                  description="Form 'BRP Personen purpose limitation header value' field help text"
                />
              }
            >
              <TextInput
                value={brpPersonenRequestOptions?.brpPersonenPurposeLimitationHeaderValue || ''}
                onChange={onChange}
                maxLength="255"
              />
            </Field>
          </FormRow>
          <FormRow>
            <Field
              name="form.brpPersonenRequestOptions.brpPersonenProcessingHeaderValue"
              label={
                <FormattedMessage
                  defaultMessage="BRP Personen processing header value"
                  description="Form 'BRP Personen processing header value' field label"
                />
              }
              helpText={
                <FormattedMessage
                  defaultMessage='The processing ("verwerking") for queries to the BRP Persoon API.'
                  description="Form 'BRP Personen processing header value' field help text"
                />
              }
            >
              <TextInput
                value={brpPersonenRequestOptions?.brpPersonenProcessingHeaderValue || ''}
                onChange={onChange}
                maxLength="242"
              />
            </Field>
          </FormRow>
        </Fieldset>
      ) : (
        <p style={{padding: '1em 0 0', color: 'var(--body-quiet-color)'}}>
          <FormattedMessage
            defaultMessage="No advanced configuration is available for this form."
            description="Form advanced configuration fallback message"
          />
        </p>
      )}
    </>
  );
};

FormAdvancedConfiguration.propTypes = {
  form: PropTypes.shape({
    brpPersonenRequestOptions: PropTypes.shape({
      brpPersonenPurposeLimitationHeaderValue: PropTypes.string,
      brpPersonenProcessingHeaderValue: PropTypes.string,
    }),
  }).isRequired,
  formSteps: PropTypes.arrayOf(TYPES.FormStep).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default FormAdvancedConfiguration;
