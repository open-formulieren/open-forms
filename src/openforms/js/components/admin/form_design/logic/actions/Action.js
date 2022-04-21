import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import {useIntl} from 'react-intl';

import Select from '../../../forms/Select';
import DeleteIcon from '../../../DeleteIcon';
import {ACTION_TYPES} from '../constants';
import DataPreview from '../DataPreview';
import {ActionComponent} from './Actions';
import {Action as ActionType, ActionError} from './types';
import DSLEditorNode from '../DSLEditorNode';


const Action = ({prefixText, action, errors={}, onChange, onDelete}) => {
    const intl = useIntl();
    const hasErrors = Object.entries(errors).length > 0;

    return (
        <div className="logic-action">

            <div className={`logic-action__row ${classNames({'logic-action__row--has-errors': hasErrors})}`}>

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
                        <DSLEditorNode errors={null}>{prefixText}</DSLEditorNode>

                        <DSLEditorNode errors={errors.action?.type}>
                            <Select
                                name="action.type"
                                choices={ACTION_TYPES}
                                translateChoices
                                allowBlank
                                onChange={onChange}
                                value={action.action.type}
                            />
                        </DSLEditorNode>

                        <ActionComponent action={action} errors={errors} onChange={onChange}/>
                    </div>
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
    errors: ActionError,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};


export default Action;
