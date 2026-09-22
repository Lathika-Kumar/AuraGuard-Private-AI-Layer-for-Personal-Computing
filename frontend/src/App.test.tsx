import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

describe('App', () => {
  it('renders the AuraGuard dashboard shell', () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText('AuraGuard')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /system overview/i })).toBeInTheDocument();
  });
});
