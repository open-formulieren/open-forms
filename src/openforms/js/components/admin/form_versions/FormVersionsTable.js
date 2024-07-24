import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedDate, FormattedMessage, FormattedTime, useIntl} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';
import semverDiff from 'semver/functions/diff';
import semverValid from 'semver/functions/valid';

import Loader from 'components/admin/Loader';
import User from 'components/admin/User';
import {APIContext} from 'components/admin/form_design/Context';
import {FORM_ENDPOINT} from 'components/admin/form_design/constants';
import {WarningIcon} from 'components/admin/icons';
import {get, post} from 'utils/fetch';

const checkVersionsCompatible = (version1, version2) => {
  // if any of the versions is empty, we can't reach any conclusions
  if (!version1 || !version2) return true;
  // if we get non-semver versions -> check for strict equality
  if (!semverValid(version1) || !semverValid(version2)) return version1 === version2;
  const diffLevel = semverDiff(version1, version2);
  // patch releases are backwards compatible
  return diffLevel === 'patch';
};

const FormVersionsTable = ({formUuid, currentRelease}) => {
  const {csrftoken} = useContext(APIContext);
  const intl = useIntl();
  const [formVersions, setFormVersions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const restoreVersion = async (csrftoken, formUuid, versionUuid, redirectUrl) => {
    await post(`${FORM_ENDPOINT}/${formUuid}/versions/${versionUuid}/restore`, csrftoken);
    // finalize the "transaction".
    //
    // * schedule a success message
    // * obtain the admin URL to redirect to the detail page for further editing
    const messageData = {
      isCreate: false,
      submitAction: '_continue',
    };
    const messageResponse = await post(
      `${FORM_ENDPOINT}/${formUuid}/admin-message`,
      csrftoken,
      messageData
    );
    // this full-page reload ensures that the admin messages are displayed
    window.location = messageResponse.data.redirectUrl;
  };

  const getFormVersions = async uuid => {
    const response = await get(`${FORM_ENDPOINT}/${uuid}/versions`);
    setFormVersions(response.data);
    setIsLoading(false);
  };

  useAsync(async () => await getFormVersions(formUuid), []);

  const rows = formVersions.map((version, index) => {
    const created = new Date(version.created);
    const showVersionWarning = !checkVersionsCompatible(version.appRelease, currentRelease);
    return (
      <tr key={version.uuid}>
        <th>
          <FormattedDate value={created} year="numeric" month="long" day="2-digit" />
          &nbsp;&nbsp;
          <FormattedTime value={created} />
        </th>
        <td>{version.user ? <User {...version.user} /> : '-'}</td>
        <td>{version.description}</td>
        <td>
          {showVersionWarning && (
            <WarningIcon
              asLead
              text={intl.formatMessage({
                description: 'FormVersion: Warning message different application versions',
                defaultMessage: `This form version was created in an application version different
                from the current version. There may be missing configuration after restoring.`,
              })}
            />
          )}
          {version.appRelease}
        </td>
        <td>
          <a
            href="#"
            onClick={event => {
              event.preventDefault();
              restoreVersion(csrftoken, formUuid, version.uuid);
            }}
          >
            <FormattedMessage description="Restore form version link" defaultMessage="Restore" />
          </a>
        </td>
      </tr>
    );
  });

  if (isLoading) {
    return <Loader />;
  } else {
    return (
      <>
        {rows.length > 0 ? (
          <table id="change-history">
            <thead>
              <tr>
                <th scope="col">
                  <FormattedMessage
                    description="Date/time column header"
                    defaultMessage="Date/time"
                  />
                </th>
                <th scope="col">
                  <FormattedMessage description="User column header" defaultMessage="User" />
                </th>
                <th scope="col">
                  <FormattedMessage
                    description="Description column header"
                    defaultMessage="Description"
                  />
                </th>
                <th scope="col">
                  <FormattedMessage
                    description="App version column header"
                    defaultMessage="App version"
                  />
                </th>
                <th scope="col">
                  <FormattedMessage description="Action column header" defaultMessage="Action" />
                </th>
              </tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
        ) : (
          <p>
            <FormattedMessage
              description="No form version history message"
              defaultMessage="This form has no versions."
            />
          </p>
        )}
      </>
    );
  }
};

FormVersionsTable.propTypes = {
  formUuid: PropTypes.string.isRequired,
  currentRelease: PropTypes.string.isRequired,
};

export default FormVersionsTable;
