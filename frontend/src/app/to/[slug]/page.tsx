"use client";

import { Suspense, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Form } from "@/types";
import { api } from "@/lib/api";
import RespondentFlow from "@/components/respondent/RespondentFlow";

function PublicForm() {
  const { slug } = useParams<{ slug: string }>();
  const [form, setForm] = useState<Form | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPublicForm(slug).then((res) => setForm(res.form), (e: Error) => setError(e.message));
  }, [slug]);

  if (error) {
    return (
      <main className="grid h-dvh place-items-center bg-[#fafafa] p-6 text-center">
        <div>
          <h1 className="text-2xl">This form isn&apos;t available</h1>
          <p className="mt-2 text-muted">{error}</p>
          <Link href="/" className="mt-6 inline-block rounded-md bg-plum px-4 py-2 font-semibold text-white">
            Go to homepage
          </Link>
        </div>
      </main>
    );
  }
  if (!form) return <Loading />;

  return (
    <main className="h-dvh w-screen">
      <RespondentFlow form={form} />
    </main>
  );
}

const Loading = () => <div className="grid h-dvh place-items-center text-sm text-muted">Loading…</div>;

// useParams needs a Suspense boundary so the static shell can prerender
export default function PublicFormPage() {
  return (
    <Suspense fallback={<Loading />}>
      <PublicForm />
    </Suspense>
  );
}
