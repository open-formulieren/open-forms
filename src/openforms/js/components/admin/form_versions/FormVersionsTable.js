import React, {useState} from 'react';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';

import {get, post} from '../../../utils/fetch';
import {FORM_ENDPOINT} from '../form_design/constants';
import Loader from "../Loader";


const FormVersionsTable = ({ csrftoken, formUuid }) => {
    const [formVersions, setFormVersions] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    const restoreVersion = async (csrftoken, formUuid, versionUuid, redirectUrl) => {
        await post(
            `${FORM_ENDPOINT}/${formUuid}/versions/${versionUuid}/restore`,
            csrftoken
        );
        // finalize the "transaction".
        //
        // * schedule a success message
        // * obtain the admin URL to redirect to the detail page for further editing
        const messageData = {
            isCreate: false,
            submitAction: '_continue',
        };
        const messageResponse = await post(`${FORM_ENDPOINT}/${formUuid}/admin-message`, csrftoken, messageData);
        // this full-page reload ensures that the admin messages are displayed
        window.location = messageResponse.data.redirectUrl;
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
                    restoreVersion(csrftoken, formUuid, version.uuid);
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
}

export default FormVersionsTable;
