export const saveAndContinueButtonQuery = "form input[type=submit][name=_continue]";

const saveAndContinueHandler = (event) => {
    // because of the way React initializes we run the querySelector when the buttons is pressed
    const button = document.querySelector(saveAndContinueButtonQuery);
    if (!button) {
        console.warn("Cannot find 'Save & Continue' button");
    } else {
        event.preventDefault();
        button.click();
    }
}

const enableKeyboardShortcuts = () => {
    window.addEventListener('DOMContentLoaded', (e) => {
        document.addEventListener('keydown', event => {
            // add a Ctrl+S keyboard listener as trigger for Django's standard "Save & Continue" button
            if (event.ctrlKey && event.key === 's') {
                saveAndContinueHandler(event);
            }
        });
    });
};

export default enableKeyboardShortcuts;
