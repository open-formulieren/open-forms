import React, {useState} from 'react';

const Collapsible = ({title, content, onDelete}) => {
    const [isOpen, setIsOpen] = useState(false);

    const toggleOpen = () => {
        setIsOpen(!isOpen);
    };

    return (
        <>
            <div>
                <button type="button" className="collapsible" onClick={toggleOpen}>{title}</button>
                <span className="material-icons" onClick={onDelete} title='delete'>delete</span>
            </div>
            {isOpen ?
                content : null
            }
        </>
    );
};

export {Collapsible};
