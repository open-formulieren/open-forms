import React from 'react';
import PropTypes from 'prop-types';
import useKeyboardShortcut from 'use-keyboard-shortcut'

import {SubmitAction, AddAnotherAction, ContinueEditingAction} from './ActionButton';


const SubmitRow = ({ onSubmit, preventDefault=true, isDefault=false, extraClassName='', children }) => {
    let className = 'submit-row';
    if (extraClassName) {
        className += ` ${extraClassName}`;
    }

    const onSubmitClick = (event) => {
        if (preventDefault) event.preventDefault();
        if (onSubmit) onSubmit(event);
    };

    if (onSubmit) {
        const saveKeyHandler = shortcutKeys => {
            onSubmit({target: {name: "_continue"}});
        };
        const saveKeyOptions = {
            overrideSystem: true,
            ignoreInputFields: false,
            repeatOnHold: false
        };
        const {flushControlHeldKeys} = useKeyboardShortcut(
            ["Control", "S"],
            saveKeyHandler,
            saveKeyOptions
        );
        const {flushMetaHeldKeys} = useKeyboardShortcut(
            ["Meta", "S"],
            saveKeyHandler,
            saveKeyOptions
        );
    }

    return (
        <div className={className}>
            { children ?? (
                <>
                    <SubmitAction
                        className={isDefault ? 'default' : ''}
                        onClick={onSubmitClick}
                    />
                    <AddAnotherAction onClick={onSubmitClick} />
                    <ContinueEditingAction onClick={onSubmitClick} />
                </>
            )}
        </div>
    );
};

SubmitRow.propTypes = {
    onSubmit: PropTypes.func,
    preventDefault: PropTypes.bool,
    isDefault: PropTypes.bool,
    extraClassName: PropTypes.string,
    children: PropTypes.node,
};


export default SubmitRow;
