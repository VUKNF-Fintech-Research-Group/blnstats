import { NextResponse } from 'next/server';



export function middleware(request) {
  // Clone the request headers
  const requestHeaders = new Headers(request.headers);
  
  // Set the x-current-path header with the pathname
  requestHeaders.set('x-current-path', request.nextUrl.pathname);
  
  // Return the response with the modified headers
  return NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });
}



// Configure which paths the middleware runs on
export const config = {
  matcher: [
    // Apply to all paths except for API routes, static files, etc.
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};