import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProcessingProgress } from '../ProcessingProgress';

describe('ProcessingProgress', () => {
  it('should render the component with message and progress', () => {
    render(
      <ProcessingProgress
        stage="extracting"
        message="Extracting text from PDF..."
        progress={10}
      />
    );

    expect(screen.getByText('Extracting text from PDF...')).toBeInTheDocument();
    expect(screen.getByText('10%')).toBeInTheDocument();
  });

  it('should display correct icon for extracting stage', () => {
    const { container } = render(
      <ProcessingProgress
        stage="extracting"
        message="Extracting..."
        progress={10}
      />
    );

    expect(container.textContent).toContain('📄');
  });

  it('should display correct icon for summarizing stage', () => {
    const { container } = render(
      <ProcessingProgress
        stage="summarizing"
        message="Summarizing..."
        progress={50}
      />
    );

    expect(container.textContent).toContain('✨');
  });

  it('should display correct icon for formatting stage', () => {
    const { container } = render(
      <ProcessingProgress
        stage="formatting"
        message="Formatting..."
        progress={90}
      />
    );

    expect(container.textContent).toContain('📝');
  });

  it('should display correct icon for complete stage', () => {
    const { container } = render(
      <ProcessingProgress
        stage="complete"
        message="Complete!"
        progress={100}
      />
    );

    expect(container.textContent).toContain('✅');
  });

  it('should display correct icon for error stage', () => {
    const { container } = render(
      <ProcessingProgress
        stage="error"
        message="Error occurred"
        progress={0}
      />
    );

    expect(container.textContent).toContain('❌');
  });

  it('should display default icon for unknown stage', () => {
    const { container } = render(
      <ProcessingProgress
        stage="unknown"
        message="Unknown stage"
        progress={0}
      />
    );

    expect(container.textContent).toContain('⏳');
  });

  it('should display partial summary when provided', () => {
    render(
      <ProcessingProgress
        stage="summarizing"
        message="Processing..."
        progress={50}
        partialSummary="This is a partial summary being generated..."
      />
    );

    expect(screen.getByText('Summary (in progress):')).toBeInTheDocument();
    expect(screen.getByText('This is a partial summary being generated...')).toBeInTheDocument();
  });

  it('should not display partial summary section when not provided', () => {
    render(
      <ProcessingProgress
        stage="extracting"
        message="Extracting..."
        progress={10}
      />
    );

    expect(screen.queryByText('Summary (in progress):')).not.toBeInTheDocument();
  });

  it('should round progress to whole number', () => {
    render(
      <ProcessingProgress
        stage="summarizing"
        message="Processing..."
        progress={45.7}
      />
    );

    expect(screen.getByText('46%')).toBeInTheDocument();
  });

  it('should handle zero progress', () => {
    render(
      <ProcessingProgress
        stage="idle"
        message="Starting..."
        progress={0}
      />
    );

    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('should handle 100% progress', () => {
    render(
      <ProcessingProgress
        stage="complete"
        message="Done!"
        progress={100}
      />
    );

    expect(screen.getByText('100%')).toBeInTheDocument();
  });
});
