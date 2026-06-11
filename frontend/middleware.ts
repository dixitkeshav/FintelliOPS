import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/** Showcase build: no auth gate — agent pipeline is open for demo. */
export function middleware(_req: NextRequest) {
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image).*)'],
};
