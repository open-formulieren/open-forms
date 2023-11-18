import SubmitRow from 'components/admin/forms/SubmitRow';

import FormModal from './FormModal';

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
    <FormModal
      isOpen={viewMode === 'story' ? args.isOpen : false}
      title={args.title}
      closeModal={args.closeModal}
      extraModifiers={args.extraModifiers}
      children={null}
      parentSelector={() => document.getElementById('storybook-root')}
      ariaHideApp={false}
    >
      <p>Content before the submit row</p>
      <SubmitRow isDefault />
    </FormModal>
  </div>
);

export default {
  title: 'Admin/Custom/Modals/Form',
  component: FormModal,
  render,

  argTypes: {
    children: {
      table: {
        disable: true,
      },
    },
  },
};

export const Default = {
  args: {
    title: 'A form modal with submit row',
    isOpen: true,
    closeModal: () => alert('Close modal triggered'),
    extraModifiers: [],
  },
};
