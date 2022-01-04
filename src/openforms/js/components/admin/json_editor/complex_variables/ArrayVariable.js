import React, {useState, useEffect} from 'react';
import PropTypes from 'prop-types';
import {produce} from 'immer';
import {FormattedMessage} from 'react-intl';

import ButtonContainer from '../../forms/ButtonContainer';
import {ChangelistTableWrapper, HeadColumn, TableRow} from '../../tables';
import TypeRepresentation from '../TypeRepresentation';
import Types from '../types';
import ValueRepresentation from '../ValueRepresentation';



const ArrayItem = ({index, definition=null, onEditDefinition}) => (
    <TableRow index={index}>
        <span>{index}.</span>
        <TypeRepresentation definition={definition} />
        <ValueRepresentation definition={definition} />
        <a href="#" onClick={onEditDefinition}>
            <FormattedMessage
                description="JSON editor: edit value definition"
                defaultMessage="Edit definition"
            />
        </a>
    </TableRow>
);

ArrayItem.propTypes = {
    index: PropTypes.number.isRequired,
    definition: Types.VariableDefinition,
    onEditDefinition: PropTypes.func.isRequired,
};


const ArrayVariable = ({ definition=[], onChange, onEditDefinition }) => {

    const items = definition ?? [];

    const onEditClick = (index, event) => {
        event.preventDefault();
        onEditDefinition({
            name: index,
            definition: definition[index],
        });
    }

    const onAddItem = (event) => {
        event.preventDefault();
        const newDefinition = produce(items, draft => {
            draft.push(null); // add new, empty definition to the end
        });
        onChange(newDefinition);
    };

    const headColumns = (
        <>
            <HeadColumn content="#" />
            <HeadColumn content={<FormattedMessage
                description="JSON editor: 'type' header label"
                defaultMessage="Type"
            />} />
            <HeadColumn content={<FormattedMessage
                description="JSON editor: 'value' header label"
                defaultMessage="Value"
            />} />
            <HeadColumn content={<FormattedMessage
                description="JSON editor: 'configure' header label"
                defaultMessage="Configure"
            />} />
        </>
    );
    return (
        <div style={{paddingTop: '10px'}}>
            <ChangelistTableWrapper headColumns={headColumns}>
                {
                    items.map((item, index) => (
                        <ArrayItem
                            key={index}
                            index={index}
                            definition={item}
                            onEditDefinition={onEditClick.bind(null, index)}
                        />
                    ))
                }
            </ChangelistTableWrapper>

            <ButtonContainer onClick={onAddItem}>
                <FormattedMessage
                    description="JSON editor: add array value button"
                    defaultMessage="Add item"
                />
            </ButtonContainer>
        </div>
    );
};

ArrayVariable.propTypes = {
    definition: PropTypes.arrayOf(Types.VariableDefinition),
    onChange: PropTypes.func.isRequired,
    onEditDefinition: PropTypes.func.isRequired,
};

export default ArrayVariable;
