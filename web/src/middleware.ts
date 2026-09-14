import { clerkMiddleware } from "@clerk/nextjs/server";

// Clerk now recommends resource-based auth checks (done in each page/layout)
// over middleware path-matching, which can diverge from actual route
// resolution. This middleware only establishes the auth context; /onboarding
// and /settings/preferences each redirect to /sign-in themselves when signed out.
export default clerkMiddleware();

export const config = {
  matcher: [
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    "/(api|trpc)(.*)",
  ],
};
