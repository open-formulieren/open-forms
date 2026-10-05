import {fn} from 'storybook/test';

import Modal, {CONTENT_MODIFIERS} from './Modal';

const UnsafeHTML = ({content}) => <div dangerouslySetInnerHTML={{__html: content}} />;

export default {
  title: 'Admin/Custom/Modals/Base',
  component: Modal,
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
  },

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
    contentModifiers: [],
    children: <UnsafeHTML content="<strong>Sample</strong> modal content." />,
  },
};

export const WithoutTitle = {
  name: 'Without title',

  args: {
    title: '',
    contentModifiers: [],
    children: <UnsafeHTML content="<strong>Sample</strong> modal content." />,
  },
};
