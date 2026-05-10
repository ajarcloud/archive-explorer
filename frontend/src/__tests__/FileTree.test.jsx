import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FileTree from '../components/FileTree';

const tree = {
  archive_id: "abc123",
  name: "myarchive",
  is_dir: true,
  size: 25,
  children: [
    { name: "readme.md", path: "readme.md", is_dir: false, size: 10, children: null },
    {
      name: "src",
      path: "src",
      is_dir: true,
      size: 15,
      children: [
        { name: "main.py", path: "src/main.py", is_dir: false, size: 15, children: null },
      ],
    },
  ],
};

describe("FileTree", () => {
  it("renders nothing when tree is null", () => {
    const { container } = render(<FileTree tree={null} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders archive name", () => {
    render(<FileTree tree={tree} />);
    expect(screen.getByText("myarchive")).toBeInTheDocument();
  });

  it("renders top-level files", () => {
    render(<FileTree tree={tree} />);
    expect(screen.getByText("readme.md")).toBeInTheDocument();
  });

  it("shows directory collapsed by default", () => {
    render(<FileTree tree={tree} />);
    expect(screen.queryByText("main.py")).not.toBeInTheDocument();
  });

  it("reveals children when directory is clicked", async () => {
    render(<FileTree tree={tree} />);
    await userEvent.click(screen.getByText("src"));
    expect(screen.getByText("main.py")).toBeInTheDocument();
  });

  it("collapses directory on second click", async () => {
    render(<FileTree tree={tree} />);
    const src = screen.getByText("src");
    await userEvent.click(src);
    expect(screen.getByText("main.py")).toBeInTheDocument();
    await userEvent.click(src);
    expect(screen.queryByText("main.py")).not.toBeInTheDocument();
  });

  it("displays file sizes", () => {
    render(<FileTree tree={tree} />);
    expect(screen.getByText("10 B")).toBeInTheDocument();
  });
});
