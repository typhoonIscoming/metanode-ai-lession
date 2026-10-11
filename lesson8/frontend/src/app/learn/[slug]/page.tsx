import Link from 'next/link';
import { notFound } from 'next/navigation';
import { articlesApi } from '@/lib/api';
import type { Metadata } from 'next';

interface PageProps { params: Promise<{ slug: string }> }

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  try {
    const a = await articlesApi.bySlug(slug);
    return { title: `${a.title} — web3.career Learn`, description: a.excerpt };
  } catch { return { title: 'Article not found' }; }
}

export default async function ArticlePage({ params }: PageProps) {
  const { slug } = await params;
  let a;
  try { a = await articlesApi.bySlug(slug); } catch { notFound(); }
  if (!a) notFound();

  return (
    <article className="mx-auto max-w-3xl px-6 pt-14 pb-20">
      <div className="text-xs font-mono text-zinc-500 mb-4">
        <Link href="/learn" className="hover:text-cyan-300">/learn</Link>
        <span className="text-zinc-700"> / </span>
        <span className="text-zinc-400">{a.category}</span>
      </div>

      <span className="chip">{a.category}</span>
      <h1 className="mt-4 text-4xl md:text-5xl font-semibold tracking-tight leading-tight">{a.title}</h1>
      <p className="mt-3 text-zinc-400">{a.excerpt}</p>
      <div className="mt-4 flex items-center gap-x-4 gap-y-1 text-xs font-mono text-zinc-500">
        <span>by {a.author}</span>
        <span>·</span>
        <span>{new Date(a.publishedAt).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })}</span>
        {a.readMinutes && <><span>·</span><span>{a.readMinutes} min read</span></>}
      </div>

      {a.externalUrl && (
        <a href={a.externalUrl} target="_blank" rel="noopener noreferrer" className="mt-6 inline-flex btn-glow rounded-md px-5 py-2 text-sm font-medium">Open external ↗</a>
      )}

      <div className="prose prose-invert mt-10 max-w-none text-zinc-200 leading-relaxed whitespace-pre-wrap">
        {a.contentMd}
      </div>
    </article>
  );
}
