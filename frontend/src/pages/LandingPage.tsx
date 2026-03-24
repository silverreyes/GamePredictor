import { Link } from "react-router";

export function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="font-display text-[1.75rem] font-bold text-foreground">
        NFL Nostradamus
      </h1>
      <p className="text-muted-foreground">Landing page coming soon.</p>
      <Link
        to="/this-week"
        className="rounded-md bg-primary px-6 py-3 text-sm text-primary-foreground transition-colors hover:bg-primary/90"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}
