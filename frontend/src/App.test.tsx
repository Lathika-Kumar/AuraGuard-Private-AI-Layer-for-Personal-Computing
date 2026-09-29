import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

describe('App Component', () => {
  it('renders the AuraGuard navigation and dashboard shell', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByText('AuraGuard')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /system overview/i })).toBeInTheDocument();
    expect(screen.getByText('Memory (ReMind)')).toBeInTheDocument();
    expect(screen.getByText('Privacy Center')).toBeInTheDocument();
  });

  it('renders the ReMind page at /memory', () => {
    render(
      <MemoryRouter initialEntries={['/memory']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /personal context & memory/i })).toBeInTheDocument();
    expect(screen.getByText('+ Add Memory')).toBeInTheDocument();
  });

  it('renders the Privacy Center page at /privacy', () => {
    render(
      <MemoryRouter initialEntries={['/privacy']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /local privacy & shield/i })).toBeInTheDocument();
    expect(screen.getByText(/privacy policy configuration/i)).toBeInTheDocument();
  });

  it('renders the Ask page at /ask', () => {
    render(
      <MemoryRouter initialEntries={['/ask']}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { name: /local context intelligence/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ask auraguard/i })).toBeInTheDocument();
  });
});
