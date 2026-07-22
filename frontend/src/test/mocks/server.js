/**
 * MSW (Mock Service Worker) test server setup.
 *
 * Ready to use when MSW is installed as a dev dependency:
 *   npm install --save-dev msw
 *
 * --- Usage ---
 * 1. Uncomment the code below
 * 2. Import and start the server in src/test/setup.js:
 *      import { server } from './mocks/server';
 *      beforeAll(() => server.listen());
 *      afterEach(() => server.resetHandlers());
 *      afterAll(() => server.close());
 * 3. Override handlers per test with server.use(...)
 *
 * Until MSW is installed, tests rely on vi.mock patterns to
 * stub the axios-based config/api module. See __tests__/Login.test.jsx
 * for an example.
 */

// import { setupServer } from 'msw/node';
// import { handlers } from './handlers';
//
// export const server = setupServer(...handlers);
