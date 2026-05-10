import RegisterForm from './RegisterForm';
import {fn} from '@storybook/test';

export default {
  title: 'Components/RegisterForm',
  component: RegisterForm,
  args: {
    onRegister: fn(),
  },
};

export const Default = {};
