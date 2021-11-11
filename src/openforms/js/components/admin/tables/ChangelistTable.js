import React from 'react';
import PropTypes from 'prop-types';

import ChangelistColumn from './ChangelistColumn';
import {IconYes, IconNo, IconUnknown} from '../BooleanIcons';


const ChangelistTable = ({ linkColumn=0, linkProp="", data=[], rowKey="", children }) => {
    const renderLink = linkColumn != null && Boolean(linkProp);
    const tableColumns = [];

    // process the configuration of the columns
    React.Children.map(children, (child) => {
        if (child.type.name !== 'ChangelistColumn') {
            throw new Error(`ChangelistTable only takes ChangelistColumn children, but got ${child.type.name} instead.`);
        }
        tableColumns.push({
            header: React.cloneElement(child.props.children),
            objProp: child.props.objProp,
            isBool: child.props.isBool ?? false,
        });
    });

    return (
        <div className="changelist changelist--react">
            <div className="results">
                <table>
                    <thead>
                        <tr>
                            {
                                tableColumns.map((col, colIndex) => (
                                    <th scope="col" key={colIndex}>
                                        <div className="text">
                                            <span>{col.header}</span>
                                        </div>
                                    </th>
                                ))
                            }
                        </tr>
                    </thead>

                    <tbody>
                        {
                            data.map((obj, index) => (
                                <tr key={rowKey ? obj[rowKey] : index} className={`row${(index % 2) + 1}`}>
                                    {
                                        tableColumns.map((col, colIndex) => (
                                            <RowColumn
                                                key={colIndex}
                                                obj={obj}
                                                index={colIndex}
                                                objProp={col.objProp}
                                                linkColumn={linkColumn}
                                                linkProp={linkProp}
                                                isBool={col.isBool}
                                            />
                                        ))
                                    }
                                </tr>
                            ))
                        }
                    </tbody>
                </table>
            </div>
        </div>
    );
};

ChangelistTable.propTypes = {
    linkColumn: PropTypes.number,
    linkProp: PropTypes.string,
    data: PropTypes.arrayOf(PropTypes.object),
    rowKey: PropTypes.string,
    children: PropTypes.node,
};


const RowColumn = ({ obj, index, objProp, linkColumn=0, linkProp="", isBool=false }) => {
    const renderLink = (linkColumn != null && Boolean(linkProp)) && linkColumn === index;
    const Component = (index === linkColumn) ? 'th' : 'td';
    const value = obj[objProp];
    let content;

    if (isBool) {
        content = (value == null)
            ? <IconUnknown />
            : value
                ? <IconYes />
                : <IconNo />
    } else {
        content = value;
    }

    if (renderLink) {
        content = (
            <a href={obj[linkProp]} target="_blank" rel="noopener nofollower noreferrer">
                {content}
            </a>
        );
    }

    return (
        <Component className={(index === linkColumn) ? 'nowrap' : ''}>
            {content}
        </Component>
    );
};

RowColumn.propTypes = {
    obj: PropTypes.object.isRequired,
    index: PropTypes.number.isRequired,
    objProp: PropTypes.string.isRequired,
    linkColumn: PropTypes.number,
    linkProp: PropTypes.string,
    isBool: PropTypes.bool,
};

export default ChangelistTable;
