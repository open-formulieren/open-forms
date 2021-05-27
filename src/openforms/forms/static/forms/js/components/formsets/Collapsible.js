import React, {useState} from 'react';

const Collapsible = ({title, content}) => {
    const [isOpen, setIsOpen] = useState(false);

    const toggle = () => {
        setIsOpen(!isOpen);
    };

    return (
        <>
            <button type="button" className="collapsible" onClick={toggle}>{title}</button>
            {isOpen ?
                content : null
            }
        </>
    );
};

export {Collapsible};
