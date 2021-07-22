import React, {useState} from 'react';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';

import {post, get} from '../../../utils/fetch';
import {FORM_ENDPOINT} from '../form_design/constants';


const FormVersionsTable = ({ csrftoken, formUuid, formAdminUrl}) => {
    const [formVersions, setFormVersions] = useState([]);

    const restoreVersion = async (csrftoken, formUuid, versionUuid, redirectUrl) => {
        await post(
            `${FORM_ENDPOINT}/${formUuid}/restore_version`,
            csrftoken,
            {uuid: versionUuid}
        );
        window.location = redirectUrl;
    };

    const getFormVersions = async (uuid) => {
        const response = await get(
            `${FORM_ENDPOINT}/${uuid}/retrieve_versions`
        );
        setFormVersions(response.data);
    };

    useAsync(async () => {await getFormVersions(formUuid);}, []);

    const rows = formVersions.map((version, index) => {
        const dateCreation = new Date(version.dateCreation);
        return (
           <tr key={index}>
                <th>{ dateCreation.toDateString() } { dateCreation.toLocaleTimeString() }</th>
                <td><a href="#" onClick={() => restoreVersion(csrftoken, formUuid, version.uuid, formAdminUrl)}>Restore</a></td>
            </tr>
        );
    });

    return (
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
        </table>
    );

};

export default FormVersionsTable;
