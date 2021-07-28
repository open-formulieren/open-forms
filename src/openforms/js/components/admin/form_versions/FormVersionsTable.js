import React, {useState} from 'react';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';

import {get, apiCall} from '../../../utils/fetch';
import {FORM_ENDPOINT} from '../form_design/constants';
import Loader from "../Loader";


const FormVersionsTable = ({ csrftoken, formUuid, formAdminUrl}) => {
    const [formVersions, setFormVersions] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    const restoreVersion = async (csrftoken, formUuid, versionUuid, redirectUrl) => {
        await apiCall(
            `${FORM_ENDPOINT}/${formUuid}/versions/${versionUuid}/restore`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
            }
        );
        window.location = redirectUrl;
    };

    const getFormVersions = async (uuid) => {
        const response = await get(
            `${FORM_ENDPOINT}/${uuid}/versions`
        );
        setFormVersions(response.data);
        setIsLoading(false);
    };

    useAsync(async () => {await getFormVersions(formUuid);}, []);

    const rows = formVersions.map((version, index) => {
        const created = new Date(version.created);
        return (
           <tr key={index}>
                <th>{ created.toDateString() } { created.toLocaleTimeString() }</th>
                <td><a href="#" onClick={(event) => {
                    event.preventDefault();
                    restoreVersion(csrftoken, formUuid, version.uuid, formAdminUrl);
                }}>Herstellen</a></td>
            </tr>
        );
    });

    if (isLoading) {
        return (<Loader />);
    } else {
        return (
            <>
                {rows.length > 0 ?
                    <table id="change-history">
                        <thead>
                        <tr>
                            <th scope="col">Datum/Tijd</th>
                            <th scope="col">Actie</th>
                        </tr>
                        </thead>
                        <tbody>
                        {rows}
                        </tbody>
                    </table> : <p>Dit formulier heeft geen versies.</p>
                }
            </>
        );
    }

};

FormVersionsTable.propTypes = {
    csrftoken: PropTypes.string.isRequired,
    formUuid: PropTypes.string.isRequired,
    formAdminUrl: PropTypes.string.isRequired,
}

export default FormVersionsTable;
