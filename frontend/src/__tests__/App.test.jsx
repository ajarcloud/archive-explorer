import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

beforeEach(() => {
  localStorage.clear();
});

describe("App", () => {
  it("shows login page when no token", () => {
    render(<App />);
    expect(screen.getByText('Archive Explorer')).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /log in/i })).toBeInTheDocument();
  });

  it("shows dashboard when token exists", () => {
    localStorage.setItem('token', 'fake-token');
    render(<App />);
    expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();
  });

  it("can toggle to register form", async () => {
    render(<App />);
    const { userEvent } = await import("@testing-library/user-event");
    await userEvent.click(screen.getByText("Register"));
    expect(screen.getByRole("button", { name: /register/i })).toBeInTheDocument();
  });

  it("logs out when logout button clicked", async () => {
    localStorage.setItem('token', 'fake-token');
    render(<App />);
    const { userEvent } = await import("@testing-library/user-event");
    await userEvent.click(screen.getByRole("button", { name: /log out/i }));
    expect(screen.getByRole("button", { name: /log in/i })).toBeInTheDocument();
    expect(localStorage.getItem('token')).toBeNull();
  });
});
