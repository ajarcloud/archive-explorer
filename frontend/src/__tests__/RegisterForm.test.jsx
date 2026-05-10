import {describe, it, expect, vi, beforeEach} from 'vitest';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegisterForm from '../components/RegisterForm';

vi.mock('../api', () => ({
  default: {post: vi.fn()},
}));

import api from '../api';

beforeEach(() => {
  vi.clearAllMocks();
});

describe('RegisterForm', () => {
  it('renders email, password fields and register button', () => {
    render(<RegisterForm onRegister={vi.fn()} />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(
      screen.getByRole('button', {name: /register/i})
    ).toBeInTheDocument();
  });

  it('calls onRegister with token on success', async () => {
    api.post.mockResolvedValueOnce({access_token: 'reg-tok'});
    const onRegister = vi.fn();
    render(<RegisterForm onRegister={onRegister} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'new@b.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'secret123');
    await userEvent.click(
      screen.getByRole('button', {name: /register/i})
    );

    await waitFor(() => {
      expect(onRegister).toHaveBeenCalledWith('reg-tok');
    });
  });

  it('shows error when email already registered', async () => {
    api.post.mockRejectedValueOnce({
      data: {detail: 'Email already registered'},
    });
    render(<RegisterForm onRegister={vi.fn()} />);

    await userEvent.type(screen.getByLabelText(/email/i), 'dup@b.com');
    await userEvent.type(screen.getByLabelText(/password/i), 'secret123');
    await userEvent.click(
      screen.getByRole('button', {name: /register/i})
    );

    await waitFor(() => {
      expect(
        screen.getByText('Email already registered')
      ).toBeInTheDocument();
    });
  });
});
