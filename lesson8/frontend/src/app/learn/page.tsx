import Link from 'next/link';
import { articlesApi, type ArticleDto } from '@/lib/api';
import { Tilt } from '@/components/tilt';

export const revalidate = 120;

const CATEGORY_LABEL: Record<string, string> = {
  article:    'Articles',
  book:       'Books',
  course:     'Courses',
  tutorial:   'Tutorials',
  video:      'Videos',
  bootcamp:   'Bootcamps',
  news:       'News',
  whitepaper: 'Whitepapers',
};

export default async function LearnPage() {
  const { data } = await articlesApi.list({ limit: 100 });
  const grouped = new Map<string, ArticleDto[]>();
  for (const a of data) {
    const arr = grouped.get(a.category) ?? [];
    arr.push(a);
    grouped.set(a.category, arr);
  }

  return (
    <div className="mx-auto max-w-7xl px-6 pt-14 pb-20">
      <div className="text-xs font-mono text-zinc-500 uppercase tracking-widest mb-3">/learn</div>
      <h1 className="text-4xl md:text-5xl font-semibold tracking-tight">
        Learn <span className="holo-text">web3</span> with these free resources
      </h1>
      <p className="mt-3 text-zinc-400 max-w-2xl">
        Curated articles, books, courses, bootcamps and tutorials. Most are free.
      </p>

      {Array.from(grouped.entries()).map(([category, items]) => (
        <section key={category} className="mt-12">
          <h2 className="text-xl font-semibold tracking-tight mb-4">{CATEGORY_LABEL[category] ?? category}</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((a) => (
              <ArticleCard key={a.id} a={a} />
            ))}
          </div>
        </section>
      ))}
      {data.length === 0 && (
        <div className="glass rounded-xl p-10 text-center text-zinc-500 mt-10">
          No articles indexed yet — run <code className="font-mono text-cyan-300">pnpm db:seed</code> in the backend.
        </div>
      )}
    </div>
  );
}

function ArticleCard({ a }: { a: ArticleDto }) {
  const gradient = a.coverGradient ?? 'from-cyan-500/30 to-violet-500/30';
  const isExternal = !!a.externalUrl;
  const href = isExternal ? a.externalUrl! : `/learn/${a.slug}`;
  return (
    <Tilt className="fade-up">
      <Link href={href} target={isExternal ? '_blank' : undefined} rel={isExternal ? 'noopener noreferrer' : undefined} className="glass group rounded-xl overflow-hidden block">
        <div className={`h-24 bg-gradient-to-br ${gradient} relative`}>
          <span className="absolute top-2 right-2 chip">{a.category}</span>
          {!a.isFree && <span className="absolute top-2 left-2 chip chip-violet">paid</span>}
        </div>
        <div className="p-5">
          <h3 className="font-medium text-[15px] text-zinc-100 group-hover:text-cyan-200 transition line-clamp-2">{a.title}</h3>
          <p className="text-sm text-zinc-400 mt-2 line-clamp-3">{a.excerpt}</p>
          <div className="mt-3 flex items-center justify-between text-xs font-mono text-zinc-500">
            <span>{a.author}</span>
            <span>{a.readMinutes ? `${a.readMinutes} min` : isExternal ? 'external ↗' : ''}</span>
          </div>
        </div>
      </Link>
    </Tilt>
  );
}
