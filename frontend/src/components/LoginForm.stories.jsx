import LoginForm from './LoginForm';
import {fn} from '@storybook/test';

export default {
  title: 'Components/LoginForm',
  component: LoginForm,
  args: {
    onLogin: fn(),
  },
};

export const Default = {};
