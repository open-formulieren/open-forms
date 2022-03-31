import React from 'react';
import PropTypes from 'prop-types';
import {useIntl} from 'react-intl';

import Select from '../../forms/Select';
import DeleteIcon from '../../DeleteIcon';

import {ACTION_TYPES} from './constants';
import DataPreview from './DataPreview';
import {ActionComponent} from './actions/Actions';
import {Action as ActionType} from './actions/types';


const Action = ({prefixText, action, onChange, onDelete}) => {
    const intl = useIntl();

    return (
        <div className="logic-action">

            <div className="logic-action__actions">
                <DeleteIcon
                    onConfirm={onDelete}
                    message={intl.formatMessage({
                        description: 'Logic rule action deletion confirm message',
                        defaultMessage: 'Are you sure you want to delete this action?',
                    })}
                />
            </div>

            <div className="logic-action__action">
                <div className="dsl-editor">
                    <div className="dsl-editor__node">{prefixText}</div>

                    <div className="dsl-editor__node">
                        <Select
                            name="action.type"
                            choices={ACTION_TYPES}
                            translateChoices
                            allowBlank
                            onChange={onChange}
                            value={action.action.type}
                        />
                    </div>

                    <ActionComponent action={action} errors={[]} onChange={onChange}/>
                </div>
            </div>

            <div className="logic-action__data-preview">
                <DataPreview data={action} />
            </div>

        </div>
    );
};


Action.propTypes = {
    prefixText: PropTypes.node.isRequired,
    action: ActionType.isRequired,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};


export default Action;
