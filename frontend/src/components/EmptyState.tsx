import { type ReactNode } from 'react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {icon && <div className="text-gray-300 mb-4">{icon}</div>}
      <h3 className="text-lg font-medium text-text mb-2">{title}</h3>
      {description && <p className="text-sm text-text-secondary mb-6 text-center max-w-md">{description}</p>}
      {action}
    </div>
  );
}
