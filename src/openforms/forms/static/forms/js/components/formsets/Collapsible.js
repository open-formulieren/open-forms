import React, {useState} from 'react';

const Collapsible = ({header, content}) => {
    const [isOpen, setIsOpen] = useState(false);

    const toggleOpen = (event) => {
        event.preventDefault();
        setIsOpen(!isOpen);
    };

    return (
        <>
            <div className="collapsible-header">
                <div className='collapsible-header-title'>{header}</div>
                <a href='#' onClick={toggleOpen}>{isOpen ? 'Collapse' : 'Expand'}</a>
            </div>
            {isOpen ?
                content : null
            }
        </>
    );
};

export {Collapsible};
