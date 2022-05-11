import React, {useEffect, useState} from 'react';
import PropTypes from 'prop-types';
import { useGlobalState } from 'state-pool';
import classNames from 'classnames';
import useTimeout from 'react-use/esm/useTimeout';
import useTimeoutFn from 'react-use/esm/useTimeoutFn';
import {
    FormattedDate,
    FormattedMessage,
    FormattedRelativeTime,
    FormattedTime,
    useIntl,
} from 'react-intl';

import { sessionExpiresAt } from '../../utils/session-expiry';
import FormModal from './FormModal';
import ActionButton, {SubmitAction} from './forms/ActionButton';
import SubmitRow from './forms/SubmitRow';


const WARN_SESSION_TIMEOUT_SECONDS = 2 * 60; // 2 minutes, in seconds
const WARN_SESSION_TIMEOUT_FACTOR = 0.9; // once 90% of the session expiry time has passed, show a warning


const isToday = (date) => {
    const today = new Date();
    return (
        today.getFullYear() === date.getFullYear()
        && today.getMonth() === date.getMonth()
        && today.getDate() === date.getDate()
    );
};


const RelativeTimeToExpiry = ({ numSeconds, raw=false }) => {
    // more than 24 hours -> don't bother
    if (numSeconds >= (3600 * 24)) return null;
    const component = <FormattedRelativeTime value={numSeconds} numeric="auto" updateIntervalInSeconds={1} />;
    if (raw) return component;
    return <>&nbsp;({component})</>;
}


const SessionStatusWrapper = ({ showInModal=false, modalTitle, submitRowContent=null, onCloseModal, children }) => {
    const intl = useIntl();

    if (!showInModal) {
        return (
            <div className="session-status-wrapper session-status-wrapper--no-modal">
                {children}
            </div>
        );
    }

    return (
        <FormModal isOpen title={modalTitle} closeModal={onCloseModal} onFormSubmit={(event) => {
            event.preventDefault();
            onCloseModal();
        }} extraModifiers={['small']}>
            <div className="session-status-wrapper session-status-wrapper--modal">
                {children}
            </div>
            <SubmitRow isDefault>
                {
                    submitRowContent ?? (
                        <SubmitAction
                            text={intl.formatMessage({description: 'Session status modal close button', defaultMessage: 'Back to login'})}
                        />
                    )
                }
            </SubmitRow>
        </FormModal>
    );
};

SessionStatusWrapper.propTypes = {
    showInModal: PropTypes.bool,
    modalTitle: PropTypes.node,
    children: PropTypes.node,
    onCloseModal: PropTypes.func.isRequired,
    submitRowContent: PropTypes.node,
};


const useTriggerWarning = (numSeconds, timeToExpiryInMS) => {
    let timeout;

    const [showWarning, setShowWarning] = useState(false);

    // no time available
    if (numSeconds == null) {
        timeout = 10 * 3600 * 1000; // 10 hours as a fallback
    } else {
        // re-render WARN_SESSION_TIMEOUT_FACTOR before the session expires to show a warning
        const timeToWarningFromFactorInMS = WARN_SESSION_TIMEOUT_FACTOR * numSeconds * 1000;
        // re-render WARN_SESSION_TIMEOUT_SECONDS before the expiry timestamp
        const timeToWarningFromFixedOffsetInMS = timeToExpiryInMS - (WARN_SESSION_TIMEOUT_SECONDS * 1000);

        // it's possible the session duration is shorter than the upfront notice we give,
        // leading to negative values for timeToWarningFromFixedOffsetInMS
        if (timeToWarningFromFixedOffsetInMS <= 0) {
            timeout = timeToWarningFromFactorInMS;
        } else {
            // grab whichever is soonest
            timeout = Math.min(timeToWarningFromFactorInMS, timeToWarningFromFixedOffsetInMS);
        }
    }

    // ensure we have a positive timeout value
    const timeToWarningInMS = Math.max(timeout, 0);

    const [isReady, cancel, reset] = useTimeoutFn(
        () => setShowWarning(true),
        timeToWarningInMS
    );
    return [
        showWarning,
        () => {
            setShowWarning(false);
            reset();
        },
    ];
};


const SessionStatus = () => {
    const intl = useIntl();
    const [warningDismissed, setWarningDismissed] = useState(false);

    const [sessionExpiry] = useGlobalState(sessionExpiresAt);
    const {date, numSeconds, authFailure} = sessionExpiry;
    const now = new Date();

    // re-render when the session is expired to show the error message
    const timeToExpiryInMS = date ? Math.max((date - now), 0) : 1000 * 3600 * 10; // 10 hour fallback in case there's no date
    const [,cancelExpiryTimeout, resetExpiryTimeout] = useTimeout(timeToExpiryInMS);
    const [warningTriggered, resetWarningTriggered] = useTriggerWarning(numSeconds, timeToExpiryInMS);

    // reset if a new timeout date is received
    useEffect(
        () => {
            if (!date) {
                cancelExpiryTimeout();
                return;
            }
            resetExpiryTimeout();
            resetWarningTriggered();
            setWarningDismissed(false);
        },
        [date]
    );

    const showWarning = !warningDismissed && warningTriggered;
    const isExpired = date && new Date() >= date;
    const showInModal = Boolean(showWarning || authFailure || isExpired);

    const className = classNames(
        'session-status',
        {
            'session-status--auth-failed': authFailure,
            'session-status--expired': isExpired,
            'session-status--in-modal': showInModal,
        },
    );

    // if we don't have any expiry date information, we can't show anything -> abort early.
    if (date == null) return null;

    let onCloseModal = () => {
        const params = new URLSearchParams({next: window.location.pathname});
        window.location = `/admin/login/?${params}`;
    };

    let modalTitle;
    let content;
    let submitRowContent;

    const secondsToExpiry = parseInt((date - now) / 1000);
    const loginToContinue = (
        <FormattedMessage description="Call to action to log in again" defaultMessage="Please log in again to continue." />
    );

    if (authFailure) {
        modalTitle = (
            <FormattedMessage description="Modal title API call failed with HTTP 401" defaultMessage="Authentication failure" />
        );
        content = (
            <>
                <p><FormattedMessage
                    description="Session expiry notice - API call failed with 401"
                    defaultMessage="Sorry, we couldn't do that because you are logged out - this may be because your session expired."
                /></p>
                <p>{loginToContinue}</p>
            </>
        );
    } else if (isExpired) {
        modalTitle = (
            <FormattedMessage description="Modal title session expired" defaultMessage="Session expired" />
        );
        content = (
            <>
                <p><FormattedMessage description="Session expiry notice - expired" defaultMessage="Your session has expired." /></p>
                <p>{loginToContinue}</p>
            </>
        );
    } else if (showWarning) {
        modalTitle = (
            <FormattedMessage description="Model title session expiry warning" defaultMessage="Session will expire" />
        );
        content = (
            <FormattedMessage
                description="Session expiry warning (in modal)"
                defaultMessage="Your session is about to expire {delta}. Extend your session if you wish to continue."
                values={{
                    delta: <RelativeTimeToExpiry numSeconds={secondsToExpiry} raw />,
                }}
            />
        );
        submitRowContent = (
            <>
                <ActionButton
                    type="button"
                    text={intl.formatMessage({
                        description: 'Session expiry warning "do nothing" button',
                        defaultMessage: 'Do nothing',
                    })}
                    onClick={event => {
                        event.preventDefault();
                        setWarningDismissed(true);
                    }}
                />
                <ActionButton
                    type="button"
                    className="default"
                    text={intl.formatMessage({
                        description: 'Extend session button',
                        defaultMessage: 'Stay logged in',
                    })}
                    onClick={event => {
                        event.preventDefault();
                        console.log('Ok');
                        // TODO
                    }}
                />
            </>
        );
        onCloseModal = () => setWarningDismissed(true);
    } else {
        content = (
            <>
                <FormattedMessage
                    description="Session expiry notice"
                    defaultMessage="Session expires {expiresToday, select, true {{relativeTimeToExpiry}} other {on {expiryDate} at {expiryTime}}}"
                    values={{
                        expiresToday: isToday(date),
                        relativeTimeToExpiry: <RelativeTimeToExpiry numSeconds={secondsToExpiry} key={date / 1000} raw />,
                        expiryDate: <FormattedDate value={date} />,
                        expiryTime: <FormattedTime value={date} />,
                    }}
                />
            </>
        );
    }

    return (
        <SessionStatusWrapper
            showInModal={showInModal}
            modalTitle={modalTitle}
            onCloseModal={onCloseModal}
            submitRowContent={submitRowContent}
        >
            <div className={className}>
                {content}
            </div>
        </SessionStatusWrapper>
    );
};

SessionStatus.propTypes = {
};


export default SessionStatus;
