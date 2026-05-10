import {describe, it, expect, vi, beforeEach} from 'vitest';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginForm from '../components/LoginForm';

vi.mock('../api', () => ({
  default: {post: vi.fn()},
}));

import api from '../api';

beforeEach(() => {
  vi.clearAllMocks();
});

describe('LoginForm', () => {
  it('renders email and password fields', () => {
    render(<LoginForm onLogin={vi.fn()} />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', {name: /log in/i})
    ).toBeInTheDocument();
  });

  it('calls onLogin with token on success', async () => {
    api.post.mockResolvedValueOnce({access_token: 'tok'});
    const onLogin = vi.fn();
    render(<LoginForm onLogin={onLogin} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'a@b.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'pass');
    await userEvent.click(
      screen.getByRole('button', {name: /log in/i})
    );

    await waitFor(() => {
      expect(onLogin).toHaveBeenCalledWith('tok');
    });
  });

  it('shows error on failure', async () => {
    api.post.mockRejectedValueOnce({
      data: {detail: 'Invalid credentials'},
    });
    render(<LoginForm onLogin={vi.fn()} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'a@b.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'wrong');
    await userEvent.click(
      screen.getByRole('button', {name: /log in/i})
    );

    await waitFor(() => {
      expect(
        screen.getByText('Invalid credentials')
      ).toBeInTheDocument();
    });
  });
});
