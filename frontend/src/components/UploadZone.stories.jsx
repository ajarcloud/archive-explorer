import {fn} from '@storybook/test';
import UploadZone from './UploadZone';

export default {
  title: 'Components/UploadZone',
  component: UploadZone,
  args: {
    onUploaded: fn(),
  },
};

export const Default = {};

export const DragOver = {
  play: async ({canvasElement}) => {
    const dropzone = canvasElement.querySelector('.dropzone');
    dropzone.dispatchEvent(new Event('dragover', {bubbles: true}));
  },
};
