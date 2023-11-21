import Modal, {CONTENT_MODIFIERS} from './Modal';

const UnsafeHTML = ({content}) => <div dangerouslySetInnerHTML={{__html: content}} />;

const render = (args, {viewMode}) => (
  <div style={viewMode === 'story' ? {maxWidth: '600px', margin: '0 auto'} : undefined}>
    {viewMode === 'story' ? (
      <div>
        Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
        labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco
        laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in
        voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat
        cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
      </div>
    ) : (
      <div>
        The modal itself is disabled in docs view mode - use the canvas to see the behaviour and
        appearance.
      </div>
    )}
    <Modal
      isOpen={viewMode === 'story' ? args.isOpen : false}
      title={args.title}
      closeModal={args.closeModal}
      contentModifiers={args.contentModifiers}
      children={null}
      parentSelector={() => document.getElementById('storybook-root')}
      ariaHideApp={false}
    >
      <UnsafeHTML content={args.content} />
    </Modal>
  </div>
);

export default {
  title: 'Admin/Custom/Modals/Base',
  component: Modal,
  render,

  argTypes: {
    contentModifiers: {
      options: CONTENT_MODIFIERS,

      control: {
        type: 'check',
      },
    },

    children: {
      table: {
        disable: true,
      },
    },
  },
};

export const Open = {
  name: 'Open',

  args: {
    title: 'Example title',
    isOpen: true,
    closeModal: () => alert('Close modal triggered'),
    contentModifiers: [],
    content: '<strong>Sample</strong> modal content.',
  },
};

export const WithoutTitle = {
  name: 'Without title',

  args: {
    title: '',
    isOpen: true,
    closeModal: () => alert('Close modal triggered'),
    contentModifiers: [],
    content: '<strong>Sample</strong> modal content.',
  },
};
