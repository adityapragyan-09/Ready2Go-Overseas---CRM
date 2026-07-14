import { useEffect } from 'react';

/**
 * Custom hook to dynamically update the browser tab document title.
 * Automatically appends the branding suffix.
 */
import { appConfig } from '../config/appConfig';

export const useDocumentTitle = (title) => {
  useEffect(() => {
    document.title = `${title} | ${appConfig.APP_NAME}`;
  }, [title]);
};

export default useDocumentTitle;
