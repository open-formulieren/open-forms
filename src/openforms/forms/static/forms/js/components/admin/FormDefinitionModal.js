import ReactModal from 'react-modal';

ReactModal.setAppElement('#root');

<ReactModal

  isOpen={
    false
  /* Boolean describing if the modal should be shown or not. */}

  onAfterOpen={
    handleAfterOpenFunc
  /* Function that will be run after the modal has opened. */}

  onAfterClose={
    handleAfterCloseFunc
  /* Function that will be run after the modal has closed. */}

  onRequestClose={
    handleRequestCloseFunc
  /* Function that will be run when the modal is requested
     to be closed (either by clicking on overlay or pressing ESC).
     Note: It is not called if isOpen is changed by other means. */}

  closeTimeoutMS={
    0
  /* Number indicating the milliseconds to wait before closing
     the modal. */}

  style={
    { overlay: {}, content: {} }
  /* Object indicating styles to be used for the modal.
     It has two keys, `overlay` and `content`.
     See the `Styles` section for more details. */}

  contentLabel={
    "Example Modal"
  /* String indicating how the content container should be announced
     to screenreaders */}

  portalClassName={
    "ReactModalPortal"
  /* String className to be applied to the portal.
     See the `Styles` section for more details. */}

  overlayClassName={
    "ReactModal__Overlay"
  /* String className to be applied to the overlay.
     See the `Styles` section for more details. */}

  id={
    "some-id"
  /* String id to be applied to the content div. */}

  className={
    "ReactModal__Content"
  /* String className to be applied to the modal content.
     See the `Styles` section for more details. */}

  bodyOpenClassName={
    "ReactModal__Body--open"
  /* String className to be applied to the document.body
     (must be a constant string).
     This attribute when set as `null` doesn't add any class
     to document.body.
     See the `Styles` section for more details. */}

  htmlOpenClassName={
    "ReactModal__Html--open"
  /* String className to be applied to the document.html
     (must be a constant string).
     This attribute is `null` by default.
     See the `Styles` section for more details. */}

  ariaHideApp={
    true
  /* Boolean indicating if the appElement should be hidden */}

  shouldFocusAfterRender={
    true
  /* Boolean indicating if the modal should be focused after render. */}

  shouldCloseOnOverlayClick={
    true
  /* Boolean indicating if the overlay should close the modal */}

  shouldCloseOnEsc={
    true
  /* Boolean indicating if pressing the esc key should close the modal
     Note: By disabling the esc key from closing the modal
     you may introduce an accessibility issue. */}

  shouldReturnFocusAfterClose={
    true
  /* Boolean indicating if the modal should restore focus to the element
     that had focus prior to its display. */}

  role={
    "dialog"
  /* String indicating the role of the modal, allowing the 'dialog' role
     to be applied if desired.
     This attribute is `dialog` by default. */}

  preventScroll={
    false
  /* Boolean indicating if the modal should use the preventScroll flag when
     restoring focus to the element that had focus prior to its display. */}

  parentSelector={
    () => document.body
  /* Function that will be called to get the parent element
     that the modal will be attached to. */}

  aria={
    {
      labelledby: "heading",
      describedby: "full_description"
    }
  /* Additional aria attributes (optional). */}

  data={
    { background: "green" }
  /* Additional data attributes (optional). */}

  testId={
    ""
  /* String testId that renders a data-testid attribute in the DOM,
    useful for testing. */}

  overlayRef={
    setOverlayRef
  /* Overlay ref callback. */}

  contentRef={
    setContentRef
  /* Content ref callback. */}

  overlayElement={
    (props, contentElement) => <div {...props}>{contentElement}</div>
  /* Custom Overlay element. */}

  contentElement={
    (props, children) => <div {...props}>{children}</div>
  /* Custom Content element. */}
  >
    <p>Modal Content</p>
</ReactModal>
