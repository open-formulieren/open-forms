import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import {TextInput} from '../forms/Inputs';
import Select from "../forms/Select";


const DataRemoval = ({ successfulSubmissionsRemovalLimit, successfulSubmissionsRemovalMethod,
                         incompleteSubmissionsRemovalLimit, incompleteSubmissionsRemovalMethod,
                         erroredSubmissionsRemovalLimit, erroredSubmissionsRemovalMethod,
                         allSubmissionsRemovalLimit, removalMethods, onChange }) => {

    return (
        <Fieldset>
            <FormRow>
                <Field
                    name="form.successfulSubmissionsRemovalLimit"
                    label={<FormattedMessage description="literals.beginText form label" defaultMessage="Begin text" />}
                    helpText={
                        <FormattedMessage
                            description="literals.beginText help text"
                            defaultMessage="The text that will be displayed at the start of the form to indicate the user can begin to fill in the form. Leave blank to get value from global configuration." />
                    }
                >
                    <TextInput
                        value={successfulSubmissionsRemovalLimit}
                        onChange={onChange}
                        maxLength="50"
                        type="number"
                        min="1"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.successfulSubmissionsRemovalMethod"
                    label={<FormattedMessage defaultMessage="Successful Submissions Removal Method" description="Successful Submissions Removal Method" />}
                >
                    <Select
                        name='form.successfulSubmissionsRemovalMethod'
                        choices={removalMethods}
                        value={successfulSubmissionsRemovalMethod}
                        onChange={onChange}
                        allowBlank={true}
                    />
                </Field>
            </FormRow>
        </Fieldset>
    );
};

DataRemoval.propTypes = {
    successfulSubmissionsRemovalLimit: PropTypes.number,
    successfulSubmissionsRemovalMethod: PropTypes.string,
    incompleteSubmissionsRemovalLimit: PropTypes.number,
    incompleteSubmissionsRemovalMethod: PropTypes.string,
    erroredSubmissionsRemovalLimit: PropTypes.number,
    erroredSubmissionsRemovalMethod: PropTypes.string,
    allSubmissionsRemovalLimit: PropTypes.number,
    removalMethods: PropTypes.arrayOf(PropTypes.shape({
        id: PropTypes.string.isRequired,
        label: PropTypes.string.isRequired,
    })),
    onChange: PropTypes.func.isRequired,
};


export default DataRemoval;
