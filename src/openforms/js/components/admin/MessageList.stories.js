import MessageList from './MessageList';

export default {
  title: 'Admin / Django / MessageList',
  component: MessageList,
};

export const Success = {
  args: {
    messages: [
      {
        level: 'success',
        message: 'A success message',
      },
    ],
  },
};

export const Warning = {
  args: {
    messages: [
      {
        level: 'warning',
        message: 'A warning message',
      },
    ],
  },
};

export const Error = {
  args: {
    messages: [
      {
        level: 'error',
        message: 'An error message',
      },
    ],
  },
};
