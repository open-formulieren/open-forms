import React from 'react';
import {FormattedMessage} from 'react-intl';
import FormioUtils from 'formiojs/utils';
import PropTypes from 'prop-types';


const CUSTOM_FIELD_TYPES = ['npFamilyMembers'];


const AuthenticationWarning = ({loginRequired, configuration}) => {
    if (loginRequired) return null;

    const components = FormioUtils.flattenComponents(configuration.components || [], true);
    const componentsWithCustomFieldTypes = Object.values(components).filter(
        (component) => (CUSTOM_FIELD_TYPES.includes(component.type))
    );

    if (!componentsWithCustomFieldTypes.length) return null;

    const formattedWarnings = componentsWithCustomFieldTypes.map((component, index) => (
        <FormattedMessage
            key={index}
            description="No login required for formstep"
            defaultMessage="Component {label} requires login, but this form step doesn't have the login marked as required."
            values={{label: component.label}}
        />
    ));

    return (
        <ul className="messagelist">
            {
                formattedWarnings.map((warning, index) => {
                    return (
                        <li key={index} className="warning">{warning}</li>
                    );
                })
            }
        </ul>
    );

};


AuthenticationWarning.propTypes = {
    loginRequired: PropTypes.bool.isRequired,
    configuration: PropTypes.object.isRequired,
};


export default AuthenticationWarning;
