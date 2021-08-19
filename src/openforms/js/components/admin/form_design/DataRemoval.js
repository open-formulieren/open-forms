import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

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
                    label={
                        <FormattedMessage
                                description="form.successfulSubmissionsRemovalLimit form label"
                                defaultMessage="Successful Submissions Removal Limit"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="form.successfulSubmissionsRemovalLimit help text"
                            defaultMessage="Amount of days successful submissions of this form will remain before being removed. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <TextInput
                        value={successfulSubmissionsRemovalLimit || ''}
                        onChange={onChange}
                        type="number"
                        min="1"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.successfulSubmissionsRemovalMethod"
                    label={
                        <FormattedMessage
                            defaultMessage="Successful Submissions Removal Method"
                            description="Successful Submissions Removal Method"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="form.successfulSubmissionsRemovalMethod help text"
                            defaultMessage="How successful submissions of this form will be removed after the limit. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <Select
                        name='form.successfulSubmissionsRemovalMethod'
                        choices={removalMethods}
                        value={successfulSubmissionsRemovalMethod || ''}
                        onChange={onChange}
                        allowBlank={true}
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.incompleteSubmissionsRemovalLimit"
                    label={
                        <FormattedMessage
                                description="form.incompleteSubmissionsRemovalLimit form label"
                                defaultMessage="Incomplete Submissions Removal Limit"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="form.incompleteSubmissionsRemovalLimit help text"
                            defaultMessage="Amount of days incomplete submissions of this form will remain before being removed. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <TextInput
                        value={incompleteSubmissionsRemovalLimit || ''}
                        onChange={onChange}
                        type="number"
                        min="1"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.incompleteSubmissionsRemovalMethod"
                    label={
                        <FormattedMessage
                            defaultMessage="Incomplete Submissions Removal Method"
                            description="Incomplete Submissions Removal Method"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="form.incompleteSubmissionsRemovalMethod help text"
                            defaultMessage="How incomplete submissions of this form will be removed after the limit. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <Select
                        name='form.incompleteSubmissionsRemovalMethod'
                        choices={removalMethods}
                        value={incompleteSubmissionsRemovalMethod || ''}
                        onChange={onChange}
                        allowBlank={true}
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.erroredSubmissionsRemovalLimit"
                    label={
                        <FormattedMessage
                                description="form.erroredSubmissionsRemovalLimit form label"
                                defaultMessage="Errored Submissions Removal Limit"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="form.erroredSubmissionsRemovalLimit help text"
                            defaultMessage="Amount of days errored submissions of this form will remain before being removed. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <TextInput
                        value={erroredSubmissionsRemovalLimit || ''}
                        onChange={onChange}
                        type="number"
                        min="1"/>
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.erroredSubmissionsRemovalMethod"
                    label={
                        <FormattedMessage
                            defaultMessage="Errored Submissions Removal Method"
                            description="Errored Submissions Removal Method"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="form.erroredSubmissionsRemovalMethod help text"
                            defaultMessage="How errored submissions of this form will be removed after the limit. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <Select
                        name='form.erroredSubmissionsRemovalMethod'
                        choices={removalMethods}
                        value={erroredSubmissionsRemovalMethod || ''}
                        onChange={onChange}
                        allowBlank={true}
                    />
                </Field>
            </FormRow>
            <FormRow>
                <Field
                    name="form.allSubmissionsRemovalLimit"
                    label={
                        <FormattedMessage
                                description="form.allSubmissionsRemovalLimit form label"
                                defaultMessage="All Submissions Removal Limit"
                        />
                    }
                    helpText={
                        <FormattedMessage
                            description="form.allSubmissionsRemovalLimit help text"
                            defaultMessage="Amount of days when all submissions of this form will be permanently deleted. Leave blank to use value in General Configuration."
                        />
                    }
                >
                    <TextInput
                        value={allSubmissionsRemovalLimit || ''}
                        onChange={onChange}
                        type="number"
                        min="1"/>
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
    removalMethods: PropTypes.arrayOf(PropTypes.array),
    onChange: PropTypes.func.isRequired,
};


export default DataRemoval;
