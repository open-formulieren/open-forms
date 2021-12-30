import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage} from 'react-intl';

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



const VariableSourceSelector = ({ varSource='', ...props }) => (
    <Select choices={VARIABLE_SOURCES} translateChoices value={varSource} {...props} />
);

VariableSourceSelector.propTypes = {
    varSource: Types.VariableSource,
};


export default VariableSourceSelector;
