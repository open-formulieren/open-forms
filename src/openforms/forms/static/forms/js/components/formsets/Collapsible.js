import React, {useState} from 'react';

const Collapsible = ({title, content}) => {
    const [isOpen, setIsOpen] = useState(false);

    const toggleOpen = () => {
        setIsOpen(!isOpen);
    };

    return (
        <>
            <a href='#' onClick={toggleOpen}>{title}</a>
            {isOpen ?
                content : null
            }
        </>
    );
};

export {Collapsible};
