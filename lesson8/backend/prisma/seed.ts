import { PrismaClient, TagCategory, Seniority, EmploymentType, ApplyType } from '@prisma/client';
import { hash } from 'bcryptjs';
import { randomBytes } from 'crypto';

const prisma = new PrismaClient();

const TAGS: Array<{ slug: string; name: string; category: TagCategory }> = [
  { slug: 'solidity',     name: 'Solidity',      category: 'skill' },
  { slug: 'rust',         name: 'Rust',          category: 'skill' },
  { slug: 'react',        name: 'React',         category: 'skill' },
  { slug: 'typescript',   name: 'TypeScript',    category: 'skill' },
  { slug: 'golang',       name: 'Go',            category: 'skill' },
  { slug: 'python',       name: 'Python',        category: 'skill' },
  { slug: 'smart-contract', name: 'Smart Contract', category: 'skill' },
  { slug: 'defi',         name: 'DeFi',          category: 'role' },
  { slug: 'nft',          name: 'NFT',           category: 'role' },
  { slug: 'security',     name: 'Security',      category: 'role' },
  { slug: 'frontend',     name: 'Frontend',      category: 'role' },
  { slug: 'backend',      name: 'Backend',       category: 'role' },
  { slug: 'devops',       name: 'DevOps',        category: 'role' },
  { slug: 'marketing',    name: 'Marketing',     category: 'role' },
  { slug: 'design',       name: 'Design',        category: 'role' },
  { slug: 'ethereum',     name: 'Ethereum',      category: 'chain' },
  { slug: 'solana',       name: 'Solana',        category: 'chain' },
  { slug: 'bitcoin',      name: 'Bitcoin',       category: 'chain' },
  { slug: 'polygon',      name: 'Polygon',       category: 'chain' },
  { slug: 'remote',       name: 'Remote',        category: 'benefit' },
  { slug: 'pay-in-crypto', name: 'Pay in Crypto', category: 'benefit' },
  { slug: 'equity',       name: 'Equity',        category: 'benefit' },
];

const COMPANIES: Array<{ slug: string; name: string; description: string; website: string; logoUrl: string; hqCity: string; hqCountry: string; sizeBucket: string }> = [
  { slug: 'helios-protocol', name: 'Helios Protocol', description: 'Modular L2 rollup pushing Ethereum scalability.', website: 'https://helios.example', logoUrl: '/logos/helios.svg', hqCity: 'New York', hqCountry: 'US', sizeBucket: '51-200' },
  { slug: 'nebula-labs',     name: 'Nebula Labs',     description: 'Zero-knowledge proof infrastructure for privacy-preserving apps.', website: 'https://nebula.example', logoUrl: '/logos/nebula.svg', hqCity: 'Berlin', hqCountry: 'DE', sizeBucket: '11-50' },
  { slug: 'orbit-finance',   name: 'Orbit Finance',   description: 'Cross-chain perpetual DEX with deep liquidity.', website: 'https://orbit.example', logoUrl: '/logos/orbit.svg', hqCity: 'Singapore', hqCountry: 'SG', sizeBucket: '11-50' },
  { slug: 'kairos-security', name: 'Kairos Security', description: 'Top-tier smart contract audit firm.', website: 'https://kairos.example', logoUrl: '/logos/kairos.svg', hqCity: 'London', hqCountry: 'GB', sizeBucket: '11-50' },
  { slug: 'pixel-realm',     name: 'Pixel Realm',     description: 'AAA on-chain gaming studio building autonomous worlds.', website: 'https://pixelrealm.example', logoUrl: '/logos/pixel.svg', hqCity: 'Remote', hqCountry: 'US', sizeBucket: '51-200' },
];

const JOBS: Array<{
  title: string;
  companySlug: string;
  description: string;
  location: string;
  isRemote: boolean;
  seniority: Seniority;
  salaryMin: number;
  salaryMax: number;
  applyType: ApplyType;
  applyUrl: string;
  tags: string[];
}> = [
  { title: 'Senior Solidity Engineer', companySlug: 'helios-protocol', description: 'Design and ship the next generation of our rollup contracts. Own auditing, gas optimization, and protocol upgrades.', location: 'Remote', isRemote: true, seniority: 'senior', salaryMin: 180_000, salaryMax: 240_000, applyType: 'external', applyUrl: 'https://helios.example/careers/solidity', tags: ['solidity', 'smart-contract', 'ethereum', 'remote'] },
  { title: 'Rust Engineer — Sequencer', companySlug: 'helios-protocol', description: 'Build and operate the rollup sequencer. Deep concurrency and low-latency networking required.', location: 'New York, US', isRemote: false, seniority: 'senior', salaryMin: 170_000, salaryMax: 230_000, applyType: 'external', applyUrl: 'https://helios.example/careers/rust', tags: ['rust', 'backend', 'ethereum'] },
  { title: 'Smart Contract Auditor', companySlug: 'kairos-security', description: 'Audit DeFi protocols, write public reports, and contribute to internal tooling.', location: 'Remote', isRemote: true, seniority: 'senior', salaryMin: 200_000, salaryMax: 300_000, applyType: 'external', applyUrl: 'https://kairos.example/careers/auditor', tags: ['security', 'solidity', 'remote'] },
  { title: 'ZK Researcher', companySlug: 'nebula-labs', description: 'Research and implement state-of-the-art zk proving systems. Bring novel cryptography to production.', location: 'Berlin, DE', isRemote: false, seniority: 'lead', salaryMin: 200_000, salaryMax: 280_000, applyType: 'external', applyUrl: 'https://nebula.example/careers/zk', tags: ['rust', 'security', 'ethereum'] },
  { title: 'Senior Frontend Engineer', companySlug: 'orbit-finance', description: 'Own the trader UI for our perpetual DEX. Obsess about microseconds and microns.', location: 'Remote', isRemote: true, seniority: 'senior', salaryMin: 150_000, salaryMax: 200_000, applyType: 'external', applyUrl: 'https://orbit.example/careers/frontend', tags: ['frontend', 'react', 'typescript', 'defi', 'remote'] },
  { title: 'DevOps Engineer', companySlug: 'orbit-finance', description: 'Run the cross-chain matching engine and oracle network. Wake up the bots, not the people.', location: 'Singapore', isRemote: false, seniority: 'mid', salaryMin: 120_000, salaryMax: 170_000, applyType: 'external', applyUrl: 'https://orbit.example/careers/devops', tags: ['devops', 'backend', 'golang'] },
  { title: 'Game Engine Engineer', companySlug: 'pixel-realm', description: 'Build the rendering layer for our autonomous on-chain MMO.', location: 'Remote', isRemote: true, seniority: 'senior', salaryMin: 160_000, salaryMax: 220_000, applyType: 'external', applyUrl: 'https://pixelrealm.example/careers/engine', tags: ['typescript', 'frontend', 'nft', 'remote'] },
  { title: 'Smart Contract Engineer — Gaming', companySlug: 'pixel-realm', description: 'Design ERC-721/1155 mechanics for autonomous worlds. Be the lawyer for an in-game economy.', location: 'Remote', isRemote: true, seniority: 'mid', salaryMin: 140_000, salaryMax: 190_000, applyType: 'external', applyUrl: 'https://pixelrealm.example/careers/contract', tags: ['solidity', 'nft', 'smart-contract', 'remote'] },
  { title: 'Backend Engineer — Indexer', companySlug: 'nebula-labs', description: 'Build the high-throughput indexer powering our zkApp ecosystem.', location: 'Remote', isRemote: true, seniority: 'mid', salaryMin: 130_000, salaryMax: 180_000, applyType: 'external', applyUrl: 'https://nebula.example/careers/indexer', tags: ['rust', 'backend', 'remote'] },
  { title: 'Security Engineer', companySlug: 'helios-protocol', description: 'Threat-model the protocol and lead our bug bounty program.', location: 'Remote', isRemote: true, seniority: 'lead', salaryMin: 190_000, salaryMax: 260_000, applyType: 'external', applyUrl: 'https://helios.example/careers/security', tags: ['security', 'solidity', 'remote'] },
  { title: 'Product Designer', companySlug: 'orbit-finance', description: 'Design end-to-end flows for our perpetual DEX. Make complex onchain ops feel native.', location: 'Remote', isRemote: true, seniority: 'mid', salaryMin: 110_000, salaryMax: 160_000, applyType: 'external', applyUrl: 'https://orbit.example/careers/design', tags: ['design', 'defi', 'remote'] },
  { title: 'Growth Marketing Lead', companySlug: 'pixel-realm', description: 'Own community + content. Build a movement around our game.', location: 'Remote', isRemote: true, seniority: 'lead', salaryMin: 120_000, salaryMax: 170_000, applyType: 'external', applyUrl: 'https://pixelrealm.example/careers/growth', tags: ['marketing', 'remote'] },
  { title: 'Junior Solidity Developer', companySlug: 'helios-protocol', description: 'Pair with our senior contract engineers. Write tests, fuzz harnesses, and tooling.', location: 'Remote', isRemote: true, seniority: 'junior', salaryMin: 80_000, salaryMax: 120_000, applyType: 'external', applyUrl: 'https://helios.example/careers/junior', tags: ['solidity', 'smart-contract', 'remote'] },
  { title: 'Senior Backend Engineer — Python', companySlug: 'nebula-labs', description: 'Build proving-as-a-service APIs with Python and Rust.', location: 'Berlin, DE', isRemote: false, seniority: 'senior', salaryMin: 160_000, salaryMax: 210_000, applyType: 'external', applyUrl: 'https://nebula.example/careers/backend', tags: ['python', 'backend', 'rust'] },
  { title: 'DevRel Engineer', companySlug: 'helios-protocol', description: 'Be the bridge between our protocol and the dev ecosystem.', location: 'Remote', isRemote: true, seniority: 'mid', salaryMin: 130_000, salaryMax: 180_000, applyType: 'external', applyUrl: 'https://helios.example/careers/devrel', tags: ['marketing', 'frontend', 'solidity', 'remote'] },
  { title: 'On-chain Data Analyst', companySlug: 'orbit-finance', description: 'Build the data layer for our trading and incentive programs.', location: 'Remote', isRemote: true, seniority: 'mid', salaryMin: 110_000, salaryMax: 160_000, applyType: 'external', applyUrl: 'https://orbit.example/careers/data', tags: ['python', 'defi', 'remote'] },
  { title: 'Senior Audit Engineer', companySlug: 'kairos-security', description: 'Lead audit engagements. Mentor juniors. Publish public reports that move the industry.', location: 'London, GB', isRemote: false, seniority: 'lead', salaryMin: 220_000, salaryMax: 320_000, applyType: 'external', applyUrl: 'https://kairos.example/careers/lead', tags: ['security', 'solidity'] },
  { title: 'Junior Smart Contract Auditor', companySlug: 'kairos-security', description: 'Train into one of the toughest disciplines in Web3 with our senior auditors.', location: 'Remote', isRemote: true, seniority: 'junior', salaryMin: 90_000, salaryMax: 130_000, applyType: 'external', applyUrl: 'https://kairos.example/careers/junior', tags: ['security', 'solidity', 'remote'] },
  { title: 'Game Producer', companySlug: 'pixel-realm', description: 'Coordinate dev, art, and community streams across our flagship title.', location: 'Remote', isRemote: true, seniority: 'senior', salaryMin: 140_000, salaryMax: 200_000, applyType: 'external', applyUrl: 'https://pixelrealm.example/careers/producer', tags: ['design', 'marketing', 'remote'] },
  { title: 'TypeScript SDK Engineer', companySlug: 'nebula-labs', description: 'Build the SDK developers reach for first when adding zk to their app.', location: 'Remote', isRemote: true, seniority: 'mid', salaryMin: 140_000, salaryMax: 190_000, applyType: 'external', applyUrl: 'https://nebula.example/careers/sdk', tags: ['typescript', 'frontend', 'remote'] },
];

async function main() {
  console.log('Seeding tags…');
  for (const t of TAGS) {
    await prisma.tag.upsert({ where: { slug: t.slug }, update: {}, create: t });
  }

  console.log('Seeding employer & candidate users…');
  const employerHash = await hash('password1', 8);
  const candidateHash = await hash('password1', 8);
  const employer = await prisma.user.upsert({
    where: { email: 'demo-employer@web3career.local' },
    update: {},
    create: { email: 'demo-employer@web3career.local', passwordHash: employerHash, role: 'employer', displayName: 'Demo Employer', emailVerifiedAt: new Date() },
  });
  await prisma.user.upsert({
    where: { email: 'demo-candidate@web3career.local' },
    update: {},
    create: { email: 'demo-candidate@web3career.local', passwordHash: candidateHash, role: 'candidate', displayName: 'Demo Candidate', emailVerifiedAt: new Date() },
  });

  console.log('Seeding companies…');
  for (const c of COMPANIES) {
    await prisma.company.upsert({
      where: { slug: c.slug },
      update: {},
      create: { ...c, isClaimed: true, isVerified: true, ownerUserId: c.slug === 'helios-protocol' ? employer.id : null },
    });
  }

  console.log('Seeding jobs…');
  for (const j of JOBS) {
    const company = await prisma.company.findUnique({ where: { slug: j.companySlug } });
    if (!company) continue;
    const tagRows = await prisma.tag.findMany({ where: { slug: { in: j.tags } } });
    const slug = j.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80) + '-' + randomBytes(3).toString('hex');
    await prisma.job.create({
      data: {
        slug,
        title: j.title,
        description: j.description,
        location: j.location,
        isRemote: j.isRemote,
        seniority: j.seniority,
        employmentType: 'full_time',
        salaryMin: j.salaryMin,
        salaryMax: j.salaryMax,
        applyType: j.applyType,
        applyUrl: j.applyUrl,
        companyId: company.id,
        status: 'live',
        postedAt: new Date(Date.now() - Math.floor(Math.random() * 14) * 24 * 3600 * 1000),
        expiresAt: new Date(Date.now() + 60 * 24 * 3600 * 1000),
        tags: { create: tagRows.map((t, idx) => ({ tagId: t.id, position: idx })) },
      },
    });
  }
  const ARTICLES: Array<{ slug: string; title: string; category: 'article'|'book'|'course'|'tutorial'|'video'|'bootcamp'|'news'|'whitepaper'; author: string; excerpt: string; contentMd: string; coverGradient: string; readMinutes: number | null; isFree: boolean; externalUrl: string | null; publishedAt: Date }> = [
    { slug: 'how-to-get-web3-job-2026', title: 'How to land your first Web3 job in 2026', category: 'article', author: 'Helia Sun', excerpt: 'A pragmatic, no-hype playbook for breaking into Web3 — what to build, where to ship, how to interview.', contentMd: '# How to land your first Web3 job\n\nWeb3 hiring matured a lot in 2025. The companies that hire fastest now look for three things: a public portfolio, opinionated taste, and reliability.\n\n## 1. Ship something on-chain\nNot a tutorial fork. Find a tiny annoyance, fix it, deploy.\n\n## 2. Be visible in the right places\nGithub > Twitter > Discord. Audit reports, EIPs, fork experiments.\n\n## 3. Interview like a pro\nKnow the contract you wrote. Have opinions about gas, MEV, security.\n\n## 4. Pick the right company\nFollow the money, but also follow the founders.', coverGradient: 'from-cyan-500/40 to-violet-500/30', readMinutes: 7, isFree: true, externalUrl: null, publishedAt: new Date('2026-04-22') },
    { slug: 'solidity-gas-optimization-deep-dive', title: 'Solidity gas optimization: deep dive', category: 'tutorial', author: 'Marek Vladov', excerpt: 'Sixteen patterns that actually move the needle — measured on mainnet, not testnet.', contentMd: '# Gas optimization that matters\n\nThe usual advice (`uint256` vs `uint8`, `unchecked`, immutable, packed structs) is well-trodden. Here are sixteen non-obvious patterns that we measured on real mainnet transactions.\n\n## 1. Pack hot data first\nEverything you read every call goes together. Storage reads are 2,100 gas the first time per slot.\n\n## 2. Use bitmaps for access lists\nA `uint256` is 256 bits — that is 256 booleans for the price of one SSTORE.\n\n## 3. Cache `array.length` in for-loops\nThe compiler should do it but `forge inspect` shows it often does not.\n\n## (more)', coverGradient: 'from-lime-500/30 to-cyan-500/30', readMinutes: 14, isFree: true, externalUrl: null, publishedAt: new Date('2026-03-30') },
    { slug: 'audit-mindset-secureum-bootcamp', title: 'How I think during a smart contract audit', category: 'article', author: 'Kairos Sec Team', excerpt: 'Notes from a senior auditor on how to actually find bugs nobody else does.', contentMd: '# Audit mindset\n\nThere are three modes I switch between when reading a codebase:\n\n## Mode 1: Tourist\nRead the README. Read the tests. Build a mental map of the user flow.\n\n## Mode 2: Adversary\nFor each function, ask: who can call it? Who benefits? What does it cost? What invariant could it break?\n\n## Mode 3: Engineer\nIf I were rewriting this, would I structure it this way? Where would I cut corners?', coverGradient: 'from-rose-500/30 to-violet-500/30', readMinutes: 9, isFree: true, externalUrl: null, publishedAt: new Date('2026-03-11') },
    { slug: 'mastering-ethereum', title: 'Mastering Ethereum (Antonopoulos & Wood)', category: 'book', author: 'Andreas M. Antonopoulos, Gavin Wood', excerpt: 'The reference book. Read it twice. Implement every example.', contentMd: '# Mastering Ethereum\n\nThe canonical book for understanding how Ethereum actually works under the hood.\n\nIt is dense. Read it twice. Type out every code example yourself.', coverGradient: 'from-violet-500/30 to-cyan-500/30', readMinutes: null, isFree: true, externalUrl: 'https://github.com/ethereumbook/ethereumbook', publishedAt: new Date('2026-02-04') },
    { slug: 'metana-web3-bootcamp', title: 'Metana — Web3 Bootcamp (Job-Guaranteed)', category: 'bootcamp', author: 'Metana', excerpt: 'Full-time, immersive — solidity, foundry, real audit experience. Job placement included.', contentMd: '# Metana Web3 Bootcamp\n\nFull-time, four months, solidity-first. The placement guarantee is real (verified with alumni).\n\nFee: $9,500 (income-share alternative available).', coverGradient: 'from-cyan-500/30 to-lime-500/30', readMinutes: null, isFree: false, externalUrl: 'https://metana.io', publishedAt: new Date('2026-01-15') },
    { slug: 'foundry-from-zero', title: 'Foundry from zero to deployment', category: 'course', author: 'Patrick Collins', excerpt: 'The free course everyone runs through before their first real audit.', contentMd: '# Foundry from zero\n\nFree, ~25 hours, ships you all the way from "what is a hash" to mainnet deployment.\n\nDo every exercise. Skip the videos at 2x.', coverGradient: 'from-cyan-500/30 to-violet-500/40', readMinutes: null, isFree: true, externalUrl: 'https://updraft.cyfrin.io', publishedAt: new Date('2025-12-20') },
    { slug: 'zk-circuits-explained', title: 'ZK circuits, explained like you finished high school', category: 'tutorial', author: 'Nebula Labs', excerpt: 'No PhD required. Halo2, Circom, Plonky2 — what they do and when to pick which.', contentMd: '# ZK circuits\n\nLet us start with what a circuit even is and only then jump into the alphabet soup.', coverGradient: 'from-violet-500/40 to-rose-500/30', readMinutes: 18, isFree: true, externalUrl: null, publishedAt: new Date('2026-04-02') },
    { slug: 'l2-economics-2026', title: 'L2 economics in 2026: who is actually profitable?', category: 'news', author: 'Helios Research', excerpt: 'A breakdown of L2 sequencer revenue vs proving cost across the top 10 rollups.', contentMd: '# L2 economics\n\nWe pulled on-chain data for the top 10 rollups for Q1 2026. The headline: only three are profitable after accounting for proving costs.', coverGradient: 'from-lime-500/30 to-cyan-500/40', readMinutes: 11, isFree: true, externalUrl: null, publishedAt: new Date('2026-05-05') },
    { slug: 'mev-deep-dive-video', title: 'MEV from the trenches — a 90 minute deep dive', category: 'video', author: 'Flashbots', excerpt: 'Live walkthrough: searcher, builder, validator. Three roles, one block.', contentMd: '# MEV deep dive\n\nA recorded talk from Devcon. Watch with a notepad.', coverGradient: 'from-rose-500/30 to-violet-500/40', readMinutes: 90, isFree: true, externalUrl: 'https://example.com/mev-deepdive', publishedAt: new Date('2025-11-18') },
    { slug: 'ethereum-yellow-paper', title: 'Ethereum Yellow Paper', category: 'whitepaper', author: 'Gavin Wood', excerpt: 'The formal specification of Ethereum. Yes you should read it. No it is not optional.', contentMd: '# The Yellow Paper\n\nIf you build on Ethereum, the Yellow Paper is the source of truth.', coverGradient: 'from-cyan-500/30 to-zinc-500/30', readMinutes: null, isFree: true, externalUrl: 'https://ethereum.github.io/yellowpaper/paper.pdf', publishedAt: new Date('2025-10-01') },
  ];

  console.log('Seeding articles…');
  for (const a of ARTICLES) {
    await prisma.article.upsert({
      where: { slug: a.slug },
      update: {},
      create: a,
    });
  }

  console.log('✓ seed complete.');
}

main()
  .catch((e) => { console.error(e); process.exit(1); })
  .finally(() => prisma.$disconnect());
