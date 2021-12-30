import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import ComponentSelection from '../../forms/ComponentSelection';
import Field from '../../forms/Field';
import Fieldset from '../../forms/Fieldset';
import FormRow from '../../forms/FormRow';
import Types from '../types';

import ComplexManualVariable from './ComplexManualVariable';
import PrimitiveManualVariable from './PrimitiveManualVariable';
import VariableSourceSelector from './VariableSourceSelector';


const ComponentSelectionRow = ({ component='', onChange }) => {
    return (
        <FormRow>
            <Field name="component" label={<FormattedMessage
                description="Formio component selection label"
                defaultMessage="Component"
            />}>
                <ComponentSelection name="component" value={component} onChange={onChange} />
            </Field>
        </FormRow>
    );
};

ComponentSelectionRow.propTypes = {
    component: PropTypes.string,
    onChange: PropTypes.func.isRequired,
};


const DependentFields = ({ source, component, manual, onChange }) => {
    let fields = null;

    switch (source) {
        case 'component': {
            fields = (<ComponentSelectionRow component={component} onChange={onChange} />);
            break;
        }
        case 'manual': {
            fields = (
                <PrimitiveManualVariable {...manual} onChange={onChange} />
            );
            break;
        }
    }
    return fields;
};

DependentFields.propTypes = {
    source: Types.VariableSource.isRequired,
    component: PropTypes.string,
    manual: PropTypes.shape({
        type: Types.VariableType,
        definition: Types.LeafVariableDefinition,
    }),
    onChange: PropTypes.func.isRequired,
};


const EditVariable = ({
    name, source, component='', manual, parent=null,
    onFieldChange, onManualChange, dependentFieldsOnChange, onEditDefinition,
}) => {
    return (
        <>
            <Fieldset>
                <FormRow>
                    <Field name="source" label={<FormattedMessage
                        description="JSON editor: value source selector label"
                        defaultMessage="Source"
                    />}
                    >
                        <VariableSourceSelector value={source} onChange={onFieldChange} />
                    </Field>
                </FormRow>

                <DependentFields
                    source={source}
                    component={component}
                    manual={manual}
                    onChange={dependentFieldsOnChange}
                />

            </Fieldset>

            { source === 'manual'
                ? (
                    <ComplexManualVariable
                        name={name}
                        {...manual}
                        parent={parent}
                        onChange={onManualChange}
                        onEditDefinition={onEditDefinition}
                    />
                )
                : null
            }
        </>
    );
};

EditVariable.propTypes = {
    name: Types.VariableIdentifier.isRequired,
    source: Types.VariableSource.isRequired,
    component: PropTypes.string,
    manual: PropTypes.shape({
        type: Types.VariableType,
        definition: Types.LeafVariableDefinition,
    }),
    parent: Types.VariableParent,
    onFieldChange: PropTypes.func.isRequired,
    onManualChange: PropTypes.func.isRequired,
    dependentFieldsOnChange: PropTypes.func.isRequired,
    onEditDefinition: PropTypes.func.isRequired,
};


export default EditVariable;
