import ActionButton from './ActionButton';
import SubmitRow from './SubmitRow';

export default {
  title: 'Admin/Django/SubmitRow',
  component: SubmitRow,
  args: {
    preventDefault: true,
    isDefault: false,
    extraClassName: 'foo',
    children: (
      <>
        <ActionButton name="ActionButton" text="Save" />
        <ActionButton name="ActionButton" text="Save and continue editing" />
      </>
    ),
  },
  argTypes: {
    children: {
      control: {
        disable: true,
      },
    },
  },
};

export const Default = {};
