import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import {TextInput} from '../forms/Inputs';
import Select from '../forms/Select';


const DataRemoval = ({ submissionsRemovalOptions, removalMethods, onChange }) => {

    const { successfulSubmissionsRemovalLimit='', successfulSubmissionsRemovalMethod='',
            incompleteSubmissionsRemovalLimit='', incompleteSubmissionsRemovalMethod='',
            erroredSubmissionsRemovalLimit='', erroredSubmissionsRemovalMethod='',
            allSubmissionsRemovalLimit='' } = submissionsRemovalOptions;

    return (
        <Fieldset>
            <FormRow>
                <Field
                    name="submissionsRemovalOptions.successfulSubmissionsRemovalLimit"
                    label={
                        <FormattedMessage
                                description="Successful Submissions Removal Limit field label"
                                defaultMessage="Successful Submissions Removal Limit"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="Successful Submissions Removal Limit help text"
                            defaultMessage="Amount of days successful submissions of this form will remain before being removed. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <TextInput
                        value={successfulSubmissionsRemovalLimit}
                        onChange={onChange}
                        type="number"
                        min="1"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="submissionsRemovalOptions.successfulSubmissionsRemovalMethod"
                    label={
                        <FormattedMessage
                            defaultMessage="Successful Submissions Removal Method field label"
                            description="Successful Submissions Removal Method"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="Successful Submissions Removal Method help text"
                            defaultMessage="How successful submissions of this form will be removed after the limit. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <Select
                        name="submissionsRemovalOptions.successfulSubmissionsRemovalMethod"
                        choices={removalMethods}
                        value={successfulSubmissionsRemovalMethod}
                        onChange={onChange}
                        allowBlank
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="submissionsRemovalOptions.incompleteSubmissionsRemovalLimit"
                    label={
                        <FormattedMessage
                                description="Incomplete Submissions Removal Limit field label"
                                defaultMessage="Incomplete Submissions Removal Limit"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="Incomplete Submissions Removal Limit help text"
                            defaultMessage="Amount of days incomplete submissions of this form will remain before being removed. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <TextInput
                        value={incompleteSubmissionsRemovalLimit}
                        onChange={onChange}
                        type="number"
                        min="1"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="submissionsRemovalOptions.incompleteSubmissionsRemovalMethod"
                    label={
                        <FormattedMessage
                            defaultMessage="Incomplete Submissions Removal Method"
                            description="Incomplete Submissions Removal Method field label"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="Incomplete Submissions Removal Method help text"
                            defaultMessage="How incomplete submissions of this form will be removed after the limit. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <Select
                        name="submissionsRemovalOptions.incompleteSubmissionsRemovalMethod"
                        choices={removalMethods}
                        value={incompleteSubmissionsRemovalMethod}
                        onChange={onChange}
                        allowBlank
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="submissionsRemovalOptions.erroredSubmissionsRemovalLimit"
                    label={
                        <FormattedMessage
                                description="Errored Submissions Removal Limit field label"
                                defaultMessage="Errored Submissions Removal Limit"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="Errored Submissions Removal Limit help text"
                            defaultMessage="Amount of days errored submissions of this form will remain before being removed. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <TextInput
                        value={erroredSubmissionsRemovalLimit}
                        onChange={onChange}
                        type="number"
                        min="1"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="submissionsRemovalOptions.erroredSubmissionsRemovalMethod"
                    label={
                        <FormattedMessage
                            defaultMessage="Errored Submissions Removal Method"
                            description="Errored Submissions Removal Method field label"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="Errored Submissions Removal Method help text"
                            defaultMessage="How errored submissions of this form will be removed after the limit. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <Select
                        name="submissionsRemovalOptions.erroredSubmissionsRemovalMethod"
                        choices={removalMethods}
                        value={erroredSubmissionsRemovalMethod}
                        onChange={onChange}
                        allowBlank
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="submissionsRemovalOptions.allSubmissionsRemovalLimit"
                    label={
                        <FormattedMessage
                                description="All Submissions Removal Limit field label"
                                defaultMessage="All Submissions Removal Limit"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="All Submissions Removal Limit help text"
                            defaultMessage="Amount of days when all submissions of this form will be permanently deleted. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <TextInput
                        value={allSubmissionsRemovalLimit}
                        onChange={onChange}
                        type="number"
                        min="1"/>
                </Field>
            </FormRow>
        </Fieldset>
    );
};

DataRemoval.propTypes = {
    submissionsRemovalOptions: PropTypes.shape(PropTypes.shape({
        successfulSubmissionsRemovalLimit: PropTypes.number,
        successfulSubmissionsRemovalMethod: PropTypes.string,
        incompleteSubmissionsRemovalLimit: PropTypes.number,
        incompleteSubmissionsRemovalMethod: PropTypes.string,
        erroredSubmissionsRemovalLimit: PropTypes.number,
        erroredSubmissionsRemovalMethod: PropTypes.string,
        allSubmissionsRemovalLimit: PropTypes.number,
    })),
    removalMethods: PropTypes.arrayOf(PropTypes.array).isRequired,
    onChange: PropTypes.func.isRequired,
};


export default DataRemoval;
