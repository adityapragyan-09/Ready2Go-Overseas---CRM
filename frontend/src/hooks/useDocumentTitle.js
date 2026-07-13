import { useEffect } from 'react';

/**
 * Custom hook to dynamically update the browser tab document title.
 * Automatically appends the branding suffix.
 */
export const useDocumentTitle = (title) => {
  useEffect(() => {
    document.title = `${title} | Ready2Go Overseas CRM`;
  }, [title]);
};

export default useDocumentTitle;
