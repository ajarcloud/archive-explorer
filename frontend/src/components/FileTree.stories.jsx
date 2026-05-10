import FileTree from './FileTree';

export default {
  title: 'Components/FileTree',
  component: FileTree,
};

const emptyArchive = {
  name: 'empty.zip',
  is_dir: true,
  size: 0,
  children: [],
};

const flatFiles = {
  name: 'documents.zip',
  is_dir: true,
  size: 2468000,
  children: [
    {name: 'README.md', is_dir: false, size: 1420},
    {name: 'report.pdf', is_dir: false, size: 2100000},
    {name: 'notes.txt', is_dir: false, size: 366580},
  ],
};

const nestedDirs = {
  name: 'project.tar.zst',
  is_dir: true,
  size: 5120000,
  children: [
    {
      name: 'src',
      is_dir: true,
      size: 3100000,
      children: [
        {name: 'index.js', is_dir: false, size: 12000},
        {name: 'utils.js', is_dir: false, size: 8000},
        {
          name: 'lib',
          is_dir: true,
          size: 3080000,
          children: [
            {name: 'big-file.bin', is_dir: false, size: 3000000},
            {name: 'helper.js', is_dir: false, size: 80000},
          ],
        },
      ],
    },
    {
      name: 'tests',
      is_dir: true,
      size: 420000,
      children: [
        {name: 'app.test.js', is_dir: false, size: 350000},
        {name: 'utils.test.js', is_dir: false, size: 70000},
      ],
    },
    {name: 'package.json', is_dir: false, size: 2400},
    {name: '.gitignore', is_dir: false, size: 180},
  ],
};

export const Empty = {args: {tree: emptyArchive}};

export const FlatFiles = {args: {tree: flatFiles}};

export const NestedDirectories = {args: {tree: nestedDirs}};

export const Null = {args: {tree: null}};
