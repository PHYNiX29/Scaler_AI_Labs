import Link from "next/link";

const FEATURES = [
  ["Conversational forms", "One question at a time, with smooth transitions and full keyboard navigation."],
  ["Branching logic", "Send each respondent down a different path based on what they answer."],
  ["Results at a glance", "Per-question summaries, individual responses, completion rate and CSV export."],
];

export default function LandingPage() {
  return (
    <div className="landing-hero flex min-h-dvh flex-col text-white">
      <header className="flex items-center justify-between px-6 py-5 sm:px-10">
        <Link href="/" className="flex items-center gap-2 text-xl font-semibold">
          <span className="flex gap-0.5" aria-hidden>
            <span className="h-5 w-1.5 rounded-sm bg-white" />
            <span className="h-5 w-6 rounded-md bg-white" />
          </span>
          Typeform clone
        </Link>
        <Link href="/dashboard" className="rounded-lg bg-white px-4 py-2 text-sm font-medium text-ink">
          Open workspace
        </Link>
      </header>

      <main className="flex flex-1 flex-col items-center px-6 pt-16 text-center">
        <p className="text-xs font-medium tracking-wide text-[#d9b8f2]">FORMS &amp; WORKFLOWS</p>
        <h1 className="mt-5 font-serif text-5xl leading-[1.05] sm:text-7xl">
          The form is only
          <br />
          the beginning
        </h1>
        <p className="mt-6 max-w-md text-lg text-white/90">Build a form, share it with a link, and watch the responses come in.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link href="/dashboard" className="rounded-lg bg-white px-5 py-3 font-medium text-ink">
            Get started—it&apos;s free
          </Link>
          <Link href="/to/customer-feedback" className="rounded-lg border border-white/30 px-5 py-3 font-medium">
            Try a live form
          </Link>
        </div>

        <ul className="mt-20 grid w-full max-w-5xl gap-5 pb-16 sm:grid-cols-3">
          {FEATURES.map(([title, text]) => (
            <li key={title} className="rounded-2xl bg-white/10 p-6 text-left backdrop-blur">
              <h2 className="text-lg font-medium">{title}</h2>
              <p className="mt-2 text-sm text-white/75">{text}</p>
            </li>
          ))}
        </ul>
      </main>
    </div>
  );
}
