import React from 'react';
import PropTypes from 'prop-types';


const ChangedFormDefinitionWarning = ({ changed, affectedForms=[] }) => {
    if (!changed) return null;
    return (
        <ul className="messagelist">
            <li className="warning">
                Je bewerkt een bestaande set van formuliervelden! Deze wijziging heeft
                effect op <a href="#" onClick={console.log}>{affectedForms.length} formulier(en)</a>.
            </li>
        </ul>
    );
};

ChangedFormDefinitionWarning.propTypes = {
    changed: PropTypes.bool,
    affectedForms: PropTypes.arrayOf(PropTypes.shape({
        url: PropTypes.string.isRequired,
        uuid: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        active: PropTypes.bool.isRequired,
    })),
};


export default ChangedFormDefinitionWarning;
