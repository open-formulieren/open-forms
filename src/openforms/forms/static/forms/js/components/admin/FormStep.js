import React, { useContext } from 'react';
import PropTypes from 'prop-types';
import usePrevious from 'react-use/esm/usePrevious';

import Select from "../formsets/Select";
import { getFormDefinitionChoices } from "../utils/form-definition-choices";
import { FormDefinitionsContext } from './Context';
import FormStepDefinition from './FormStepDefinition';
import FAIcon from './FAIcon';

const FormStepHeader = ({title, currentFormDefinition='', onDelete, onReplace}) => {




    const formDefinitions = useContext(FormDefinitionsContext);
    const formDefinitionChoices = getFormDefinitionChoices(formDefinitions);
    return (
        <>
            <FAIcon icon="trash" extraClassname="danger" title="Delete" onClick={onDelete} />
            <Select
                name="Form definition"
                choices={formDefinitionChoices}
                value={currentFormDefinition}
                onChange={onReplace}
                className={"step-select"}
            />
        </>
    )
};

FormStepHeader.propTypes = {
    title: PropTypes.string.isRequired,
    currentFormDefinition: PropTypes.string,
    onDelete: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
};


const NewStepFormDefinitionPicker = ({  }) => {
    return (
        <div className="tiles tiles--horizontal">
            <button type="button" className="tiles__tile">
                <FAIcon icon="recycle" extraClassname="fa-2x" title="Selecteer definitie" />
                <span>Gebruik bestaande formulierdefinitie</span>
            </button>

            <span className="tiles__separator">&bull;</span>

            <button type="button" className="tiles__tile">
                <FAIcon icon="pencil-square-o" extraClassname="fa-2x" title="Maak definitie" />
                <span>Maak een nieuwe formulierdefinitie</span>
            </button>

        </div>
    );
};



const FormStep = ({ title, data, onEdit, onFieldChange, onReplace, errors={} }) => {
    const { configuration, formDefinition, name, slug, isNew } = data;

    const previousFormDefinition = usePrevious(formDefinition);
    let forceBuilderUpdate = false;
    if (previousFormDefinition && previousFormDefinition != formDefinition) {
        forceBuilderUpdate = true;
    }

    if (isNew) {
        return (
            <NewStepFormDefinitionPicker />
        );
    }

    return (
        <>
            { Object.keys(errors).length ? <div className='fetch-error'>The form step below is invalid.</div> : null }
            <FormStepDefinition
                name={name}
                slug={slug}
                url={formDefinition}
                configuration={configuration}
                onFieldChange={onFieldChange}
                onChange={onEdit}
                forceUpdate={forceBuilderUpdate}
                errors={errors}
            />
        </>
    );
};


FormStep.propTypes = {
    title: PropTypes.string.isRequired,
    data: PropTypes.shape({
        configuration: PropTypes.object,
        formDefinition: PropTypes.string,
        index: PropTypes.number,
        name: PropTypes.string,
        slug: PropTypes.string,
        url: PropTypes.string,
        isNew: PropTypes.bool,
    }).isRequired,
    onEdit: PropTypes.func.isRequired,
    onFieldChange: PropTypes.func.isRequired,
    onReplace: PropTypes.func.isRequired,
    errors: PropTypes.object,
};


export default FormStep;
