import {fn} from 'storybook/test';

import SubmitRow from 'components/admin/forms/SubmitRow';

import FormModal from './FormModal';

export default {
  title: 'Admin/Custom/Modals/Form',
  component: FormModal,
  decorators: [
    Story => (
      <div style={{maxInlineSize: '600px', margin: '0 auto'}}>
        <div>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt
          ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
          ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
          reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur
          sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id
          est laborum.
        </div>
        <Story />
      </div>
    ),
  ],

  args: {
    isOpen: true,
    closeModal: fn(),
    children: (
      <>
        <p>Content before the submit row</p>
        <SubmitRow isDefault />
      </>
    ),
  },

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
    extraModifiers: [],
  },
};
