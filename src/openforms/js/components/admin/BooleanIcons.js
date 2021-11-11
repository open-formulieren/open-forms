import React from 'react';
import PropTypes from 'prop-types';

import {STATIC_URL} from './constants';


const BooleanIcon = ({ icon, ...props }) => {
    const fullUrl = `${STATIC_URL}admin/img/icon-${icon}.svg`;
    return (<img src={fullUrl} {...props} />);
};

BooleanIcon.propTypes = {
    icon: PropTypes.oneOf(['unknown', 'yes', 'no']).isRequired,
};


const IconYes = () => (<BooleanIcon icon="yes" alt="True" /> );
const IconNo = () => (<BooleanIcon icon="no" alt="False" /> );
const IconUnknown = () => (<BooleanIcon icon="unknown" alt="None" /> );


export default BooleanIcon;
export {IconYes, IconNo, IconUnknown};
