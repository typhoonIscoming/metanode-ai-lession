-- CreateEnum
CREATE TYPE "ArticleCategory" AS ENUM ('article', 'book', 'course', 'tutorial', 'video', 'bootcamp', 'news', 'whitepaper');

-- CreateTable
CREATE TABLE "articles" (
    "id" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "category" "ArticleCategory" NOT NULL,
    "author" TEXT NOT NULL,
    "excerpt" TEXT NOT NULL,
    "content_md" TEXT NOT NULL,
    "cover_gradient" TEXT,
    "read_minutes" INTEGER,
    "is_free" BOOLEAN NOT NULL DEFAULT true,
    "external_url" TEXT,
    "published_at" TIMESTAMP(3) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "articles_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "articles_slug_key" ON "articles"("slug");

-- CreateIndex
CREATE INDEX "articles_category_published_at_idx" ON "articles"("category", "published_at" DESC);
