import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, useIntl} from 'react-intl';

import {getTranslatedChoices} from '../../../../utils/i18n';
import Select from '../../forms/Select';
import Types from '../types';


const VARIABLE_SOURCES = {
    component: defineMessage({
        description: 'JSON editor: "component" variable source label',
        defaultMessage: 'From form field',
    }),
    manual: defineMessage({
        description: 'JSON editor: "manual" variable source label',
        defaultMessage: 'Manually defined',
    }),
};



const VariableSourceSelector = ({ varSource='', ...props }) => {
    const intl = useIntl();
    return (
        <Select choices={getTranslatedChoices(intl, VARIABLE_SOURCES)} value={varSource} {...props} />
    );
};

VariableSourceSelector.propTypes = {
    varSource: Types.VariableSource,
};


export default VariableSourceSelector;
